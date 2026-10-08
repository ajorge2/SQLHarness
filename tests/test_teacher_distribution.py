from __future__ import annotations

import json

from graphsql.teacher_distribution import analyze_teacher_distribution


def test_teacher_distribution_measures_repeated_graph_variability(tmp_path):
    trace_one = tmp_path / "one.jsonl"
    trace_two = tmp_path / "two.jsonl"
    trace_one.write_text(
        json.dumps(
            {
                "example_id": "1",
                "graph": {
                    "nodes": [
                        {"node_id": "a", "kind": "operation", "concept": "count"},
                        {"node_id": "o", "kind": "output", "concept": "answer"},
                    ],
                    "edges": [{"source": "o", "role": "returns", "target": "a"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    trace_two.write_text(
        json.dumps(
            {
                "example_id": "1",
                "graph": {
                    "nodes": [
                        {"node_id": "x", "kind": "operation", "concept": "total"},
                        {"node_id": "o", "kind": "output", "concept": "answer"},
                    ],
                    "edges": [{"source": "o", "role": "returns", "target": "x"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output = tmp_path / "distribution.json"
    summary = analyze_teacher_distribution([trace_one, trace_two], output_path=output)
    detail = json.loads(output.read_text())
    assert summary["examples_with_repeated_samples"] == 1
    assert summary["mean_node_jaccard_on_repeated_valid_examples"] == 1 / 3
    assert detail["examples"][0]["unique_graphs"] == 2
