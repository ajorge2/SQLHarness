from __future__ import annotations

import json
import sqlite3

from sqlharness.intent import IntentGraph
from sqlharness.intent_evaluation import load_intent_audit_sample, run_intent_generation_audit
from sqlharness.providers.codex_cli_intent import IntentGraphGeneration
from sqlharness.types import TokenUsage


class FakeIntentGenerator:
    def generate(self, *, question: str, evidence: str, schema: str) -> IntentGraphGeneration:
        return IntentGraphGeneration(
            graph=IntentGraph.from_dict(
                {
                    "graph_version": "0.2",
                    "request": question,
                    "evidence": evidence,
                    "nodes": [
                        {
                            "node_id": "answer",
                            "kind": "output",
                            "concept": "answer",
                            "spans": [],
                            "schema_candidates": [],
                            "attributes": {},
                        }
                    ],
                    "edges": [],
                }
            ),
            model="fake/intent",
            latency_ms=5.0,
            usage=TokenUsage(input_tokens=10, output_tokens=20),
            raw_output="{}",
        )


def test_intent_generation_audit_records_structural_metrics(tmp_path):
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(
        json.dumps(
            {
                "examples": [
                    {
                        "example_id": "1",
                        "db_id": "shop",
                        "question": "Return the answer",
                        "evidence": "",
                        "gold_sql": "SELECT 1",
                        "difficulty": "simple",
                    }
                ]
            }
        )
    )
    database_dir = tmp_path / "databases" / "shop"
    database_dir.mkdir(parents=True)
    with sqlite3.connect(database_dir / "shop.sqlite") as connection:
        connection.execute("CREATE TABLE customers (id INTEGER)")

    examples = load_intent_audit_sample(sample_path)
    summary = run_intent_generation_audit(
        examples,
        database_root=tmp_path / "databases",
        generator=FakeIntentGenerator(),
        output_path=tmp_path / "audit.jsonl",
    )

    assert summary["examples"] == 1
    assert summary["structural_validity_rate"] == 1.0
    assert summary["input_fidelity_rate"] == 1.0
    assert summary["input_tokens"] == 10
