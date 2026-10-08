from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable, Mapping


GRAPH_VERSION = "0.2"
NODE_KINDS = frozenset(
    {
        "entity",
        "attribute",
        "value",
        "operation",
        "condition",
        "logic",
        "relation",
        "scope",
        "output",
    }
)
SPAN_SOURCES = frozenset({"request", "evidence"})
EDGE_ROLES = frozenset(
    {
        "theme",
        "attribute",
        "value",
        "source",
        "target",
        "group_by",
        "filter",
        "compare",
        "measure",
        "order_by",
        "constrained_by",
        "returns",
        "operand",
        "numerator",
        "denominator",
        "member_of",
        "joined_by",
        "scoped_to",
        "optional",
        "tie_breaker",
    }
)

ROLE_SIGNATURES: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "attribute": (frozenset({"entity", "relation"}), frozenset({"attribute"})),
    "value": (frozenset({"condition"}), frozenset({"value"})),
    "source": (frozenset({"relation"}), frozenset({"entity"})),
    "target": (frozenset({"relation"}), frozenset({"entity"})),
    "group_by": (frozenset({"operation"}), frozenset({"attribute", "entity"})),
    "filter": (
        frozenset({"entity", "scope", "output", "operation"}),
        frozenset({"condition", "logic"}),
    ),
    "compare": (frozenset({"condition"}), frozenset({"attribute", "operation"})),
    "measure": (frozenset({"operation"}), frozenset({"attribute", "operation"})),
    "order_by": (
        frozenset({"operation", "output", "scope"}),
        frozenset({"attribute", "operation"}),
    ),
    "returns": (
        frozenset({"output"}),
        frozenset({"attribute", "entity", "operation"}),
    ),
    "operand": (frozenset({"logic"}), frozenset({"condition", "logic"})),
    "numerator": (
        frozenset({"operation"}),
        frozenset({"operation", "entity", "scope", "condition"}),
    ),
    "denominator": (
        frozenset({"operation"}),
        frozenset({"operation", "entity", "scope", "condition"}),
    ),
    "joined_by": (
        frozenset({"entity", "scope", "output", "operation"}),
        frozenset({"relation"}),
    ),
    "scoped_to": (
        frozenset({"output", "operation", "condition", "scope"}),
        frozenset({"scope"}),
    ),
    "optional": (
        frozenset({"output", "operation"}),
        frozenset({"attribute", "entity", "operation"}),
    ),
    "tie_breaker": (
        frozenset({"operation"}),
        frozenset({"attribute", "operation"}),
    ),
}


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int
    text: str
    source: str = "request"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SourceSpan:
        return cls(
            start=int(payload["start"]),
            end=int(payload["end"]),
            text=str(payload["text"]),
            source=str(payload.get("source", "request")),
        )


@dataclass(frozen=True)
class IntentNode:
    node_id: str
    kind: str
    concept: str
    spans: tuple[SourceSpan, ...] = ()
    schema_candidates: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> IntentNode:
        return cls(
            node_id=str(payload["node_id"]),
            kind=str(payload["kind"]),
            concept=str(payload["concept"]),
            spans=tuple(SourceSpan.from_dict(span) for span in payload.get("spans", ())),
            schema_candidates=tuple(str(item) for item in payload.get("schema_candidates", ())),
            attributes=dict(payload.get("attributes", {})),
        )


@dataclass(frozen=True)
class IntentEdge:
    source: str
    role: str
    target: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> IntentEdge:
        return cls(source=str(payload["source"]), role=str(payload["role"]), target=str(payload["target"]))


@dataclass(frozen=True)
class IntentGraph:
    request: str
    nodes: tuple[IntentNode, ...]
    edges: tuple[IntentEdge, ...]
    evidence: str = ""
    graph_version: str = GRAPH_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> IntentGraph:
        return cls(
            request=str(payload["request"]),
            nodes=tuple(IntentNode.from_dict(node) for node in payload.get("nodes", ())),
            edges=tuple(IntentEdge.from_dict(edge) for edge in payload.get("edges", ())),
            evidence=str(payload.get("evidence", "")),
            graph_version=str(payload.get("graph_version", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntentGraphValidation:
    valid: bool
    errors: tuple[str, ...] = ()


def validate_intent_graph(graph: IntentGraph) -> IntentGraphValidation:
    errors: list[str] = []
    if graph.graph_version != GRAPH_VERSION:
        errors.append(f"unsupported_graph_version: {graph.graph_version!r}")
    if not graph.request.strip():
        errors.append("empty_request")
    if not graph.nodes:
        errors.append("empty_nodes")

    node_ids = [node.node_id for node in graph.nodes]
    duplicate_ids = sorted({node_id for node_id in node_ids if node_ids.count(node_id) > 1})
    if duplicate_ids:
        errors.append(f"duplicate_node_ids: {', '.join(duplicate_ids)}")
    known_ids = set(node_ids)
    node_kinds = {node.node_id: node.kind for node in graph.nodes}

    for node in graph.nodes:
        if not node.node_id.strip():
            errors.append("empty_node_id")
        if node.kind not in NODE_KINDS:
            errors.append(f"unknown_node_kind: {node.node_id}={node.kind}")
        if not node.concept.strip():
            errors.append(f"empty_concept: {node.node_id}")
        for span in node.spans:
            if span.source not in SPAN_SOURCES:
                errors.append(f"unknown_span_source: {node.node_id}={span.source}")
                continue
            source_text = graph.request if span.source == "request" else graph.evidence
            if span.start < 0 or span.end <= span.start or span.end > len(source_text):
                errors.append(f"invalid_span_bounds: {node.node_id}[{span.start}:{span.end}]")
                continue
            observed = source_text[span.start : span.end]
            if observed != span.text:
                errors.append(
                    f"span_text_mismatch: {node.node_id}[{span.start}:{span.end}] "
                    f"expected={observed!r} found={span.text!r}"
                )
        if (
            not node.spans
            and node.kind not in {"output", "scope"}
            and node.attributes.get("inferred") is not True
        ):
            errors.append(f"ungrounded_node_without_inferred_marker: {node.node_id}")

    output_nodes = [node for node in graph.nodes if node.kind == "output"]
    if graph.nodes and not output_nodes:
        errors.append("missing_output_node")
    if len(output_nodes) > 1:
        errors.append("multiple_output_nodes")

    edge_keys: list[tuple[str, str, str]] = []
    for edge in graph.edges:
        edge_keys.append((edge.source, edge.role, edge.target))
        if edge.source not in known_ids:
            errors.append(f"unknown_edge_source: {edge.source}")
        if edge.target not in known_ids:
            errors.append(f"unknown_edge_target: {edge.target}")
        if edge.source == edge.target:
            errors.append(f"self_edge: {edge.source}")
        if edge.role not in EDGE_ROLES:
            errors.append(f"unknown_edge_role: {edge.role}")
        elif edge.source in node_kinds and edge.target in node_kinds:
            signature = ROLE_SIGNATURES.get(edge.role)
            if signature is not None:
                source_kinds, target_kinds = signature
                if (
                    node_kinds[edge.source] not in source_kinds
                    or node_kinds[edge.target] not in target_kinds
                ):
                    errors.append(
                        "invalid_edge_signature: "
                        f"{edge.source}({node_kinds[edge.source]})-"
                        f"{edge.role}->{edge.target}({node_kinds[edge.target]})"
                    )

    duplicate_edges = sorted({edge for edge in edge_keys if edge_keys.count(edge) > 1})
    if duplicate_edges:
        errors.append(f"duplicate_edges: {duplicate_edges!r}")

    if not _is_acyclic(known_ids, graph.edges):
        errors.append("cyclic_graph")
    if output_nodes and not _is_weakly_connected(known_ids, graph.edges, output_nodes[0].node_id):
        errors.append("disconnected_graph")

    return IntentGraphValidation(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def repair_unique_source_spans(graph: IntentGraph) -> tuple[IntentGraph, tuple[str, ...]]:
    """Repair incorrect offsets only when the claimed text occurs exactly once.

    This preserves the model's semantic claim while making a deterministic offset
    correction. Ambiguous or nonexistent text is never guessed.
    """
    repairs: list[str] = []
    repaired_nodes: list[IntentNode] = []
    for node in graph.nodes:
        repaired_spans: list[SourceSpan] = []
        for span in node.spans:
            source_text = graph.request if span.source == "request" else graph.evidence
            observed = (
                source_text[span.start : span.end]
                if 0 <= span.start < span.end <= len(source_text)
                else None
            )
            if observed == span.text:
                repaired_spans.append(span)
                continue
            starts: list[int] = []
            cursor = source_text.find(span.text)
            while cursor >= 0:
                starts.append(cursor)
                cursor = source_text.find(span.text, cursor + 1)
            if len(starts) == 1:
                start = starts[0]
                repaired_spans.append(
                    SourceSpan(
                        source=span.source,
                        start=start,
                        end=start + len(span.text),
                        text=span.text,
                    )
                )
                repairs.append(
                    f"{node.node_id}:{span.source}[{span.start}:{span.end}]"
                    f"->[{start}:{start + len(span.text)}]"
                )
            else:
                repaired_spans.append(span)
        repaired_nodes.append(replace(node, spans=tuple(repaired_spans)))
    return replace(graph, nodes=tuple(repaired_nodes)), tuple(repairs)


def _is_acyclic(node_ids: set[str], edges: Iterable[IntentEdge]) -> bool:
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].append(edge.target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return False
        if node_id in visited:
            return True
        visiting.add(node_id)
        if not all(visit(target) for target in adjacency[node_id]):
            return False
        visiting.remove(node_id)
        visited.add(node_id)
        return True

    return all(visit(node_id) for node_id in node_ids)


def _is_weakly_connected(
    node_ids: set[str], edges: Iterable[IntentEdge], start_node_id: str
) -> bool:
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
    reachable: set[str] = set()
    frontier = [start_node_id]
    while frontier:
        node_id = frontier.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        frontier.extend(adjacency[node_id] - reachable)
    return reachable == node_ids
