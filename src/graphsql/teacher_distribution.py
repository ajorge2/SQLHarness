from __future__ import annotations

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


def analyze_teacher_distribution(
    trace_paths: Iterable[str | Path],
    *,
    output_path: str | Path,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace_path in trace_paths:
        for line in Path(trace_path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            grouped[str(record["example_id"])].append(record)

    records = []
    for example_id, samples in sorted(grouped.items()):
        valid_graphs = [sample["graph"] for sample in samples if sample.get("graph")]
        node_sets = [_node_signatures(graph) for graph in valid_graphs]
        edge_sets = [_edge_signatures(graph) for graph in valid_graphs]
        records.append(
            {
                "example_id": example_id,
                "samples": len(samples),
                "valid_graphs": len(valid_graphs),
                "unique_graphs": len({_canonical_graph(graph) for graph in valid_graphs}),
                "mean_pairwise_node_jaccard": _mean_pairwise_jaccard(node_sets),
                "mean_pairwise_edge_jaccard": _mean_pairwise_jaccard(edge_sets),
                "node_signatures": [sorted(values) for values in node_sets],
                "edge_signatures": [sorted(values) for values in edge_sets],
            }
        )

    repeated = [record for record in records if record["samples"] > 1]
    summary = {
        "examples": len(records),
        "samples": sum(record["samples"] for record in records),
        "examples_with_repeated_samples": len(repeated),
        "repeated_examples_with_multiple_valid_graphs": sum(
            record["valid_graphs"] > 1 for record in repeated
        ),
        "mean_node_jaccard_on_repeated_valid_examples": _mean(
            record["mean_pairwise_node_jaccard"]
            for record in repeated
            if record["mean_pairwise_node_jaccard"] is not None
        ),
        "mean_edge_jaccard_on_repeated_valid_examples": _mean(
            record["mean_pairwise_edge_jaccard"]
            for record in repeated
            if record["mean_pairwise_edge_jaccard"] is not None
        ),
        "interpretation": (
            "Repeated teacher samples estimate representation variability; they do not "
            "establish semantic correctness without gold-compatible or human review."
        ),
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"summary": summary, "examples": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _canonical_graph(graph: dict[str, Any]) -> str:
    payload = {
        "nodes": sorted(_node_signatures(graph)),
        "edges": sorted(_edge_signatures(graph)),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _node_signatures(graph: dict[str, Any]) -> set[str]:
    return {
        f"{node.get('kind', '')}|{str(node.get('concept', '')).strip().lower()}"
        for node in graph.get("nodes", ())
    }


def _edge_signatures(graph: dict[str, Any]) -> set[str]:
    nodes = {
        str(node.get("node_id")): (
            str(node.get("kind", "")),
            str(node.get("concept", "")).strip().lower(),
        )
        for node in graph.get("nodes", ())
    }
    return {
        "|".join((*nodes.get(str(edge.get("source")), ("?", "?")), str(edge.get("role", "")), *nodes.get(str(edge.get("target")), ("?", "?"))))
        for edge in graph.get("edges", ())
    }


def _mean_pairwise_jaccard(values: list[set[str]]) -> float | None:
    if len(values) < 2:
        return None
    return _mean(_jaccard(left, right) for left, right in combinations(values, 2))


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def _mean(values: Iterable[float]) -> float | None:
    observed = list(values)
    return sum(observed) / len(observed) if observed else None
