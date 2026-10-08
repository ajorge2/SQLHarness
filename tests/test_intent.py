from __future__ import annotations

import json
from pathlib import Path

from graphsql.intent import (
    IntentEdge,
    IntentGraph,
    repair_unique_source_spans,
    validate_intent_graph,
)


ROOT = Path(__file__).resolve().parents[1]


def test_example_intent_graph_is_valid():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    graph = IntentGraph.from_dict(payload)
    result = validate_intent_graph(graph)
    assert result.valid
    assert result.errors == ()
    assert graph.to_dict()["nodes"][0]["concept"] == "region"


def test_rejects_span_that_is_not_grounded_in_request():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    payload["nodes"][0]["spans"][0]["text"] = "division"
    result = validate_intent_graph(IntentGraph.from_dict(payload))
    assert not result.valid
    assert any(error.startswith("span_text_mismatch") for error in result.errors)


def test_rejects_cycle():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    graph = IntentGraph.from_dict(payload)
    cyclic = IntentGraph(
        request=graph.request,
        nodes=graph.nodes,
        edges=graph.edges + (IntentEdge(source="region", role="attribute", target="answer"),),
        evidence=graph.evidence,
    )
    result = validate_intent_graph(cyclic)
    assert not result.valid
    assert "cyclic_graph" in result.errors


def test_accepts_evidence_grounding():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    payload["evidence"] = "Customers are grouped by geographic region."
    payload["nodes"][0]["spans"] = [
        {"source": "evidence", "start": 36, "end": 42, "text": "region"}
    ]
    result = validate_intent_graph(IntentGraph.from_dict(payload))
    assert result.valid


def test_rejects_ungrounded_implicit_node_without_marker():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    payload["nodes"][1]["spans"] = []
    result = validate_intent_graph(IntentGraph.from_dict(payload))
    assert not result.valid
    assert "ungrounded_node_without_inferred_marker: customers" in result.errors

    payload["nodes"][1]["attributes"] = {"inferred": True}
    assert validate_intent_graph(IntentGraph.from_dict(payload)).valid


def test_rejects_disconnected_graph():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    payload["edges"] = [edge for edge in payload["edges"] if edge["target"] != "customers"]
    result = validate_intent_graph(IntentGraph.from_dict(payload))
    assert not result.valid
    assert "disconnected_graph" in result.errors


def test_repairs_unique_span_offset_without_guessing_meaning():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    payload["nodes"][0]["spans"][0].update({"start": 5, "end": 11})
    graph = IntentGraph.from_dict(payload)
    assert not validate_intent_graph(graph).valid

    repaired, repairs = repair_unique_source_spans(graph)
    assert validate_intent_graph(repaired).valid
    assert repairs == ("region:request[5:11]->[6:12]",)


def test_rejects_reversed_attribute_edge():
    payload = json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    payload["edges"][1] = {"source": "region", "role": "attribute", "target": "customers"}
    result = validate_intent_graph(IntentGraph.from_dict(payload))
    assert not result.valid
    assert any(error.startswith("invalid_edge_signature") for error in result.errors)
