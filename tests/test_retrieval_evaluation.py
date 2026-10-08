from __future__ import annotations

import json

import pytest

pytest.importorskip("sqlglot")

from graphsql.fragments import extract_sql_fragments
from graphsql.retrieval_evaluation import evaluate_fragment_retrieval, fragment_signature
from graphsql.types import BirdExample


def test_signature_ignores_schema_names_but_preserves_structure():
    left = extract_sql_fragments(
        "SELECT region FROM customers WHERE spend > 100",
        example_id="left",
        db_id="shop",
    )
    right = extract_sql_fragments(
        "SELECT state FROM accounts WHERE balance > 5",
        example_id="right",
        db_id="bank",
    )
    assert {fragment_signature(item) for item in left} == {
        fragment_signature(item) for item in right
    }


def test_evaluation_separates_catalog_coverage_from_retrieval_recall(tmp_path):
    corpus = extract_sql_fragments(
        "SELECT region, COUNT(customer_id) FROM customers GROUP BY region",
        example_id="train",
        db_id="shop",
    )
    example = BirdExample(
        example_id="heldout",
        db_id="bank",
        question="Count accounts by state.",
        evidence="",
        gold_sql="SELECT state, COUNT(account_id) FROM accounts GROUP BY state",
    )
    graph = {
        "graph_version": "0.2",
        "request": "Count accounts by state.",
        "evidence": "",
        "nodes": [
            {
                "node_id": "count",
                "kind": "operation",
                "concept": "count accounts",
                "spans": [{"source": "request", "start": 0, "end": 5, "text": "Count"}],
                "schema_candidates": ["accounts.account_id"],
            },
            {
                "node_id": "state",
                "kind": "attribute",
                "concept": "state",
                "spans": [{"source": "request", "start": 18, "end": 23, "text": "state"}],
                "schema_candidates": ["accounts.state"],
            },
            {
                "node_id": "output",
                "kind": "output",
                "concept": "return grouped counts",
                "spans": [],
                "schema_candidates": [],
            },
        ],
        "edges": [
            {"source": "count", "role": "group_by", "target": "state"},
            {"source": "output", "role": "returns", "target": "count"},
            {"source": "output", "role": "returns", "target": "state"},
        ],
    }
    output = tmp_path / "retrieval.json"
    summary = evaluate_fragment_retrieval(
        [example],
        graph_records={"heldout": {"graph": graph}},
        corpus=corpus,
        output_path=output,
        recall_at=(1, 5),
        top_k_per_intent=5,
    )
    records = json.loads(output.read_text())
    assert summary["graph_coverage"] == 1.0
    assert summary["catalog_signature_coverage"] == 1.0
    assert summary["evaluable_catalog_signature_coverage"] == 1.0
    assert summary["recall_at"]["5"]["micro_signature_recall"] == 1.0
    assert summary["mean_reciprocal_rank"] == 1.0
    assert summary["recall_at"]["1"]["eligible_query_hit_rate"] == 1.0
    assert records[0]["recall"]["5"]["catalog_conditional_signature_recall"] == 1.0


def test_missing_graph_counts_against_graph_coverage_not_retrieval(tmp_path):
    example = BirdExample("missing", "shop", "Return region.", "", "SELECT region FROM customers")
    corpus = extract_sql_fragments(
        "SELECT state FROM accounts",
        example_id="train",
        db_id="bank",
    )
    summary = evaluate_fragment_retrieval(
        [example],
        graph_records={},
        corpus=corpus,
        output_path=tmp_path / "retrieval.json",
        recall_at=(1,),
    )
    assert summary["graph_coverage"] == 0.0
    assert summary["catalog_signature_coverage"] == 1.0
    assert summary["recall_at"]["1"]["micro_signature_recall"] is None
