from __future__ import annotations

import json
import sqlite3

import pytest

pytest.importorskip("sqlglot")

from graphsql.benchmark import run_baseline
from graphsql.experiment import PricingRates
from graphsql.types import BirdExample, Generation, TokenUsage


class FakeGenerator:
    def generate(self, *, question: str, evidence: str, schema: str) -> Generation:
        assert "customers" in schema
        return Generation(
            sql="SELECT COUNT(*) FROM customers",
            model="fake-sql-model",
            latency_ms=12.5,
            usage=TokenUsage(input_tokens=20, output_tokens=5, reasoning_tokens=2),
        )


def test_runs_end_to_end_and_writes_trace(tmp_path):
    database_directory = tmp_path / "databases" / "shop"
    database_directory.mkdir(parents=True)
    database_path = database_directory / "shop.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)")
        connection.executemany(
            "INSERT INTO customers(name) VALUES (?)",
            [("Ada",), ("Grace",), ("Linus",)],
        )

    output_path = tmp_path / "artifacts" / "baseline.jsonl"
    summary = run_baseline(
        [
            BirdExample(
                example_id="shop:0",
                db_id="shop",
                question="How many customers are there?",
                evidence="",
                gold_sql="SELECT COUNT(id) FROM customers",
            )
        ],
        database_root=tmp_path / "databases",
        generator=FakeGenerator(),
        output_path=output_path,
        pricing=PricingRates(
            model="fake-sql-model",
            input_usd_per_million=2.0,
            cached_input_usd_per_million=0.5,
            output_usd_per_million=8.0,
            captured_at="2026-10-07",
        ),
    )

    assert summary["execution_accuracy"] == 1.0
    assert summary["local_evaluation_coverage"] == 1.0
    assert summary["model_total_tokens"] == 25
    assert summary["model_reasoning_tokens"] == 2
    assert summary["estimated_model_cost_usd"] == 0.00008
    trace = json.loads(output_path.read_text().strip())
    assert trace["execution_correct"] is True
    assert trace["validation"]["valid"] is True
    assert output_path.with_suffix(".summary.json").exists()
