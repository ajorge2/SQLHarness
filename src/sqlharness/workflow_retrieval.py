"""Portable relationship-level retrieval for the live MCP workflow.

This is a deterministic lexical/catalog ranker, not the research learned model.
Every graph edge receives its own ranked candidate list.  Templates describe SQL
expression shapes; an assembler must ground their placeholders to the database.
Unsupported relationships or operations abstain rather than claiming coverage.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from .intent import IntentGraph, IntentNode


CATALOG_VERSION = "sqlite-relationships-v1"
RANKER_VERSION = "relationship-lexical-v1"


@dataclass(frozen=True)
class FragmentTemplate:
    fragment_id: str
    kind: str
    template_sql: str
    semantic_text: str
    operator: str = ""


def _template(identifier: str, kind: str, sql: str, meaning: str, operator: str = "") -> FragmentTemplate:
    return FragmentTemplate(identifier, kind, sql, meaning, operator)


CATALOG: tuple[FragmentTemplate, ...] = (
    _template("projection.column", "projection", "{column_1}", "return the requested named field"),
    _template("projection.all", "projection", "*", "return the requested records and fields"),
    _template("projection.distinct", "projection", "DISTINCT {column_1}", "return distinct unique values", "distinct"),
    *(
        _template(f"projection.{op}", "projection", f"{op.upper()}({{column_1}})", f"return {op} aggregate", op)
        for op in ("count", "sum", "avg", "min", "max")
    ),
    _template("projection.count_all", "projection", "COUNT(*)", "return count of all rows", "count"),
    _template("projection.count_distinct", "projection", "COUNT(DISTINCT {column_1})", "return distinct unique count", "count_distinct"),
    *(
        _template(f"aggregate.{op}", "aggregate", f"{op.upper()}({{column_1}})", f"calculate {op} over the measured values", op)
        for op in ("count", "sum", "avg", "min", "max")
    ),
    _template("aggregate.count_all", "aggregate", "COUNT(*)", "count all records rows", "count"),
    _template("aggregate.count_distinct", "aggregate", "COUNT(DISTINCT {column_1})", "count distinct unique values", "count_distinct"),
    _template("group.column", "group", "{column_1}", "group records by the requested field"),
    _template("order.desc", "order", "{column_1} DESC", "sort descending highest largest most first", "desc"),
    _template("order.asc", "order", "{column_1} ASC", "sort ascending lowest smallest least first", "asc"),
    _template("limit.rows", "limit", "{value_1}", "limit the number of returned rows", "limit"),
    *(
        _template(f"filter.{name}", "filter", f"{{column_1}} {sql_op} {{value_1}}", meaning, sql_op)
        for name, sql_op, meaning in (
            ("equal", "=", "filter equal matching value"),
            ("not_equal", "!=", "filter not equal excluding value"),
            ("greater", ">", "filter greater above more than value"),
            ("greater_equal", ">=", "filter at least greater or equal value"),
            ("less", "<", "filter less below smaller than value"),
            ("less_equal", "<=", "filter at most less or equal value"),
            ("like", "LIKE", "filter text pattern matching value"),
        )
    ),
    _template("filter.is_null", "filter", "{column_1} IS NULL", "filter missing null value", "IS NULL"),
    _template("filter.not_null", "filter", "{column_1} IS NOT NULL", "filter present non null value", "IS NOT NULL"),
    _template("binding.column", "binding", "{table_1}.{column_1}", "bind an attribute field to its owning table"),
    _template("join.equal", "join", "{column_1} = {column_2}", "join related records using matching keys", "="),
)


# These graph constructs require assembly semantics beyond this catalog's simple
# SELECT contract.  Listing them explicitly prevents accidental generic matches.
UNSUPPORTED_ROLES = frozenset({
    "operand", "numerator", "denominator", "member_of", "scoped_to", "optional",
})
_AGGREGATES = {"count", "sum", "avg", "min", "max"}
_OP_ALIASES = {
    "count": "count", "number": "count", "number of": "count", "how many": "count",
    "sum": "sum", "total": "sum", "total revenue": "sum",
    "avg": "avg", "average": "avg", "mean": "avg",
    "min": "min", "minimum": "min", "max": "max", "maximum": "max",
    "argmax": "argmax", "most": "argmax", "largest": "argmax", "highest": "argmax",
    "argmin": "argmin", "least": "argmin", "smallest": "argmin", "lowest": "argmin",
}
_COMPARISONS = {
    "=": "=", "==": "=", "equal": "=", "equals": "=", "is": "=",
    "!=": "!=", "<>": "!=", "not equal": "!=", "not_equals": "!=",
    ">": ">", "greater": ">", "greater than": ">", "above": ">",
    ">=": ">=", "at least": ">=", "greater_equal": ">=",
    "<": "<", "less": "<", "less than": "<", "below": "<",
    "<=": "<=", "at most": "<=", "less_equal": "<=",
    "like": "LIKE", "is null": "IS NULL", "is not null": "IS NOT NULL",
}


def operation(node: IntentNode) -> str | None:
    """Resolve a declared operation without guessing from unrelated request text."""
    declared = node.attributes.get("operator")
    value = str(declared or node.concept).strip().lower().replace("_", " ")
    return _OP_ALIASES.get(value)


def _comparison(node: IntentNode) -> str | None:
    declared = node.attributes.get("operator")
    return _COMPARISONS.get(str(declared or node.concept).strip().lower())


def _direction(node: IntentNode) -> str | None:
    value = str(node.attributes.get("direction") or "").strip().lower()
    if value in {"asc", "ascending"}:
        return "asc"
    if value in {"desc", "descending"}:
        return "desc"
    op = operation(node)
    return "desc" if op == "argmax" else "asc" if op == "argmin" else None


def _requirements(role: str, source: IntentNode, target: IntentNode) -> tuple[str | None, str | None, str | None]:
    """Return required fragment kind, operator, or an explicit abstention reason."""
    if role in UNSUPPORTED_ROLES:
        return None, None, f"unsupported_relationship: {role} requires a broader assembly contract"
    if role == "returns":
        if target.kind == "operation":
            op = operation(target)
            if op not in _AGGREGATES:
                return None, None, f"unsupported_output_operation: {target.concept}"
            if op == "count" and target.attributes.get("distinct") is True:
                op = "count_distinct"
            return "projection", op, None
        if target.kind == "entity":
            return "projection", "all", None
        return "projection", "distinct" if source.attributes.get("distinct") is True else "column", None
    if role == "attribute":
        return "binding", None, None
    if role in {"source", "target", "joined_by"}:
        return "join", "=", None
    if role == "group_by":
        return "group", None, None
    if role in {"order_by", "tie_breaker"}:
        return "order", _direction(source) or _direction(target), None
    if role == "constrained_by":
        direction = _direction(target)
        if direction:
            return "order", direction, None
        if target.kind == "condition":
            op = _comparison(target)
            return ("filter", op, None) if op else (None, None, f"unsupported_condition: {target.concept}")
        return None, None, f"unsupported_constraint: {target.concept}"
    if role == "measure" and operation(source) in {"argmax", "argmin"}:
        return "limit", "limit", None
    if role in {"theme", "measure"}:
        op = operation(source)
        if op not in _AGGREGATES:
            return None, None, f"unsupported_operation: {source.concept}"
        if op == "count" and source.attributes.get("distinct") is True:
            op = "count_distinct"
        return "aggregate", op, None
    if role in {"compare", "value", "filter"}:
        condition = target if role == "filter" else source
        op = _comparison(condition)
        return ("filter", op, None) if op else (None, None, f"unsupported_condition: {condition.concept}")
    return None, None, f"unsupported_relationship: {role}"


def _compatible(template: FragmentTemplate, kind: str, operator: str | None) -> bool:
    if template.kind != kind:
        return False
    if kind == "projection" and operator in {"column", "all"}:
        return template.fragment_id == f"projection.{operator}"
    return operator is None or template.operator == operator


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def rank_relationships(
    graph: IntentGraph,
    schema: Mapping[str, tuple[str, ...]],
    top_k: int = 3,
) -> dict[str, Any]:
    """Rank distinct portable templates for each edge of a validated graph.

    No request, schema, or result is persisted.  ``coverage.complete`` means that
    this catalog can describe each relationship; it is not a proof of semantic
    correctness or executable SQL.  Graph/schema validation and assembly checks
    remain separate mandatory workflow stages.
    """
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
        raise ValueError("top_k must be an integer between 1 and 10")
    nodes = {node.node_id: node for node in graph.nodes}
    schema_names = set(schema)
    schema_names.update(f"{table}.{column}" for table, columns in schema.items() for column in columns)
    relationships: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for index, edge in enumerate(graph.edges):
        relation = {"relation_id": f"e{index}", "source": edge.source, "role": edge.role, "target": edge.target}
        source, target = nodes.get(edge.source), nodes.get(edge.target)
        reason = None
        candidates: list[dict[str, Any]] = []
        bindings: list[str] = []
        if source is None or target is None:
            reason = "unknown_relationship_endpoint"
        else:
            kind, required_op, reason = _requirements(edge.role, source, target)
            context = _tokens(" ".join((source.concept, edge.role, target.concept, *[span.text for node in (source, target) for span in node.spans])))
            bindings = sorted({candidate for node in (source, target) for candidate in node.schema_candidates if candidate in schema_names})
            for template in CATALOG:
                if kind is None or not _compatible(template, kind, required_op):
                    continue
                words = _tokens(template.semantic_text)
                overlap = len(context & words) / max(len(context | words), 1)
                score = 1.0 + (1.0 if required_op else 0.0) + overlap
                if bindings:
                    score += 0.1
                if template.fragment_id.endswith("count_all"):
                    # A grounded COUNT(column) is the preferred shape; COUNT(*)
                    # remains an explicitly ranked alternative for row counts.
                    score -= 0.05
                candidates.append({
                    "fragment_id": template.fragment_id,
                    "kind": template.kind,
                    "template_sql": template.template_sql,
                    "semantic_text": template.semantic_text,
                    "operator": template.operator,
                    "score": round(score, 6),
                })
            candidates.sort(key=lambda item: (-item["score"], item["fragment_id"]))
            unique: list[dict[str, Any]] = []
            seen: set[tuple[str, str]] = set()
            for candidate in candidates:
                identity = (candidate["kind"], candidate["template_sql"].lower())
                if identity not in seen:
                    candidate["rank"] = len(unique) + 1
                    unique.append(candidate)
                    seen.add(identity)
                if len(unique) == top_k:
                    break
            candidates = unique
        if not candidates:
            missing.append({**relation, "reason": reason or "catalog_has_no_compatible_template"})
        relationships.append({
            **relation,
            "schema_bindings": bindings,
            "candidates": candidates,
            "selected_fragment_id": candidates[0]["fragment_id"] if candidates else None,
        })
    if not relationships:
        missing.append({"relation_id": "", "source": "", "role": "", "target": "", "reason": "no_relationships"})
    return {
        "ranker": RANKER_VERSION,
        "catalog_version": CATALOG_VERSION,
        "relationships": relationships,
        "coverage": {"complete": not missing, "missing": missing},
    }
