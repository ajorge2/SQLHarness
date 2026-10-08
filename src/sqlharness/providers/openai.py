from __future__ import annotations

import json
import time
from typing import Any

from sqlharness.types import Generation, TokenUsage


SYSTEM_PROMPT = """You translate natural-language data questions into SQLite SQL.
Use only the supplied schema and evidence. Return one executable query. Do not invent tables or
columns. The response must match the requested JSON schema."""


class OpenAISQLGenerator:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("A model identifier is required")
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise RuntimeError("Install project dependencies before using OpenAI") from error
            client = OpenAI()
        self._client = client
        self._model = model
        self._reasoning_effort = reasoning_effort

    def generate(self, *, question: str, evidence: str, schema: str) -> Generation:
        user_prompt = render_user_prompt(question=question, evidence=evidence, schema=schema)
        request: dict[str, Any] = {
            "model": self._model,
            "store": False,
            "input": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "sql_answer",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {"sql": {"type": "string"}},
                        "required": ["sql"],
                        "additionalProperties": False,
                    },
                }
            },
        }
        if self._reasoning_effort:
            request["reasoning"] = {"effort": self._reasoning_effort}

        started = time.perf_counter()
        response = self._client.responses.create(**request)
        latency_ms = (time.perf_counter() - started) * 1000

        if getattr(response, "status", None) != "completed":
            detail = getattr(response, "incomplete_details", None)
            raise RuntimeError(f"Model response did not complete: {detail}")

        raw_output = response.output_text
        try:
            payload = json.loads(raw_output)
            sql = payload["sql"].strip()
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as error:
            raise RuntimeError("Structured model response did not contain SQL") from error
        if not sql:
            raise RuntimeError("Model returned an empty SQL query")

        return Generation(
            sql=sql,
            model=self._model,
            latency_ms=latency_ms,
            usage=_extract_usage(getattr(response, "usage", None)),
            raw_output=raw_output,
        )


def render_user_prompt(*, question: str, evidence: str, schema: str) -> str:
    evidence_text = evidence or "No additional evidence supplied."
    return f"""DATABASE SCHEMA
{schema}

EXTERNAL EVIDENCE
{evidence_text}

QUESTION
{question}
"""


def _extract_usage(usage: Any | None) -> TokenUsage:
    if usage is None:
        return TokenUsage()
    input_details = getattr(usage, "input_tokens_details", None)
    output_details = getattr(usage, "output_tokens_details", None)
    return TokenUsage(
        input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
        cached_input_tokens=int(getattr(input_details, "cached_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        reasoning_tokens=int(getattr(output_details, "reasoning_tokens", 0) or 0),
    )
