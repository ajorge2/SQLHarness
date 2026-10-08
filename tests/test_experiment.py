from __future__ import annotations

import json
import sqlite3

import pytest

pytest.importorskip("sqlglot")

from sqlharness.dataset import load_bird_examples
from sqlharness.experiment import (
    PricingRates,
    build_preflight_manifest,
    estimate_usage_cost,
    is_select_only,
    select_readonly_examples,
)
from sqlharness.types import TokenUsage


def test_select_only_filter_excludes_mutations():
    assert is_select_only("SELECT * FROM customers")
    assert is_select_only("WITH c AS (SELECT * FROM customers) SELECT * FROM c")
    assert not is_select_only("DELETE FROM customers")


def test_cost_accounts_for_cached_input_without_double_counting_reasoning():
    pricing = PricingRates(
        model="example",
        input_usd_per_million=2.0,
        cached_input_usd_per_million=0.5,
        output_usd_per_million=8.0,
        captured_at="2026-10-07",
    )
    usage = TokenUsage(
        input_tokens=1_000_000,
        cached_input_tokens=250_000,
        output_tokens=100_000,
        reasoning_tokens=80_000,
    )
    assert estimate_usage_cost(usage, pricing) == 2.425


def test_preflight_manifest_fingerprints_selection_and_database(tmp_path):
    database_dir = tmp_path / "databases" / "shop"
    database_dir.mkdir(parents=True)
    with sqlite3.connect(database_dir / "shop.sqlite") as connection:
        connection.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY)")

    dataset_path = tmp_path / "mini_dev_sqlite.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "id": "read",
                    "db_id": "shop",
                    "question": "List customers",
                    "evidence": "",
                    "SQL": "SELECT id FROM customers",
                },
                {
                    "id": "write",
                    "db_id": "shop",
                    "question": "Delete customers",
                    "evidence": "",
                    "SQL": "DELETE FROM customers",
                },
            ]
        )
    )
    examples = load_bird_examples(dataset_path)
    selected, omitted = select_readonly_examples(examples)
    manifest = build_preflight_manifest(
        dataset_path=dataset_path,
        database_root=tmp_path / "databases",
        all_examples=examples,
        selected_examples=selected,
        omitted_non_readonly=omitted,
        model="pinned-model",
        reasoning_effort="low",
        timeout_seconds=5.0,
        max_rows=10_000,
        offset=0,
        limit=None,
        pricing=None,
    )
    assert manifest["status"] == "preflight"
    assert manifest["benchmark"]["selected_examples"] == 1
    assert manifest["benchmark"]["omitted_non_readonly_or_unparseable"] == 1
    assert manifest["benchmark"]["gold_execution_audit"]["ready"] is True
    assert manifest["benchmark"]["gold_execution_audit"]["succeeded"] == 1
    assert len(manifest["benchmark"]["dataset_sha256"]) == 64
    assert len(manifest["benchmark"]["databases"][0]["sha256"]) == 64
    assert len(manifest["environment"]["source_sha256"]) == 64
