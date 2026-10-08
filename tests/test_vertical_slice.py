from __future__ import annotations

import json
import sqlite3

from graphsql.fragments import SQLFragment
from graphsql.types import BirdExample, Generation, TokenUsage
from graphsql.vertical_slice import run_vertical_slice


class FakeAssembler:
    def generate(self, **_kwargs):
        return Generation(
            sql="SELECT COUNT(*) FROM customers",
            model="fake-assembler",
            latency_ms=5.0,
            usage=TokenUsage(input_tokens=10, output_tokens=4),
        )


def test_vertical_slice_executes_candidate_through_authority(tmp_path):
    database_root = tmp_path / "databases"
    database_dir = database_root / "shop"
    database_dir.mkdir(parents=True)
    with sqlite3.connect(database_dir / "shop.sqlite") as connection:
        connection.executescript(
            """
            CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT);
            INSERT INTO customers VALUES (1, 'Ada'), (2, 'Grace');
            """
        )

    question = "How many customers?"
    graph = {
        "graph_version": "0.2",
        "request": question,
        "evidence": "",
        "nodes": [
            {
                "node_id": "count",
                "kind": "operation",
                "concept": "count",
                "spans": [{"source": "request", "start": 0, "end": 8, "text": "How many"}],
                "schema_candidates": ["customers.id"],
            },
            {
                "node_id": "customers",
                "kind": "entity",
                "concept": "customers",
                "spans": [{"source": "request", "start": 9, "end": 18, "text": "customers"}],
                "schema_candidates": ["customers"],
            },
            {"node_id": "answer", "kind": "output", "concept": "answer"},
        ],
        "edges": [
            {"source": "count", "role": "theme", "target": "customers"},
            {"source": "answer", "role": "returns", "target": "count"},
        ],
    }
    output_path = tmp_path / "vertical.jsonl"
    summary = run_vertical_slice(
        [
            BirdExample(
                example_id="1",
                db_id="shop",
                question=question,
                evidence="",
                gold_sql="SELECT COUNT(id) FROM customers",
            )
        ],
        database_root=database_root,
        graph_records={
            "1": {
                "example_id": "1",
                "graph": graph,
                "latency_ms": 10.0,
                "usage": {"input_tokens": 20, "output_tokens": 10},
            }
        },
        corpus=[
            SQLFragment(
                fragment_id="train:aggregate:0",
                example_id="train",
                db_id="other",
                kind="aggregate",
                scope_id="select_0",
                concrete_sql="COUNT(id)",
                template_sql="COUNT({column_1})",
                semantic_text="aggregate count column",
            )
        ],
        assembler=FakeAssembler(),
        output_path=output_path,
    )

    record = json.loads(output_path.read_text().strip())
    assert summary["end_to_end_accuracy"] == 1.0
    assert summary["authority_boundary"] == "DatabaseAuthority (also exposed through MCP)"
    assert record["authority_receipt"]["decision"] == "executed"
    assert record["authority_receipt"]["receipt_id"]
