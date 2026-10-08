from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("sqlglot")

from graphsql.fragments import (
    FastEmbedFragmentRetriever,
    IntentFragment,
    LexicalFragmentRetriever,
    SQLFragment,
    extract_sql_fragments,
    serialize_intent_fragments,
)
from graphsql.intent import IntentGraph


ROOT = Path(__file__).resolve().parents[1]


def test_extracts_parameterized_compositional_fragments():
    fragments = extract_sql_fragments(
        """
        SELECT c.region, COUNT(o.id)
        FROM customers c JOIN orders o ON c.id = o.customer_id
        WHERE o.amount > 100
        GROUP BY c.region
        ORDER BY COUNT(o.id) DESC
        LIMIT 3
        """,
        example_id="1",
        db_id="shop",
    )
    kinds = {fragment.kind for fragment in fragments}
    assert {"projection", "join", "filter", "group", "order", "limit", "aggregate"} <= kinds
    join = next(fragment for fragment in fragments if fragment.kind == "join")
    assert "{column_1}" in join.template_sql
    assert "{column_2}" in join.template_sql
    assert "customer_id" in join.concrete_sql
    assert "{column_{value" not in " ".join(fragment.template_sql for fragment in fragments)
    assert "§" not in " ".join(fragment.template_sql for fragment in fragments)


def test_serializes_local_intent_context_and_retrieves_compatible_fragment():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    graph = IntentGraph.from_dict(payload)
    intent_fragments = serialize_intent_fragments(graph)
    sql_fragments = extract_sql_fragments(
        "SELECT region, COUNT(customer_id) FROM customers GROUP BY region ORDER BY COUNT(customer_id) DESC LIMIT 1",
        example_id="train",
        db_id="shop",
    )
    hits = LexicalFragmentRetriever(sql_fragments).retrieve(intent_fragments, max_total=5)
    assert hits
    assert any(hit.fragment.kind == "aggregate" for hit in hits)
    assert all(hit.fragment.example_id == "train" for hit in hits)


class _FakeDenseEncoder:
    def passage_embed(self, texts):
        for text in texts:
            yield [1.0, 0.0] if "count" in text else [0.0, 1.0]

    def query_embed(self, texts):
        for text in texts:
            yield [1.0, 0.0] if "count" in text else [0.0, 1.0]


def test_dense_retriever_ranks_by_cosine_similarity_without_optional_dependency():
    fragments = extract_sql_fragments(
        "SELECT region, COUNT(customer_id) FROM customers",
        example_id="train",
        db_id="shop",
    )
    retriever = FastEmbedFragmentRetriever(fragments, encoder=_FakeDenseEncoder())
    hits = retriever.retrieve(
        [IntentFragment("count", "operation", "count customers")],
        top_k_per_intent=1,
        max_total=1,
    )
    assert hits[0].fragment.kind == "projection"
    assert "COUNT" in hits[0].fragment.concrete_sql


def test_retrieval_returns_each_parameterized_sql_meaning_once():
    fragments = [
        SQLFragment(
            fragment_id=f"{index}:aggregate",
            example_id=str(index),
            db_id="shop",
            kind="aggregate",
            scope_id="select_0",
            concrete_sql=concrete,
            template_sql="COUNT({column_1})",
            semantic_text=semantic,
        )
        for index, (concrete, semantic) in enumerate(
            (("COUNT(id)", "count customer id"), ("COUNT(order_id)", "count order id"))
        )
    ]
    hits = LexicalFragmentRetriever(fragments).retrieve(
        [IntentFragment("count", "operation", "count orders")],
        top_k_per_intent=2,
        max_total=2,
    )
    assert len(hits) == 1
    assert hits[0].fragment.template_sql == "COUNT({column_1})"
