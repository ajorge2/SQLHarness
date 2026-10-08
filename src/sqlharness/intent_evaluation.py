from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

from .dataset import find_sqlite_database, introspect_sqlite_schema, render_schema
from .intent import repair_unique_source_spans, validate_intent_graph
from .providers.codex_cli_intent import IntentGraphGeneration
from .types import BirdExample


class IntentGenerator(Protocol):
    def generate(self, *, question: str, evidence: str, schema: str) -> IntentGraphGeneration:
        """Generate one task-oriented intent graph."""


def load_intent_audit_sample(path: str | Path) -> list[BirdExample]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        BirdExample(
            example_id=str(item["example_id"]),
            db_id=str(item["db_id"]),
            question=str(item["question"]),
            evidence=str(item.get("evidence", "")),
            gold_sql=str(item["gold_sql"]),
            difficulty=str(item.get("difficulty", "")),
        )
        for item in payload["examples"]
    ]


def run_intent_generation_audit(
    examples: list[BirdExample],
    *,
    database_root: str | Path,
    generator: IntentGenerator,
    output_path: str | Path,
) -> dict[str, Any]:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    with target.open("w", encoding="utf-8") as output:
        for example in examples:
            try:
                database_path = find_sqlite_database(database_root, example.db_id)
                schema_map = introspect_sqlite_schema(database_path)
                schema = render_schema(schema_map)
                generation = generator.generate(
                    question=example.question,
                    evidence=example.evidence,
                    schema=schema,
                )
                raw_validation = validate_intent_graph(generation.graph)
                repaired_graph, span_repairs = repair_unique_source_spans(generation.graph)
                validation = validate_intent_graph(repaired_graph)
                schema_errors = validate_schema_candidates(repaired_graph, schema_map)
                input_fidelity = (
                    repaired_graph.request == example.question
                    and repaired_graph.evidence == example.evidence
                )
                record = {
                    "example_id": example.example_id,
                    "db_id": example.db_id,
                    "difficulty": example.difficulty,
                    "model": generation.model,
                    "raw_graph": generation.graph.to_dict(),
                    "graph": repaired_graph.to_dict(),
                    "raw_validation": {
                        "valid": raw_validation.valid,
                        "errors": list(raw_validation.errors),
                    },
                    "validation": {
                        "valid": validation.valid,
                        "errors": list(validation.errors),
                    },
                    "span_repairs": list(span_repairs),
                    "schema_validation": {
                        "valid": not schema_errors,
                        "errors": list(schema_errors),
                    },
                    "input_fidelity": input_fidelity,
                    "latency_ms": generation.latency_ms,
                    "usage": asdict(generation.usage),
                    "error": None,
                }
            except Exception as error:  # preserve a complete diagnostic trace
                record = {
                    "example_id": example.example_id,
                    "db_id": example.db_id,
                    "difficulty": example.difficulty,
                    "model": None,
                    "graph": None,
                    "raw_graph": None,
                    "raw_validation": {"valid": False, "errors": []},
                    "validation": {"valid": False, "errors": []},
                    "span_repairs": [],
                    "schema_validation": {"valid": False, "errors": []},
                    "input_fidelity": False,
                    "latency_ms": None,
                    "usage": None,
                    "error": str(error),
                }
            records.append(record)
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()

    generated = [record for record in records if record["graph"] is not None]
    latencies = [record["latency_ms"] for record in generated]
    usages = [record["usage"] for record in generated]
    summary = {
        "examples": len(records),
        "generated": len(generated),
        "generation_rate": len(generated) / len(records) if records else 0.0,
        "raw_structurally_valid": sum(
            record["raw_validation"]["valid"] for record in generated
        ),
        "raw_structural_validity_rate": (
            sum(record["raw_validation"]["valid"] for record in generated) / len(generated)
            if generated
            else 0.0
        ),
        "structurally_valid": sum(record["validation"]["valid"] for record in generated),
        "structural_validity_rate": (
            sum(record["validation"]["valid"] for record in generated) / len(generated)
            if generated
            else 0.0
        ),
        "input_fidelity_passes": sum(record["input_fidelity"] for record in generated),
        "input_fidelity_rate": (
            sum(record["input_fidelity"] for record in generated) / len(generated)
            if generated
            else 0.0
        ),
        "mean_nodes": (
            sum(len(record["graph"]["nodes"]) for record in generated) / len(generated)
            if generated
            else 0.0
        ),
        "schema_candidate_passes": sum(
            record["schema_validation"]["valid"] for record in generated
        ),
        "schema_candidate_validity_rate": (
            sum(record["schema_validation"]["valid"] for record in generated) / len(generated)
            if generated
            else 0.0
        ),
        "mean_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        "input_tokens": sum(usage["input_tokens"] for usage in usages),
        "output_tokens": sum(usage["output_tokens"] for usage in usages),
        "reasoning_tokens": sum(usage["reasoning_tokens"] for usage in usages),
        "unique_span_repairs": sum(len(record["span_repairs"]) for record in generated),
        "models": sorted({record["model"] for record in generated}),
        "disclosure": "Structural generation audit; semantic graph correctness is not yet scored.",
    }
    target.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def validate_schema_candidates(
    graph: Any, schema: dict[str, tuple[str, ...]]
) -> tuple[str, ...]:
    errors: list[str] = []
    for node in graph.nodes:
        for candidate in node.schema_candidates:
            if candidate in schema:
                continue
            if "." in candidate:
                table, column = candidate.split(".", 1)
                if table in schema and column in schema[table]:
                    continue
            errors.append(f"unknown_schema_candidate: {node.node_id}={candidate}")
    return tuple(errors)
