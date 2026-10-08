from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .dataset import find_sqlite_database, introspect_sqlite_schema, render_schema
from .execution import execute_sqlite_readonly, results_equivalent, sql_requires_order
from .experiment import PricingRates, estimate_usage_cost
from .providers.base import SQLGenerator
from .types import BenchmarkRecord, BirdExample, TokenUsage
from .validation import validate_readonly_sql


def run_baseline(
    examples: Iterable[BirdExample],
    *,
    database_root: str | Path,
    generator: SQLGenerator,
    output_path: str | Path,
    dialect: str = "sqlite",
    timeout_seconds: float = 5.0,
    max_rows: int = 10_000,
    pricing: PricingRates | None = None,
) -> dict[str, Any]:
    trace_path = Path(output_path)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    records: list[BenchmarkRecord] = []

    with trace_path.open("w", encoding="utf-8") as trace_file:
        for example in examples:
            database_path = find_sqlite_database(database_root, example.db_id)
            schema = introspect_sqlite_schema(database_path)
            generation = generator.generate(
                question=example.question,
                evidence=example.evidence,
                schema=render_schema(schema),
            )
            validation = validate_readonly_sql(generation.sql, schema, dialect=dialect)
            gold_execution = execute_sqlite_readonly(
                database_path,
                example.gold_sql,
                timeout_seconds=timeout_seconds,
                max_rows=max_rows,
            )
            candidate_execution = None
            gold_is_scoreable = gold_execution.succeeded and not gold_execution.truncated
            execution_correct: bool | None = False if gold_is_scoreable else None
            if validation.valid and validation.normalized_sql:
                candidate_execution = execute_sqlite_readonly(
                    database_path,
                    validation.normalized_sql,
                    timeout_seconds=timeout_seconds,
                    max_rows=max_rows,
                )
                if gold_is_scoreable:
                    execution_correct = results_equivalent(
                        candidate_execution,
                        gold_execution,
                        order_sensitive=sql_requires_order(example.gold_sql),
                    )

            record = BenchmarkRecord(
                example=example,
                generation=generation,
                validation=validation,
                candidate_execution=candidate_execution,
                gold_execution=gold_execution,
                execution_correct=execution_correct,
            )
            records.append(record)
            trace_file.write(json.dumps(record.to_dict(), ensure_ascii=False, default=str) + "\n")
            trace_file.flush()

    summary = summarize(records, pricing=pricing)
    summary_path = trace_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def summarize(
    records: list[BenchmarkRecord], *, pricing: PricingRates | None = None
) -> dict[str, Any]:
    total = len(records)
    evaluated = [record for record in records if record.execution_correct is not None]
    correct = sum(record.execution_correct is True for record in evaluated)
    valid = sum(record.validation.valid for record in records)
    completed = sum(
        record.candidate_execution is not None and record.candidate_execution.succeeded
        for record in records
    )
    usage = [record.generation.usage for record in records]
    latencies = [record.generation.latency_ms for record in records]
    totals = {
        "examples": total,
        "locally_evaluated_examples": len(evaluated),
        "locally_unscored_examples": total - len(evaluated),
        "local_evaluation_coverage": len(evaluated) / total if total else 0.0,
        "execution_correct": correct,
        "execution_accuracy": correct / len(evaluated) if evaluated else 0.0,
        "validation_passes": valid,
        "validation_rate": valid / total if total else 0.0,
        "execution_successes": completed,
        "execution_success_rate": completed / total if total else 0.0,
        "model_input_tokens": sum(item.input_tokens for item in usage),
        "model_cached_input_tokens": sum(item.cached_input_tokens for item in usage),
        "model_output_tokens": sum(item.output_tokens for item in usage),
        "model_reasoning_tokens": sum(item.reasoning_tokens for item in usage),
        "model_total_tokens": sum(item.total_tokens for item in usage),
        "mean_model_latency_ms": sum(latencies) / total if total else 0.0,
        "models": sorted({record.generation.model for record in records}),
    }
    if pricing is None:
        totals["estimated_model_cost_usd"] = None
        totals["pricing"] = None
    else:
        combined_usage = TokenUsage(
            input_tokens=totals["model_input_tokens"],
            cached_input_tokens=totals["model_cached_input_tokens"],
            output_tokens=totals["model_output_tokens"],
            reasoning_tokens=totals["model_reasoning_tokens"],
        )
        totals["estimated_model_cost_usd"] = estimate_usage_cost(combined_usage, pricing)
        totals["pricing"] = pricing.to_dict()
    return totals
