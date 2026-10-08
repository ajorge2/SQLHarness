from __future__ import annotations

import math
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .intent import IntentGraph, IntentNode
from .types import BirdExample


COMPATIBLE_FRAGMENT_KINDS: dict[str, frozenset[str]] = {
    "output": frozenset({"projection"}),
    "relation": frozenset({"join"}),
    "condition": frozenset({"filter", "having"}),
    "logic": frozenset({"filter", "having", "set_operation"}),
    "scope": frozenset({"scope", "group"}),
    "operation": frozenset({"aggregate", "order", "limit", "window", "group"}),
}


@dataclass(frozen=True)
class SQLFragment:
    fragment_id: str
    example_id: str
    db_id: str
    kind: str
    scope_id: str
    concrete_sql: str
    template_sql: str
    semantic_text: str
    tables: tuple[str, ...] = ()
    columns: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IntentFragment:
    node_id: str
    node_kind: str
    text: str


@dataclass(frozen=True)
class RetrievalHit:
    query_node_id: str
    score: float
    fragment: SQLFragment


def build_fragment_corpus(
    examples: Iterable[BirdExample],
    *,
    output_path: str | Path,
) -> dict[str, object]:
    fragments = [
        fragment
        for example in examples
        for fragment in extract_sql_fragments(
            example.gold_sql,
            example_id=example.example_id,
            db_id=example.db_id,
        )
    ]
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps([fragment.to_dict() for fragment in fragments], indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "fragments": len(fragments),
        "examples": len({fragment.example_id for fragment in fragments}),
        "databases": len({fragment.db_id for fragment in fragments}),
        "kinds": dict(sorted(Counter(fragment.kind for fragment in fragments).items())),
        "output": str(target),
    }


def load_fragment_corpus(path: str | Path) -> list[SQLFragment]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        SQLFragment(
            fragment_id=str(item["fragment_id"]),
            example_id=str(item["example_id"]),
            db_id=str(item["db_id"]),
            kind=str(item["kind"]),
            scope_id=str(item["scope_id"]),
            concrete_sql=str(item["concrete_sql"]),
            template_sql=str(item["template_sql"]),
            semantic_text=str(item["semantic_text"]),
            tables=tuple(str(value) for value in item.get("tables", ())),
            columns=tuple(str(value) for value in item.get("columns", ())),
        )
        for item in payload
    ]


def fragment_retrieval_key(fragment: SQLFragment) -> str:
    """Identify one reusable SQL meaning independent of its source example."""

    template = re.sub(r"\s+", " ", fragment.template_sql.strip()).lower()
    return f"{fragment.kind}|{template}"


def unique_retrieval_fragments(fragments: Iterable[SQLFragment]) -> list[SQLFragment]:
    unique: dict[str, SQLFragment] = {}
    for fragment in fragments:
        unique.setdefault(fragment_retrieval_key(fragment), fragment)
    return list(unique.values())


def extract_sql_fragments(
    sql: str,
    *,
    example_id: str,
    db_id: str,
    dialect: str = "sqlite",
) -> list[SQLFragment]:
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError as error:
        raise RuntimeError("SQL fragment extraction requires sqlglot") from error

    expression = sqlglot.parse_one(sql, read=dialect)
    fragments: list[SQLFragment] = []
    selects = list(expression.find_all(exp.Select))
    if isinstance(expression, exp.Select):
        selects = [expression, *[item for item in selects if item is not expression]]

    for scope_index, select in enumerate(selects):
        scope_id = f"select_{scope_index}"
        scoped: list[tuple[str, object]] = []
        scoped.extend(("projection", item) for item in select.expressions)
        scoped.extend(
            ("join", join.args["on"])
            for join in select.args.get("joins") or ()
            if join.args.get("on") is not None
        )
        if select.args.get("where") is not None:
            scoped.append(("filter", select.args["where"].this))
        if select.args.get("group") is not None:
            scoped.extend(("group", item) for item in select.args["group"].expressions)
        if select.args.get("having") is not None:
            scoped.append(("having", select.args["having"].this))
        if select.args.get("order") is not None:
            scoped.extend(("order", item) for item in select.args["order"].expressions)
        if select.args.get("limit") is not None:
            scoped.append(("limit", select.args["limit"].expression))

        aggregate_nodes = [
            node
            for node in select.walk()
            if isinstance(node, exp.AggFunc) and _nearest_select(node, exp) is select
        ]
        scoped.extend(("aggregate", item) for item in aggregate_nodes)
        window_nodes = [
            node
            for node in select.walk()
            if isinstance(node, exp.Window) and _nearest_select(node, exp) is select
        ]
        scoped.extend(("window", item) for item in window_nodes)

        for local_index, (kind, fragment_expression) in enumerate(scoped):
            if fragment_expression is None:
                continue
            concrete = fragment_expression.sql(dialect=dialect, pretty=False)
            template = parameterize_sql_expression(fragment_expression, dialect=dialect)
            tables = tuple(
                sorted({table.name for table in fragment_expression.find_all(exp.Table) if table.name})
            )
            columns = tuple(
                sorted({column.sql(dialect=dialect) for column in fragment_expression.find_all(exp.Column)})
            )
            fragments.append(
                SQLFragment(
                    fragment_id=f"{example_id}:{scope_id}:{kind}:{local_index}",
                    example_id=example_id,
                    db_id=db_id,
                    kind=kind,
                    scope_id=scope_id,
                    concrete_sql=concrete,
                    template_sql=template,
                    semantic_text=_semantic_text(kind, concrete, template),
                    tables=tables,
                    columns=columns,
                )
            )

    set_types = tuple(
        item
        for item in (getattr(exp, "Union", None), getattr(exp, "Intersect", None), getattr(exp, "Except", None))
        if item is not None
    )
    for index, node in enumerate(item for item in expression.walk() if isinstance(item, set_types)):
        concrete = node.key.upper()
        fragments.append(
            SQLFragment(
                fragment_id=f"{example_id}:root:set_operation:{index}",
                example_id=example_id,
                db_id=db_id,
                kind="set_operation",
                scope_id="root",
                concrete_sql=concrete,
                template_sql=concrete,
                semantic_text=f"set operation {concrete.lower()}",
            )
        )
    for index, cte in enumerate(expression.find_all(exp.CTE)):
        name = cte.alias_or_name or f"scope_{index}"
        fragments.append(
            SQLFragment(
                fragment_id=f"{example_id}:root:scope:{index}",
                example_id=example_id,
                db_id=db_id,
                kind="scope",
                scope_id="root",
                concrete_sql=name,
                template_sql="{named_scope}",
                semantic_text=f"named intermediate scope {name}",
            )
        )
    return _deduplicate_fragments(fragments)


def parameterize_sql_expression(expression: object, *, dialect: str = "sqlite") -> str:
    try:
        from sqlglot import exp
    except ImportError as error:
        raise RuntimeError("SQL parameterization requires sqlglot") from error
    rendered = expression.sql(dialect=dialect, pretty=False)
    replacements: list[tuple[str, str]] = []
    seen: dict[tuple[str, str], tuple[str, str]] = {}

    def add(category: str, raw: str) -> None:
        key = (category, raw)
        if not raw or key in seen:
            return
        index = sum(1 for item in seen if item[0] == category) + 1
        sentinel = f"§{category[0].upper()}{_alphabetic_index(index)}§"
        placeholder = f"{{{category}_{index}}}"
        seen[key] = (sentinel, placeholder)
        replacements.append((raw, sentinel))

    for column in expression.find_all(exp.Column):
        add("column", column.sql(dialect=dialect))
    for table in expression.find_all(exp.Table):
        add("table", table.sql(dialect=dialect))
    for literal in expression.find_all(exp.Literal):
        add("value", literal.sql(dialect=dialect))
    for raw, placeholder in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        rendered = rendered.replace(raw, placeholder)
    for sentinel, placeholder in seen.values():
        rendered = rendered.replace(sentinel, placeholder)
    return rendered


def serialize_intent_fragments(graph: IntentGraph) -> list[IntentFragment]:
    nodes = {node.node_id: node for node in graph.nodes}
    outgoing: dict[str, list[tuple[str, IntentNode]]] = defaultdict(list)
    incoming: dict[str, list[tuple[str, IntentNode]]] = defaultdict(list)
    for edge in graph.edges:
        if edge.source in nodes and edge.target in nodes:
            outgoing[edge.source].append((edge.role, nodes[edge.target]))
            incoming[edge.target].append((edge.role, nodes[edge.source]))

    root_kinds = {"operation", "condition", "logic", "relation", "scope", "output"}
    fragments: list[IntentFragment] = []
    for node in graph.nodes:
        if node.kind not in root_kinds:
            continue
        pieces = [node.kind, node.concept]
        pieces.extend(span.text for span in node.spans)
        pieces.extend(node.schema_candidates)
        for role, neighbor in sorted(outgoing[node.node_id], key=lambda item: (item[0], item[1].node_id)):
            pieces.extend((role, neighbor.concept, *neighbor.schema_candidates))
        for role, neighbor in sorted(incoming[node.node_id], key=lambda item: (item[0], item[1].node_id)):
            pieces.extend((f"incoming {role}", neighbor.concept, *neighbor.schema_candidates))
        fragments.append(
            IntentFragment(
                node_id=node.node_id,
                node_kind=node.kind,
                text=" | ".join(piece for piece in pieces if piece),
            )
        )
    return fragments


class LexicalFragmentRetriever:
    """Transparent retrieval control used before training the embedding model."""

    def __init__(self, fragments: Iterable[SQLFragment]) -> None:
        self._fragments = list(fragments)
        self._documents = [_tokenize(fragment.semantic_text) for fragment in self._fragments]
        self._document_frequency = Counter(
            token for document in self._documents for token in set(document)
        )
        self._average_length = (
            sum(len(document) for document in self._documents) / len(self._documents)
            if self._documents
            else 0.0
        )

    def retrieve(
        self,
        intent_fragments: Iterable[IntentFragment],
        *,
        top_k_per_intent: int = 2,
        max_total: int = 12,
    ) -> list[RetrievalHit]:
        best_by_fragment: dict[str, RetrievalHit] = {}
        for intent in intent_fragments:
            scored = [
                (
                    self._score(_tokenize(intent.text), document)
                    + _kind_prior(intent.node_kind, fragment.kind),
                    fragment,
                )
                for fragment, document in zip(self._fragments, self._documents, strict=True)
            ]
            for score, fragment in sorted(scored, key=lambda item: item[0], reverse=True)[
                :top_k_per_intent
            ]:
                hit = RetrievalHit(intent.node_id, round(score, 6), fragment)
                key = fragment_retrieval_key(fragment)
                current = best_by_fragment.get(key)
                if current is None or hit.score > current.score:
                    best_by_fragment[key] = hit
        return sorted(best_by_fragment.values(), key=lambda item: item.score, reverse=True)[:max_total]

    def _score(self, query: list[str], document: list[str]) -> float:
        if not query or not document or not self._fragments:
            return 0.0
        counts = Counter(document)
        score = 0.0
        k1 = 1.5
        b = 0.75
        for token in set(query):
            frequency = counts[token]
            if not frequency:
                continue
            document_frequency = self._document_frequency[token]
            inverse_document_frequency = math.log(
                1 + (len(self._documents) - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            denominator = frequency + k1 * (
                1 - b + b * len(document) / max(self._average_length, 1)
            )
            score += inverse_document_frequency * frequency * (k1 + 1) / denominator
        return score


class FastEmbedFragmentRetriever:
    """Dense semantic retrieval backed by a local ONNX embedding model."""

    def __init__(
        self,
        fragments: Iterable[SQLFragment],
        *,
        model_name: str = "BAAI/bge-small-en-v1.5",
        cache_dir: str | Path | None = None,
        threads: int | None = None,
        encoder: Any | None = None,
    ) -> None:
        self._fragments = list(fragments)
        if encoder is None:
            try:
                from fastembed import TextEmbedding
            except ImportError as error:
                raise RuntimeError(
                    "Dense retrieval requires the retrieval extra: uv sync --extra retrieval"
                ) from error
            encoder = TextEmbedding(
                model_name=model_name,
                cache_dir=str(cache_dir) if cache_dir is not None else None,
                threads=threads,
            )
        self._encoder = encoder
        passage_texts = [fragment.semantic_text for fragment in self._fragments]
        self._document_vectors = [
            _normalize_vector(vector)
            for vector in self._encoder.passage_embed(passage_texts)
        ]

    def retrieve(
        self,
        intent_fragments: Iterable[IntentFragment],
        *,
        top_k_per_intent: int = 2,
        max_total: int = 12,
    ) -> list[RetrievalHit]:
        intents = list(intent_fragments)
        if not intents or not self._fragments:
            return []
        query_vectors = [
            _normalize_vector(vector)
            for vector in self._encoder.query_embed([intent.text for intent in intents])
        ]
        best_by_fragment: dict[str, RetrievalHit] = {}
        for intent, query_vector in zip(intents, query_vectors, strict=True):
            scored = [
                (_dot_product(query_vector, document_vector), fragment)
                for fragment, document_vector in zip(
                    self._fragments, self._document_vectors, strict=True
                )
            ]
            for score, fragment in sorted(scored, key=lambda item: item[0], reverse=True)[
                :top_k_per_intent
            ]:
                hit = RetrievalHit(intent.node_id, round(score, 6), fragment)
                key = fragment_retrieval_key(fragment)
                current = best_by_fragment.get(key)
                if current is None or hit.score > current.score:
                    best_by_fragment[key] = hit
        return sorted(best_by_fragment.values(), key=lambda item: item.score, reverse=True)[:max_total]


def _nearest_select(node: object, exp: object) -> object | None:
    current = getattr(node, "parent", None)
    while current is not None:
        if isinstance(current, exp.Select):
            return current
        current = getattr(current, "parent", None)
    return None


def _semantic_text(kind: str, concrete: str, template: str) -> str:
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", f"{kind} {concrete} {template}")
    return re.sub(r"[^a-zA-Z0-9{}]+", " ", words).lower().strip()


def _tokenize(text: str) -> list[str]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text).replace("_", " ")
    return re.findall(r"[a-z0-9]+", expanded.lower())


def _kind_prior(node_kind: str, fragment_kind: str) -> float:
    return 1.5 if fragment_kind in COMPATIBLE_FRAGMENT_KINDS.get(node_kind, ()) else 0.0


def fragment_kind_compatible(node_kind: str, fragment_kind: str) -> bool:
    return fragment_kind in COMPATIBLE_FRAGMENT_KINDS.get(node_kind, ())


def _alphabetic_index(index: int) -> str:
    letters = ""
    value = index
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def _normalize_vector(vector: Iterable[float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in vector)
    magnitude = math.sqrt(sum(value * value for value in values))
    if magnitude == 0:
        return values
    return tuple(value / magnitude for value in values)


def _dot_product(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimension")
    return sum(first * second for first, second in zip(left, right, strict=True))


def _deduplicate_fragments(fragments: list[SQLFragment]) -> list[SQLFragment]:
    result: list[SQLFragment] = []
    seen: set[tuple[str, str, str]] = set()
    for fragment in fragments:
        key = (fragment.scope_id, fragment.kind, fragment.concrete_sql)
        if key in seen:
            continue
        seen.add(key)
        result.append(fragment)
    return result
