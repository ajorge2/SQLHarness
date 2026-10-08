from __future__ import annotations

import json
from typing import Any, Callable, Iterable

from graphsql.fragments import RetrievalHit
from graphsql.intent import IntentGraph
from graphsql.providers.codex_cli import SQL_ANSWER_SCHEMA, run_codex_structured
from graphsql.types import Generation


class CodexCLIFragmentAssembler:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str | None = None,
        timeout_seconds: float = 120.0,
        executable: str = "codex",
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._timeout_seconds = timeout_seconds
        self._executable = executable
        self._runner = runner

    def generate(
        self,
        *,
        question: str,
        evidence: str,
        schema: str,
        graph: IntentGraph,
        retrieval_hits: Iterable[RetrievalHit],
    ) -> Generation:
        prompt = _render_assembly_prompt(
            question=question,
            evidence=evidence,
            schema=schema,
            graph=graph,
            retrieval_hits=list(retrieval_hits),
        )
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
            sql = str(json.loads(raw_output)["sql"]).strip()
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise RuntimeError("Fragment assembler did not return structured SQL") from error
        if not sql:
            raise RuntimeError("Fragment assembler returned empty SQL")
        return Generation(
            sql=sql,
            model=f"codex-cli/{self._model}:fragment-assembler",
            latency_ms=latency_ms,
            usage=usage,
            raw_output=raw_output,
        )

    def repair(
        self,
        *,
        question: str,
        evidence: str,
        schema: str,
        graph: IntentGraph,
        retrieval_hits: Iterable[RetrievalHit],
        previous_sql: str,
        error: str,
    ) -> Generation:
        prompt = _render_assembly_prompt(
            question=question,
            evidence=evidence,
            schema=schema,
            graph=graph,
            retrieval_hits=list(retrieval_hits),
            repair_context={"previous_sql": previous_sql, "error": error},
        )
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
            sql = str(json.loads(raw_output)["sql"]).strip()
        except (json.JSONDecodeError, KeyError, TypeError) as error_value:
            raise RuntimeError("Fragment assembler repair did not return structured SQL") from error_value
        if not sql:
            raise RuntimeError("Fragment assembler repair returned empty SQL")
        return Generation(
            sql=sql,
            model=f"codex-cli/{self._model}:fragment-assembler-repair",
            latency_ms=latency_ms,
            usage=usage,
            raw_output=raw_output,
        )


def _render_assembly_prompt(
    *,
    question: str,
    evidence: str,
    schema: str,
    graph: IntentGraph,
    retrieval_hits: list[RetrievalHit],
    repair_context: dict[str, str] | None = None,
) -> str:
    fragment_payload = [
        {
            "matched_intent_node": hit.query_node_id,
            "score": hit.score,
            "kind": hit.fragment.kind,
            "semantic_text": hit.fragment.semantic_text,
            "sql_template": hit.fragment.template_sql,
            "source_example_id": hit.fragment.example_id,
        }
        for hit in retrieval_hits
    ]
    repair = ""
    if repair_context:
        repair = f"""
REPAIR ONE FAILED PROPOSAL
Previous SQL: {repair_context['previous_sql']}
Observed validator or database error: {repair_context['error']}
Return one corrected query. Do not repeat the failed proposal unchanged.
"""
    return f"""Assemble one executable SQLite query for the supplied request.

The intent graph is the semantic plan. Retrieved fragments are reusable structural hints from other databases, not SQL to copy literally. Replace every placeholder and use only tables and columns in the supplied schema. Ignore any retrieved identifier that is absent from this schema. Return only the JSON object required by the output schema.

Do not inspect files, browse, run commands, or use tools.

DATABASE SCHEMA
{schema}

EVIDENCE
{evidence or 'No additional evidence supplied.'}

REQUEST
{question}

INTENT GRAPH
{json.dumps(graph.to_dict(), ensure_ascii=False, sort_keys=True)}

RETRIEVED SQL FRAGMENTS
{json.dumps(fragment_payload, ensure_ascii=False, sort_keys=True)}
{repair}
"""
