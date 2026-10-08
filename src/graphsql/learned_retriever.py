from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .fragments import (
    IntentFragment,
    RetrievalHit,
    SQLFragment,
    _dot_product,
    _normalize_vector,
    _tokenize,
    extract_sql_fragments,
    fragment_kind_compatible,
    fragment_retrieval_key,
    serialize_intent_fragments,
)
from .intent import IntentGraph, repair_unique_source_spans, validate_intent_graph
from .retrieval_evaluation import fragment_signature
from .types import BirdExample


FEATURE_NAMES = (
    "dense_cosine",
    "token_jaccard",
    "operator_jaccard",
    "kind_compatible",
)
SQL_OPERATOR_TOKENS = frozenset(
    {
        "aggregate",
        "avg",
        "average",
        "between",
        "count",
        "distinct",
        "except",
        "filter",
        "group",
        "having",
        "highest",
        "join",
        "limit",
        "lowest",
        "max",
        "maximum",
        "min",
        "minimum",
        "order",
        "percentage",
        "projection",
        "rank",
        "ratio",
        "sum",
        "total",
        "union",
        "window",
    }
)


@dataclass(frozen=True)
class LinearRankerModel:
    model_version: int
    embedding_model: str
    feature_names: tuple[str, ...]
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    weights: tuple[float, ...]
    bias: float
    training_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LinearRankerModel:
        return cls(
            model_version=int(payload["model_version"]),
            embedding_model=str(payload["embedding_model"]),
            feature_names=tuple(str(value) for value in payload["feature_names"]),
            feature_means=tuple(float(value) for value in payload["feature_means"]),
            feature_scales=tuple(float(value) for value in payload["feature_scales"]),
            weights=tuple(float(value) for value in payload["weights"]),
            bias=float(payload["bias"]),
            training_summary=dict(payload.get("training_summary", {})),
        )

    @classmethod
    def load(cls, path: str | Path) -> LinearRankerModel:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def train_fragment_ranker(
    examples: Iterable[BirdExample],
    *,
    graph_records: dict[str, dict[str, Any]],
    corpus: list[SQLFragment],
    output_path: str | Path,
    embedding_model: str = "BAAI/bge-small-en-v1.5",
    cache_dir: str | Path | None = None,
    encoder: Any | None = None,
    epochs: int = 500,
    learning_rate: float = 0.08,
    l2: float = 0.01,
) -> dict[str, Any]:
    selected_examples = list(examples)
    active_encoder = encoder or _load_encoder(embedding_model, cache_dir)
    document_vectors = [
        _normalize_vector(vector)
        for vector in active_encoder.passage_embed(
            [fragment.semantic_text for fragment in corpus]
        )
    ]
    rows: list[tuple[tuple[float, ...], int]] = []
    used_examples = 0
    used_intents = 0
    skipped_examples: list[str] = []

    for example in selected_examples:
        graph_record = graph_records.get(example.example_id)
        if not graph_record or not graph_record.get("graph"):
            skipped_examples.append(example.example_id)
            continue
        graph, _ = repair_unique_source_spans(IntentGraph.from_dict(graph_record["graph"]))
        if not validate_intent_graph(graph).valid:
            skipped_examples.append(example.example_id)
            continue
        intent_fragments = serialize_intent_fragments(graph)
        if not intent_fragments:
            skipped_examples.append(example.example_id)
            continue
        query_vectors = [
            _normalize_vector(vector)
            for vector in active_encoder.query_embed([item.text for item in intent_fragments])
        ]
        gold_signatures = {
            fragment_signature(fragment)
            for fragment in extract_sql_fragments(
                example.gold_sql,
                example_id=example.example_id,
                db_id=example.db_id,
            )
        }
        for intent, query_vector in zip(intent_fragments, query_vectors, strict=True):
            positive_rows: list[tuple[tuple[float, ...], int]] = []
            negative_rows: list[tuple[tuple[float, ...], int]] = []
            for fragment, document_vector in zip(corpus, document_vectors, strict=True):
                features = _pair_features(intent, fragment, query_vector, document_vector)
                label = int(
                    fragment_signature(fragment) in gold_signatures
                    and fragment_kind_compatible(intent.node_kind, fragment.kind)
                )
                (positive_rows if label else negative_rows).append((features, label))
            if not positive_rows:
                continue
            rows.extend(positive_rows)
            rows.extend(_hard_negative_sample(negative_rows, positive_rows, limit_multiplier=8))
            used_intents += 1
        used_examples += 1

    if not rows or not any(label for _, label in rows):
        raise ValueError("No positive intent-to-fragment training pairs were produced")

    raw_features = [features for features, _ in rows]
    labels = [label for _, label in rows]
    means, scales = _fit_scaler(raw_features)
    standardized = [_standardize(features, means, scales) for features in raw_features]
    weights, bias, final_loss = _fit_logistic_regression(
        standardized,
        labels,
        epochs=epochs,
        learning_rate=learning_rate,
        l2=l2,
    )
    training_summary = {
        "examples_requested": len(selected_examples),
        "examples_used": used_examples,
        "skipped_example_ids": sorted(set(skipped_examples)),
        "intent_fragments_with_positives": used_intents,
        "training_pairs": len(rows),
        "positive_pairs": sum(labels),
        "negative_pairs": len(labels) - sum(labels),
        "final_weighted_log_loss": final_loss,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "l2": l2,
        "label_definition": (
            "Positive when a corpus fragment exactly matches a gold SQL signature and its "
            "fragment kind is compatible with the intent-node kind."
        ),
    }
    model = LinearRankerModel(
        model_version=1,
        embedding_model=embedding_model,
        feature_names=FEATURE_NAMES,
        feature_means=means,
        feature_scales=scales,
        weights=weights,
        bias=bias,
        training_summary=training_summary,
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(model.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**training_summary, "weights": dict(zip(FEATURE_NAMES, weights, strict=True)), "bias": bias}


class LearnedFragmentRetriever:
    """Task-specific linear reranker over dense and structural pair features."""

    def __init__(
        self,
        fragments: Iterable[SQLFragment],
        *,
        model: LinearRankerModel,
        cache_dir: str | Path | None = None,
        encoder: Any | None = None,
    ) -> None:
        self._fragments = list(fragments)
        self._model = model
        self._encoder = encoder or _load_encoder(model.embedding_model, cache_dir)
        self._document_vectors = [
            _normalize_vector(vector)
            for vector in self._encoder.passage_embed(
                [fragment.semantic_text for fragment in self._fragments]
            )
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
            scored: list[tuple[float, SQLFragment]] = []
            for fragment, document_vector in zip(
                self._fragments, self._document_vectors, strict=True
            ):
                raw = _pair_features(intent, fragment, query_vector, document_vector)
                features = _standardize(
                    raw,
                    self._model.feature_means,
                    self._model.feature_scales,
                )
                score = self._model.bias + _dot_product(features, self._model.weights)
                scored.append((score, fragment))
            for score, fragment in sorted(scored, key=lambda item: item[0], reverse=True)[
                :top_k_per_intent
            ]:
                hit = RetrievalHit(intent.node_id, round(score, 6), fragment)
                key = fragment_retrieval_key(fragment)
                current = best_by_fragment.get(key)
                if current is None or hit.score > current.score:
                    best_by_fragment[key] = hit
        return sorted(best_by_fragment.values(), key=lambda item: item.score, reverse=True)[:max_total]


def _load_encoder(model_name: str, cache_dir: str | Path | None) -> Any:
    try:
        from fastembed import TextEmbedding
    except ImportError as error:
        raise RuntimeError(
            "Learned retrieval requires the retrieval extra: uv sync --extra retrieval"
        ) from error
    return TextEmbedding(
        model_name=model_name,
        cache_dir=str(cache_dir) if cache_dir is not None else None,
    )


def _pair_features(
    intent: IntentFragment,
    fragment: SQLFragment,
    query_vector: tuple[float, ...],
    document_vector: tuple[float, ...],
) -> tuple[float, ...]:
    query_tokens = set(_tokenize(intent.text))
    document_tokens = set(_tokenize(fragment.semantic_text))
    operators_left = query_tokens & SQL_OPERATOR_TOKENS
    operators_right = document_tokens & SQL_OPERATOR_TOKENS
    return (
        _dot_product(query_vector, document_vector),
        _jaccard(query_tokens, document_tokens),
        _jaccard(operators_left, operators_right),
        float(fragment_kind_compatible(intent.node_kind, fragment.kind)),
    )


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _hard_negative_sample(
    negatives: list[tuple[tuple[float, ...], int]],
    positives: list[tuple[tuple[float, ...], int]],
    *,
    limit_multiplier: int,
) -> list[tuple[tuple[float, ...], int]]:
    limit = max(len(positives) * limit_multiplier, 1)
    return sorted(
        negatives,
        key=lambda row: (row[0][0] + row[0][1] + row[0][2] + row[0][3]),
        reverse=True,
    )[:limit]


def _fit_scaler(rows: list[tuple[float, ...]]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    width = len(rows[0])
    means = tuple(sum(row[index] for row in rows) / len(rows) for index in range(width))
    scales = tuple(
        max(
            math.sqrt(
                sum((row[index] - means[index]) ** 2 for row in rows) / len(rows)
            ),
            1e-8,
        )
        for index in range(width)
    )
    return means, scales


def _standardize(
    row: tuple[float, ...],
    means: tuple[float, ...],
    scales: tuple[float, ...],
) -> tuple[float, ...]:
    return tuple(
        (value - mean) / scale
        for value, mean, scale in zip(row, means, scales, strict=True)
    )


def _fit_logistic_regression(
    rows: list[tuple[float, ...]],
    labels: list[int],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[tuple[float, ...], float, float]:
    width = len(rows[0])
    weights = [0.0] * width
    bias = 0.0
    positives = sum(labels)
    negatives = len(labels) - positives
    positive_weight = negatives / max(positives, 1)
    normalizer = negatives + positive_weight * positives

    for _ in range(epochs):
        gradients = [0.0] * width
        bias_gradient = 0.0
        for row, label in zip(rows, labels, strict=True):
            prediction = _sigmoid(bias + sum(w * x for w, x in zip(weights, row, strict=True)))
            sample_weight = positive_weight if label else 1.0
            error = sample_weight * (prediction - label)
            bias_gradient += error
            for index, value in enumerate(row):
                gradients[index] += error * value
        bias -= learning_rate * bias_gradient / normalizer
        for index in range(width):
            regularized = gradients[index] / normalizer + l2 * weights[index]
            weights[index] -= learning_rate * regularized

    loss = 0.0
    for row, label in zip(rows, labels, strict=True):
        prediction = min(
            max(_sigmoid(bias + sum(w * x for w, x in zip(weights, row, strict=True))), 1e-12),
            1 - 1e-12,
        )
        sample_weight = positive_weight if label else 1.0
        loss -= sample_weight * (
            label * math.log(prediction) + (1 - label) * math.log(1 - prediction)
        )
    loss = loss / normalizer + 0.5 * l2 * sum(weight * weight for weight in weights)
    return tuple(weights), bias, loss


def _sigmoid(value: float) -> float:
    if value >= 0:
        exponent = math.exp(-value)
        return 1.0 / (1.0 + exponent)
    exponent = math.exp(value)
    return exponent / (1.0 + exponent)
