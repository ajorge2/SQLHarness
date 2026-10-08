from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from graphsql.intent import EDGE_ROLES, GRAPH_VERSION, NODE_KINDS, IntentGraph
from graphsql.providers.codex_cli import run_codex_structured
from graphsql.types import TokenUsage


INTENT_GRAPH_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "graph_version": {"type": "string", "enum": [GRAPH_VERSION]},
        "request": {"type": "string"},
        "evidence": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "kind": {"type": "string", "enum": sorted(NODE_KINDS)},
                    "concept": {"type": "string"},
                    "spans": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string", "enum": ["request", "evidence"]},
                                "start": {"type": "integer", "minimum": 0},
                                "end": {"type": "integer", "minimum": 1},
                                "text": {"type": "string"},
                            },
                            "required": ["source", "start", "end", "text"],
                            "additionalProperties": False,
                        },
                    },
                    "schema_candidates": {"type": "array", "items": {"type": "string"}},
                    "attributes": {
                        "type": "object",
                        "properties": {
                            "inferred": {"type": ["boolean", "null"]},
                            "distinct": {"type": ["boolean", "null"]},
                            "limit": {"type": ["integer", "null"], "minimum": 1},
                            "tie_policy": {"type": ["string", "null"]},
                            "direction": {"type": ["string", "null"]},
                            "operator": {"type": ["string", "null"]},
                            "unit": {"type": ["string", "null"]},
                        },
                        "required": [
                            "inferred",
                            "distinct",
                            "limit",
                            "tie_policy",
                            "direction",
                            "operator",
                            "unit",
                        ],
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "node_id",
                    "kind",
                    "concept",
                    "spans",
                    "schema_candidates",
                    "attributes",
                ],
                "additionalProperties": False,
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "role": {"type": "string", "enum": sorted(EDGE_ROLES)},
                    "target": {"type": "string"},
                },
                "required": ["source", "role", "target"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["graph_version", "request", "evidence", "nodes", "edges"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class IntentGraphGeneration:
    graph: IntentGraph
    model: str
    latency_ms: float
    usage: TokenUsage
    raw_output: str


class CodexCLIIntentGraphGenerator:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str | None = None,
        executable: str = "codex",
        timeout_seconds: float = 300.0,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._executable = executable
        self._timeout_seconds = timeout_seconds
        self._runner = runner

    def generate(self, *, question: str, evidence: str, schema: str) -> IntentGraphGeneration:
        prompt = _render_intent_prompt(question=question, evidence=evidence, schema=schema)
        raw_output, usage, latency_ms = run_codex_structured(
            prompt=prompt,
            output_schema=INTENT_GRAPH_SCHEMA,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            executable=self._executable,
            timeout_seconds=self._timeout_seconds,
            runner=self._runner,
        )
        try:
            graph = IntentGraph.from_dict(json.loads(raw_output))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Codex CLI response did not contain an intent graph") from error
        return IntentGraphGeneration(
            graph=graph,
            model=f"codex-cli/{self._model}",
            latency_ms=latency_ms,
            usage=usage,
            raw_output=raw_output,
        )


def _render_intent_prompt(*, question: str, evidence: str, schema: str) -> str:
    return f"""Convert the supplied natural-language database request into SQLHarness intent graph v{GRAPH_VERSION}.

The graph represents semantic intent, not SQL syntax. Use only these node kinds:
{', '.join(sorted(NODE_KINDS))}.

Use only these edge roles:
{', '.join(sorted(EDGE_ROLES))}.

Rules:
- Copy the request and evidence strings exactly into the output.
- Ground explicit meanings to exact zero-based, end-exclusive spans in request or evidence.
- Output and scope nodes may omit spans. Any other node without a span must set attributes.inferred=true.
- Use logic nodes for and/or/not, scope nodes for nested populations, and relation nodes for semantic relationships.
- Use numerator and denominator edges for percentages or ratios.
- Include exactly one output node and connect every node into one acyclic graph.
- Schema candidates must use exact supplied table or table.column names.
- Do not create nodes named after SQL clauses such as SELECT, JOIN, WHERE, GROUP BY, or CTE.
- Do not output SQL or an explanation.
- Do not inspect files, browse, run commands, or use tools.

Directed edge conventions:
- entity or relation -attribute-> attribute
- relation -source-> entity and relation -target-> entity
- output -returns-> attribute, entity, or operation
- logic -operand-> condition or logic
- condition -compare-> attribute or operation; condition -value-> value
- operation -measure-> attribute or operation; operation -group_by-> attribute or entity
- entity, scope, output, or operation -joined_by-> relation
- output or operation -optional-> attribute, entity, or operation

DATABASE SCHEMA
{schema}

EVIDENCE
{evidence or 'No additional evidence supplied.'}

REQUEST
{question}
"""
