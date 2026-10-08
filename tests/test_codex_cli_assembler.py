from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from graphsql.fragments import RetrievalHit, SQLFragment
from graphsql.intent import IntentGraph
from graphsql.providers.codex_cli_assembler import CodexCLIFragmentAssembler


ROOT = Path(__file__).resolve().parents[1]


def test_fragment_assembler_passes_graph_and_templates_without_concrete_training_sql():
    captured = {}

    def fake_runner(command, **kwargs):
        captured["prompt"] = kwargs["input"]
        output_path = command[command.index("--output-last-message") + 1]
        Path(output_path).write_text('{"sql":"SELECT COUNT(*) FROM customers"}')
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout=(
                '{"type":"turn.completed","usage":'
                '{"input_tokens":10,"cached_input_tokens":0,'
                '"output_tokens":5,"reasoning_output_tokens":0}}\n'
            ),
        )

    graph = IntentGraph.from_dict(
        json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    )
    fragment = SQLFragment(
        fragment_id="train:aggregate:1",
        example_id="train",
        db_id="other",
        kind="aggregate",
        scope_id="select_0",
        concrete_sql="COUNT(secret_training_column)",
        template_sql="COUNT({column_1})",
        semantic_text="aggregate count column",
    )
    assembler = CodexCLIFragmentAssembler(model="test", runner=fake_runner)
    generation = assembler.generate(
        question="How many customers?",
        evidence="",
        schema="customers(id)",
        graph=graph,
        retrieval_hits=[RetrievalHit("customer_count", 2.0, fragment)],
    )

    assert generation.sql == "SELECT COUNT(*) FROM customers"
    assert "COUNT({column_1})" in captured["prompt"]
    assert "secret_training_column" not in captured["prompt"]


def test_fragment_assembler_repair_includes_only_observed_failure_context():
    captured = {}

    def fake_runner(command, **kwargs):
        captured["prompt"] = kwargs["input"]
        output_path = command[command.index("--output-last-message") + 1]
        Path(output_path).write_text('{"sql":"SELECT COUNT(*) FROM customers"}')
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout='{\"type\":\"turn.completed\",\"usage\":{}}\n',
        )

    graph = IntentGraph.from_dict(
        json.loads((ROOT / "examples" / "intent_graph_region.json").read_text())
    )
    assembler = CodexCLIFragmentAssembler(model="test", runner=fake_runner)
    generation = assembler.repair(
        question="How many customers?",
        evidence="",
        schema="customers(id)",
        graph=graph,
        retrieval_hits=[],
        previous_sql="SELECT missing FROM customers",
        error="unknown_columns: missing",
    )

    assert generation.sql == "SELECT COUNT(*) FROM customers"
    assert "SELECT missing FROM customers" in captured["prompt"]
    assert "unknown_columns: missing" in captured["prompt"]
