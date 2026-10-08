from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from sqlharness.providers.codex_cli import CodexCLISQLGenerator


def test_codex_cli_adapter_uses_ephemeral_readonly_session_and_captures_usage():
    captured = {}

    def fake_runner(command, **kwargs):
        captured["command"] = command
        captured["prompt"] = kwargs["input"]
        output_path = command[command.index("--output-last-message") + 1]
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump({"sql": "SELECT COUNT(*) FROM customers"}, handle)
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout=(
                '{"type":"turn.completed","usage":'
                '{"input_tokens":120,"cached_input_tokens":20,'
                '"output_tokens":30,"reasoning_output_tokens":10}}\n'
            ),
        )

    generator = CodexCLISQLGenerator(
        model="supported-cli-model",
        reasoning_effort="medium",
        runner=fake_runner,
    )
    generation = generator.generate(
        question="How many customers are there?",
        evidence="",
        schema="customers(id, name)",
    )

    assert generation.sql == "SELECT COUNT(*) FROM customers"
    assert generation.model == "codex-cli/supported-cli-model"
    assert generation.usage.input_tokens == 120
    assert generation.usage.cached_input_tokens == 20
    assert generation.usage.output_tokens == 30
    assert generation.usage.reasoning_tokens == 10
    assert "--ephemeral" in captured["command"]
    assert "--ignore-user-config" in captured["command"]
    assert captured["command"][captured["command"].index("--sandbox") + 1] == "read-only"
    assert "Do not inspect files" in captured["prompt"]


def test_codex_cli_adapter_reports_bounded_timeout():
    def timeout_runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    generator = CodexCLISQLGenerator(
        model="supported-cli-model",
        timeout_seconds=12,
        runner=timeout_runner,
    )
    with pytest.raises(RuntimeError, match="12-second limit"):
        generator.generate(question="Question", evidence="", schema="table(id)")
