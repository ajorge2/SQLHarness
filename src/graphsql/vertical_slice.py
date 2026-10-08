from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Protocol

from .authority import DatabaseAuthority
from .dataset import find_sqlite_database, introspect_sqlite_schema, render_schema
from .execution import execute_sqlite_readonly, results_equivalent, sql_requires_order
from .fragments import (
    LexicalFragmentRetriever,
    RetrievalHit,
    SQLFragment,
    IntentFragment,
    serialize_intent_fragments,
)
from .intent import IntentGraph, repair_unique_source_spans, validate_intent_graph
from .intent_evaluation import validate_schema_candidates
from .providers.codex_cli_assembler import CodexCLIFragmentAssembler
from .types import BirdExample, ExecutionResult
from .validation import validate_readonly_sql


class FragmentAssembler(Protocol):
    def generate(
        self,
        *,
        question: str,
        evidence: str,
        schema: str,
        graph: IntentGraph,
        retrieval_hits: list[RetrievalHit],
    ) -> Any:
        """Assemble SQL from a graph and retrieved fragments."""


class FragmentRetriever(Protocol):
    def retrieve(
        self,
        intent_fragments: Iterable[IntentFragment],
        *,
        top_k_per_intent: int = 2,
        max_total: int = 12,
    ) -> list[RetrievalHit]: ...


def load_graph_trace(path: str | Path) -> dict[str, dict[str, Any]]:
    return {
        record["example_id"]: record
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
        for record in [json.loads(line)]
    }


def run_vertical_slice(
    examples: list[BirdExample],
    *,
    database_root: str | Path,
    graph_records: dict[str, dict[str, Any]],
    corpus: list[SQLFragment],
    assembler: FragmentAssembler,
    output_path: str | Path,
    retriever: FragmentRetriever | None = None,
    retriever_name: str = "lexical-bm25-control",
    top_k_per_intent: int = 2,
    max_retrieval_hits: int = 12,
    max_repair_attempts: int = 1,
    parser_timeout_seconds: float = 120.0,
    execution_timeout_seconds: float = 30.0,
    max_rows: int = 100_000,
) -> dict[str, Any]:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    active_retriever = retriever or LexicalFragmentRetriever(corpus)
    authority = DatabaseAuthority(
        database_root,
        timeout_seconds=execution_timeout_seconds,
        max_rows=max_rows,
    )
    records: list[dict[str, Any]] = []

    with target.open("w", encoding="utf-8") as output:
        for example in examples:
            graph_record = graph_records.get(example.example_id)
            parser_latency_ms = _parser_latency(graph_record, parser_timeout_seconds)
            parser_usage = (graph_record or {}).get("usage") or {}
            record: dict[str, Any] = {
                "example_id": example.example_id,
                "db_id": example.db_id,
                "difficulty": example.difficulty,
                "execution_correct": False,
                "abstained": False,
                "failure_stage": None,
                "parser_latency_ms": parser_latency_ms,
                "parser_usage": parser_usage,
                "retriever": retriever_name,
            }
            try:
                if not graph_record or graph_record.get("graph") is None:
                    record.update(abstained=True, failure_stage="intent_parser")
                    records.append(record)
                    output.write(json.dumps(record) + "\n")
                    output.flush()
                    continue

                graph, _ = repair_unique_source_spans(IntentGraph.from_dict(graph_record["graph"]))
                database_path = find_sqlite_database(database_root, example.db_id)
                schema_map = introspect_sqlite_schema(database_path)
                graph_validation = validate_intent_graph(graph)
                schema_errors = validate_schema_candidates(graph, schema_map)
                record["graph_validation"] = {
                    "valid": graph_validation.valid,
                    "errors": list(graph_validation.errors),
                    "schema_errors": list(schema_errors),
                }
                if not graph_validation.valid or schema_errors:
                    record.update(abstained=True, failure_stage="intent_validation")
                    records.append(record)
                    output.write(json.dumps(record) + "\n")
                    output.flush()
                    continue

                hits = active_retriever.retrieve(
                    serialize_intent_fragments(graph),
                    top_k_per_intent=top_k_per_intent,
                    max_total=max_retrieval_hits,
                )
                record["retrieval_hits"] = [_hit_to_dict(hit) for hit in hits]
                if not hits:
                    record.update(abstained=True, failure_stage="fragment_retrieval")
                    records.append(record)
                    output.write(json.dumps(record) + "\n")
                    output.flush()
                    continue

                generation_attempts: list[dict[str, Any]] = []
                authority_receipts: list[dict[str, Any]] = []
                repair_error: str | None = None
                generation = None
                validation = None
                candidate = None
                for attempt in range(max(max_repair_attempts, 0) + 1):
                    repair_method = getattr(assembler, "repair", None)
                    if attempt == 0:
                        generation = assembler.generate(
                            question=example.question,
                            evidence=example.evidence,
                            schema=render_schema(schema_map),
                            graph=graph,
                            retrieval_hits=hits,
                        )
                    elif callable(repair_method) and generation is not None and repair_error:
                        generation = repair_method(
                            question=example.question,
                            evidence=example.evidence,
                            schema=render_schema(schema_map),
                            graph=graph,
                            retrieval_hits=hits,
                            previous_sql=generation.sql,
                            error=repair_error,
                        )
                    else:
                        break

                    generation_attempts.append(asdict(generation))
                    validation = validate_readonly_sql(generation.sql, schema_map)
                    if not validation.valid or not validation.normalized_sql:
                        repair_error = "; ".join(validation.errors) or "SQL validation failed"
                        continue

                    authority_receipt = authority.execute(
                        example.db_id,
                        validation.normalized_sql,
                    )
                    authority_receipts.append(authority_receipt)
                    candidate = _execution_from_receipt(authority_receipt)
                    if not candidate.succeeded:
                        repair_error = candidate.error or "Database execution failed"
                        continue
                    break

                record["generation_attempts"] = generation_attempts
                record["repair_attempts"] = max(len(generation_attempts) - 1, 0)
                if generation is not None:
                    record["generation"] = asdict(generation)
                if validation is not None:
                    record["sql_validation"] = asdict(validation)
                if authority_receipts:
                    record["authority_receipts"] = authority_receipts
                    record["authority_receipt"] = authority_receipts[-1]

                if validation is None or not validation.valid or not validation.normalized_sql:
                    record["failure_stage"] = "sql_validation"
                elif candidate is None or not candidate.succeeded:
                    record["failure_stage"] = "execution"
                else:
                    gold = execute_sqlite_readonly(
                        database_path,
                        example.gold_sql,
                        timeout_seconds=execution_timeout_seconds,
                        max_rows=max_rows,
                    )
                    record["candidate_execution"] = asdict(candidate)
                    record["gold_execution"] = asdict(gold)
                    if gold.succeeded and not gold.truncated:
                        record["execution_correct"] = results_equivalent(
                            candidate,
                            gold,
                            order_sensitive=sql_requires_order(example.gold_sql),
                        )
                        if not record["execution_correct"]:
                            record["failure_stage"] = "result_mismatch"
            except Exception as error:
                record["failure_stage"] = record["failure_stage"] or "assembly"
                record["error"] = str(error)
            records.append(record)
            output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            output.flush()

    generated = [record for record in records if "generation" in record]
    completed_latencies = [
        float(record["parser_latency_ms"])
        + sum(
            float(attempt["latency_ms"])
            for attempt in record.get("generation_attempts", [record["generation"]])
        )
        for record in generated
    ]
    observed_latencies = [
        float(record["parser_latency_ms"])
        + sum(
            float(attempt["latency_ms"])
            for attempt in record.get(
                "generation_attempts",
                [record["generation"]] if record.get("generation") else [],
            )
        )
        for record in records
    ]
    total_tokens = sum(
        sum(int(record["parser_usage"].get(key, 0) or 0) for key in ("input_tokens", "output_tokens"))
        + sum(
            int(attempt["usage"]["input_tokens"]) + int(attempt["usage"]["output_tokens"])
            for attempt in record.get("generation_attempts", [record["generation"]])
        )
        for record in generated
    )
    summary = {
        "examples": len(records),
        "execution_correct": sum(record["execution_correct"] for record in records),
        "end_to_end_accuracy": (
            sum(record["execution_correct"] for record in records) / len(records)
            if records
            else 0.0
        ),
        "generated_sql": len(generated),
        "abstentions": sum(record["abstained"] for record in records),
        "answered_accuracy": (
            sum(record["execution_correct"] for record in generated) / len(generated)
            if generated
            else 0.0
        ),
        "failure_stages": _count_failures(records),
        "mean_completed_pipeline_latency_ms": (
            sum(completed_latencies) / len(completed_latencies)
            if completed_latencies
            else 0.0
        ),
        "mean_observed_end_to_end_latency_ms": (
            sum(observed_latencies) / len(observed_latencies)
            if observed_latencies
            else 0.0
        ),
        "reported_model_tokens_for_completed_pipelines": total_tokens,
        "retriever": retriever_name,
        "authority_boundary": "DatabaseAuthority (also exposed through MCP)",
        "repair_attempts": sum(int(record.get("repair_attempts", 0)) for record in records),
        "token_accounting_disclosure": (
            "Token total includes only completed parser-plus-assembler pipelines; "
            "the timed-out parser did not return usage."
        ),
        "disclosure": f"{len(records)}-example held-out development slice; not a benchmark claim.",
    }
    target.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _parser_latency(record: dict[str, Any] | None, timeout_seconds: float) -> float:
    if record and record.get("latency_ms") is not None:
        return float(record["latency_ms"])
    return timeout_seconds * 1000


def _hit_to_dict(hit: RetrievalHit) -> dict[str, Any]:
    return {
        "query_node_id": hit.query_node_id,
        "score": hit.score,
        "fragment": hit.fragment.to_dict(),
    }


def _count_failures(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        stage = record.get("failure_stage")
        if stage:
            counts[stage] = counts.get(stage, 0) + 1
    return dict(sorted(counts.items()))


def _execution_from_receipt(receipt: dict[str, Any]) -> ExecutionResult:
    payload = receipt.get("execution")
    if not isinstance(payload, dict):
        return ExecutionResult(
            succeeded=False,
            error=f"Authority decision: {receipt.get('decision', 'unknown')}",
        )
    return ExecutionResult(
        succeeded=bool(payload.get("succeeded")),
        rows=tuple(tuple(row) for row in payload.get("rows", ())),
        columns=tuple(str(column) for column in payload.get("columns", ())),
        latency_ms=float(payload.get("latency_ms", 0.0)),
        truncated=bool(payload.get("truncated")),
        error=str(payload["error"]) if payload.get("error") is not None else None,
    )
