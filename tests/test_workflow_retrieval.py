from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqlharness.intent import EDGE_ROLES, IntentEdge, IntentGraph, IntentNode
from sqlharness.workflow_retrieval import rank_relationships


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {"customers": ("id", "region_id"), "regions": ("id", "name")}


def test_region_example_has_five_ranked_relationships_not_three_node_queries():
    graph = IntentGraph.from_dict(json.loads((ROOT / "examples/intent_graph_region.json").read_text()))
    result = rank_relationships(graph, SCHEMA)
    assert result["coverage"] == {"complete": True, "missing": []}
    rows = result["relationships"]
    assert [row["relation_id"] for row in rows] == [f"e{i}" for i in range(5)]
    assert [(row["source"], row["role"], row["target"]) for row in rows] == [(edge.source, edge.role, edge.target) for edge in graph.edges]
    winners = {row["role"]: row["candidates"][0] for row in rows}
    assert winners["theme"]["fragment_id"] == "aggregate.count"
    assert winners["group_by"]["kind"] == "group"
    assert winners["measure"]["kind"] == "limit"
    assert winners["returns"]["kind"] == "projection"
    assert winners["constrained_by"]["template_sql"].endswith("DESC")


def _aggregate_graph(op="sum", distinct=False):
    return IntentGraph(
        request="What is total paid revenue?",
        nodes=(
            IntentNode("total", "operation", op, schema_candidates=("orders.amount_usd",), attributes={"inferred": True, "distinct": distinct}),
            IntentNode("amount", "attribute", "amount", schema_candidates=("orders.amount_usd",), attributes={"inferred": True}),
            IntentNode("paid", "condition", "paid", schema_candidates=("orders.status",), attributes={"inferred": True, "operator": "="}),
            IntentNode("paid_value", "value", "paid", attributes={"inferred": True}),
            IntentNode("answer", "output", "answer"),
        ),
        edges=(
            IntentEdge("total", "measure", "amount"),
            IntentEdge("total", "filter", "paid"),
            IntentEdge("paid", "value", "paid_value"),
            IntentEdge("answer", "returns", "total"),
        ),
    )


def test_paid_revenue_uses_sum_and_keeps_filter_relationship_coverage():
    schema = {"orders": ("id", "amount_usd", "status")}
    result = rank_relationships(_aggregate_graph(), schema)
    assert result["coverage"]["complete"]
    assert [row["selected_fragment_id"] for row in result["relationships"]] == ["aggregate.sum", "filter.equal", "filter.equal", "projection.sum"]
    assert result == rank_relationships(_aggregate_graph(), schema)


def test_distinct_count_does_not_offer_count_all_or_plain_count():
    result = rank_relationships(_aggregate_graph("count", distinct=True), {"orders": ("amount_usd", "status")})
    assert result["coverage"]["complete"]
    aggregate = result["relationships"][0]["candidates"]
    projection = result["relationships"][-1]["candidates"]
    assert [item["fragment_id"] for item in aggregate] == ["aggregate.count_distinct"]
    assert [item["fragment_id"] for item in projection] == ["projection.count_distinct"]


def test_unknown_operation_abstains_instead_of_matching_generic_aggregate():
    result = rank_relationships(_aggregate_graph("forecast"), {"orders": ("amount_usd", "status")})
    assert not result["coverage"]["complete"]
    assert result["relationships"][0]["candidates"] == []
    assert result["relationships"][-1]["selected_fragment_id"] is None
    assert {row["relation_id"] for row in result["coverage"]["missing"]} == {"e0", "e3"}


def test_advanced_roles_are_explicit_missing_coverage():
    graph = IntentGraph("ratio", (IntentNode("ratio", "operation", "ratio"), IntentNode("amount", "attribute", "amount")), (IntentEdge("ratio", "numerator", "amount"),))
    result = rank_relationships(graph, {})
    assert not result["coverage"]["complete"]
    assert "unsupported_relationship: numerator" in result["coverage"]["missing"][0]["reason"]


def test_ranked_candidates_are_distinct_ordered_and_selected_first():
    graph = _aggregate_graph("count")
    result = rank_relationships(graph, {"orders": ("amount_usd", "status")}, top_k=10)
    for row in result["relationships"]:
        candidates = row["candidates"]
        assert len({item["template_sql"] for item in candidates}) == len(candidates)
        assert [item["rank"] for item in candidates] == list(range(1, len(candidates) + 1))
        assert [item["score"] for item in candidates] == sorted((item["score"] for item in candidates), reverse=True)
        assert row["selected_fragment_id"] == candidates[0]["fragment_id"]


def test_all_declared_roles_are_either_supported_or_explicitly_rejected():
    source = IntentNode("source", "operation", "count", attributes={"operator": "="})
    target = IntentNode("target", "attribute", "id")
    for role in EDGE_ROLES:
        graph = IntentGraph("question", (source, target), (IntentEdge("source", role, "target"),))
        result = rank_relationships(graph, {})
        assert len(result["relationships"]) == 1
        assert result["coverage"]["complete"] or result["coverage"]["missing"][0]["reason"]


@pytest.mark.parametrize("top_k", [0, -1, 11, True, 1.5])
def test_invalid_candidate_limit_is_rejected(top_k):
    with pytest.raises(ValueError):
        rank_relationships(_aggregate_graph(), {}, top_k)
