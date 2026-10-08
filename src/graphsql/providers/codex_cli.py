from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from graphsql.providers.openai import SYSTEM_PROMPT, render_user_prompt
from graphsql.types import Generation, TokenUsage


SQL_ANSWER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {"sql": {"type": "string"}},
    "required": ["sql"],
    "additionalProperties": False,
}


class CodexCLISQLGenerator:
    """Temporary benchmark adapter for a ChatGPT-authenticated Codex CLI.

    This is deliberately identified separately from the OpenAI API baseline. Codex
    adds its own agent runtime and system context, and ChatGPT-plan usage cannot be
    converted into API spend even when the CLI reports token counts.
    """

    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str | None = None,
        executable: str = "codex",
        timeout_seconds: float = 300.0,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("A model identifier is required")
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._executable = executable
        self._timeout_seconds = timeout_seconds
        self._runner = runner or subprocess.run

    def generate(self, *, question: str, evidence: str, schema: str) -> Generation:
        prompt = _render_codex_prompt(question=question, evidence=evidence, schema=schema)
        raw_output, usage, latency_ms = run_codex_structured(
            prompt=prompt,
            output_schema=SQL_ANSWER_SCHEMA,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            executable=self._executable,
            timeout_seconds=self._timeout_seconds,
            runner=self._runner,
        )
        try:
            payload = json.loads(raw_output)
            sql = payload["sql"].strip()
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as error:
            raise RuntimeError("Codex CLI response did not contain structured SQL") from error
        if not sql:
            raise RuntimeError("Codex CLI returned an empty SQL query")

        return Generation(
            sql=sql,
            model=f"codex-cli/{self._model}",
            latency_ms=latency_ms,
            usage=usage,
            raw_output=raw_output,
        )


def run_codex_structured(
    *,
    prompt: str,
    output_schema: dict[str, Any],
    model: str,
    reasoning_effort: str | None,
    executable: str = "codex",
    timeout_seconds: float = 300.0,
    runner: Callable[..., Any] | None = None,
) -> tuple[str, TokenUsage, float]:
    active_runner = runner or subprocess.run
    with tempfile.TemporaryDirectory(prefix="graphsql-codex-") as temporary_directory:
        working_directory = Path(temporary_directory)
        schema_path = working_directory / "output.schema.json"
        output_path = working_directory / "answer.json"
        schema_path.write_text(json.dumps(output_schema), encoding="utf-8")

        command = [
            executable,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--model",
            model,
        ]
        if reasoning_effort:
            command.extend(["--config", f'model_reasoning_effort="{reasoning_effort}"'])
        command.extend(
            [
                "--output-schema",
                str(schema_path),
                "--json",
                "--output-last-message",
                str(output_path),
                "-",
            ]
        )

        environment = dict(os.environ)
        environment["NO_COLOR"] = "1"
        started = time.perf_counter()
        try:
            completed = active_runner(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                cwd=working_directory,
                env=environment,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                f"Codex CLI generation exceeded the {timeout_seconds:g}-second limit"
            ) from error
        latency_ms = (time.perf_counter() - started) * 1000
        if completed.returncode != 0:
            detail = "\n".join(
                part.strip()
                for part in (completed.stderr, completed.stdout)
                if part and part.strip()
            ) or "unknown error"
            raise RuntimeError(f"Codex CLI generation failed: {detail[-2000:]}")
        if not output_path.exists():
            raise RuntimeError("Codex CLI completed without writing its final response")

        raw_output = output_path.read_text(encoding="utf-8").strip()
        return raw_output, _extract_cli_usage(completed.stdout), latency_ms


def _render_codex_prompt(*, question: str, evidence: str, schema: str) -> str:
    task = render_user_prompt(question=question, evidence=evidence, schema=schema)
    return f"""{SYSTEM_PROMPT}

{task}
Do not inspect files, browse, run commands, or use any tools. Solve only from the supplied text.
Return only the JSON object required by the output schema.
"""


def _extract_cli_usage(event_stream: str) -> TokenUsage:
    for line in reversed(event_stream.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage") or {}
        return TokenUsage(
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            cached_input_tokens=int(usage.get("cached_input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            reasoning_tokens=int(usage.get("reasoning_output_tokens", 0) or 0),
        )
    return TokenUsage()
