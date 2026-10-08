from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Protocol

from .fragments import (
    IntentFragment,
    LexicalFragmentRetriever,
    RetrievalHit,
    SQLFragment,
    extract_sql_fragments,
    fragment_retrieval_key,
    serialize_intent_fragments,
)
from .intent import IntentGraph, repair_unique_source_spans, validate_intent_graph
from .types import BirdExample


class FragmentRetriever(Protocol):
    def retrieve(
        self,
        intent_fragments: Iterable[IntentFragment],
        *,
        top_k_per_intent: int = 2,
        max_total: int = 12,
    ) -> list[RetrievalHit]: ...


def fragment_signature(fragment: SQLFragment) -> str:
    """Return a schema-independent structural identity for a SQL fragment."""

    return fragment_retrieval_key(fragment)


def evaluate_fragment_retrieval(
    examples: Iterable[BirdExample],
    *,
    graph_records: dict[str, dict[str, Any]],
    corpus: list[SQLFragment],
    output_path: str | Path,
    recall_at: tuple[int, ...] = (1, 3, 5, 10, 12),
    top_k_per_intent: int = 2,
    retriever: FragmentRetriever | None = None,
    retriever_name: str = "lexical-bm25-control",
) -> dict[str, Any]:
    """Measure whether graph-conditioned retrieval surfaces gold SQL structures.

    Gold relevance is derived from parameterized fragments in each held-out gold
    query. This intentionally evaluates structural candidate coverage, not whether
    a retrieved fragment is aligned to the exact intent node that should use it.
    """

    selected = list(examples)
    ks = tuple(sorted({value for value in recall_at if value > 0}))
    if not ks:
        raise ValueError("recall_at must contain at least one positive cutoff")

    corpus_signatures = {fragment_signature(fragment) for fragment in corpus}
    corpus_kinds = {fragment.kind for fragment in corpus}
    active_retriever = retriever or LexicalFragmentRetriever(corpus)
    records: list[dict[str, Any]] = []

    for example in selected:
        gold_fragments = extract_sql_fragments(
            example.gold_sql,
            example_id=example.example_id,
            db_id=example.db_id,
        )
        gold_by_signature = _representative_fragments(gold_fragments)
        gold_signatures = set(gold_by_signature)
        gold_kinds = {fragment.kind for fragment in gold_fragments}
        catalog_signatures = gold_signatures & corpus_signatures
        catalog_kinds = gold_kinds & corpus_kinds

        record: dict[str, Any] = {
            "example_id": example.example_id,
            "db_id": example.db_id,
            "gold_signatures": sorted(gold_signatures),
            "gold_kinds": sorted(gold_kinds),
            "catalog_covered_signatures": sorted(catalog_signatures),
            "catalog_covered_kinds": sorted(catalog_kinds),
            "catalog_signature_coverage": _ratio(len(catalog_signatures), len(gold_signatures)),
            "catalog_kind_coverage": _ratio(len(catalog_kinds), len(gold_kinds)),
            "graph_available": False,
            "graph_valid": False,
            "recall": {},
        }

        graph_record = graph_records.get(example.example_id)
        if not graph_record or not graph_record.get("graph"):
            record["failure_stage"] = "intent_graph_unavailable"
            records.append(record)
            continue

        graph, _ = repair_unique_source_spans(IntentGraph.from_dict(graph_record["graph"]))
        graph_validation = validate_intent_graph(graph)
        record["graph_available"] = True
        record["graph_valid"] = graph_validation.valid
        if not graph_validation.valid:
            record["failure_stage"] = "intent_graph_invalid"
            record["graph_errors"] = list(graph_validation.errors)
            records.append(record)
            continue

        intent_fragments = serialize_intent_fragments(graph)
        hits = active_retriever.retrieve(
            intent_fragments,
            top_k_per_intent=top_k_per_intent,
            max_total=max(ks),
        )
        record["intent_fragments"] = [_intent_to_dict(item) for item in intent_fragments]
        record["retrieval_hits"] = [_hit_to_dict(hit) for hit in hits]
        record["first_relevant_rank"] = next(
            (
                index
                for index, hit in enumerate(hits, start=1)
                if fragment_signature(hit.fragment) in catalog_signatures
            ),
            None,
        )
        for cutoff in ks:
            top_hits = hits[:cutoff]
            retrieved_signatures = {fragment_signature(hit.fragment) for hit in top_hits}
            retrieved_kinds = {hit.fragment.kind for hit in top_hits}
            matched_signatures = gold_signatures & retrieved_signatures
            matched_kinds = gold_kinds & retrieved_kinds
            record["recall"][str(cutoff)] = {
                "retrieved": len(top_hits),
                "matched_signatures": sorted(matched_signatures),
                "signature_recall": _ratio(len(matched_signatures), len(gold_signatures)),
                "catalog_conditional_signature_recall": _ratio(
                    len(matched_signatures), len(catalog_signatures)
                ),
                "matched_kinds": sorted(matched_kinds),
                "kind_recall": _ratio(len(matched_kinds), len(gold_kinds)),
                "catalog_conditional_kind_recall": _ratio(
                    len(matched_kinds), len(catalog_kinds)
                ),
            }
        records.append(record)

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = _summarize(records, ks, corpus, retriever_name=retriever_name)
    target.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _summarize(
    records: list[dict[str, Any]],
    ks: tuple[int, ...],
    corpus: list[SQLFragment],
    *,
    retriever_name: str,
) -> dict[str, Any]:
    evaluable = [record for record in records if record["graph_valid"]]
    total_gold_signatures = sum(len(record["gold_signatures"]) for record in records)
    total_catalog_signatures = sum(len(record["catalog_covered_signatures"]) for record in records)
    total_gold_kinds = sum(len(record["gold_kinds"]) for record in records)
    total_catalog_kinds = sum(len(record["catalog_covered_kinds"]) for record in records)
    evaluable_gold_signatures = sum(len(record["gold_signatures"]) for record in evaluable)
    evaluable_catalog_signatures = sum(
        len(record["catalog_covered_signatures"]) for record in evaluable
    )
    evaluable_gold_kinds = sum(len(record["gold_kinds"]) for record in evaluable)
    evaluable_catalog_kinds = sum(
        len(record["catalog_covered_kinds"]) for record in evaluable
    )
    retrieval_eligible = [
        record for record in evaluable if record["catalog_covered_signatures"]
    ]
    metrics: dict[str, Any] = {}
    for cutoff in ks:
        cutoff_key = str(cutoff)
        matched_signatures = sum(
            len(record["recall"][cutoff_key]["matched_signatures"]) for record in evaluable
        )
        matched_kinds = sum(
            len(record["recall"][cutoff_key]["matched_kinds"]) for record in evaluable
        )
        metrics[cutoff_key] = {
            "micro_signature_recall": _ratio(matched_signatures, evaluable_gold_signatures),
            "catalog_conditional_micro_signature_recall": _ratio(
                matched_signatures, evaluable_catalog_signatures
            ),
            "macro_signature_recall": _mean(
                record["recall"][cutoff_key]["signature_recall"] for record in evaluable
            ),
            "micro_kind_recall": _ratio(matched_kinds, evaluable_gold_kinds),
            "catalog_conditional_micro_kind_recall": _ratio(
                matched_kinds, evaluable_catalog_kinds
            ),
            "eligible_query_hit_rate": _mean(
                1.0
                if record.get("first_relevant_rank") is not None
                and int(record["first_relevant_rank"]) <= cutoff
                else 0.0
                for record in retrieval_eligible
            ),
        }

    return {
        "examples": len(records),
        "graphs_evaluable": len(evaluable),
        "graph_coverage": _ratio(len(evaluable), len(records)),
        "corpus_fragments": len(corpus),
        "corpus_examples": len({fragment.example_id for fragment in corpus}),
        "retriever": retriever_name,
        "gold_signatures": total_gold_signatures,
        "catalog_covered_gold_signatures": total_catalog_signatures,
        "catalog_signature_coverage": _ratio(total_catalog_signatures, total_gold_signatures),
        "evaluable_gold_signatures": evaluable_gold_signatures,
        "evaluable_catalog_covered_gold_signatures": evaluable_catalog_signatures,
        "evaluable_catalog_signature_coverage": _ratio(
            evaluable_catalog_signatures, evaluable_gold_signatures
        ),
        "gold_kinds": total_gold_kinds,
        "catalog_covered_gold_kinds": total_catalog_kinds,
        "catalog_kind_coverage": _ratio(total_catalog_kinds, total_gold_kinds),
        "evaluable_gold_kinds": evaluable_gold_kinds,
        "evaluable_catalog_covered_gold_kinds": evaluable_catalog_kinds,
        "evaluable_catalog_kind_coverage": _ratio(
            evaluable_catalog_kinds, evaluable_gold_kinds
        ),
        "retrieval_eligible_queries": len(retrieval_eligible),
        "mean_reciprocal_rank": _mean(
            1.0 / int(record["first_relevant_rank"])
            if record.get("first_relevant_rank") is not None
            else 0.0
            for record in retrieval_eligible
        ),
        "recall_at": metrics,
        "relevance_definition": (
            "A retrieved fragment is strictly relevant when its kind and parameterized SQL "
            "template exactly match a structural fragment extracted from the held-out gold SQL."
        ),
        "scope_disclosure": (
            "This measures pooled structural candidate coverage. It does not yet score exact "
            "intent-node-to-gold-fragment alignment or final SQL correctness."
        ),
        "development_only": True,
    }


def _representative_fragments(fragments: Iterable[SQLFragment]) -> dict[str, SQLFragment]:
    representatives: dict[str, SQLFragment] = {}
    for fragment in fragments:
        representatives.setdefault(fragment_signature(fragment), fragment)
    return representatives


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _mean(values: Iterable[float | None]) -> float | None:
    observed = [value for value in values if value is not None]
    return sum(observed) / len(observed) if observed else None


def _intent_to_dict(fragment: IntentFragment) -> dict[str, str]:
    return {
        "node_id": fragment.node_id,
        "node_kind": fragment.node_kind,
        "text": fragment.text,
    }


def _hit_to_dict(hit: RetrievalHit) -> dict[str, Any]:
    return {
        "query_node_id": hit.query_node_id,
        "score": hit.score,
        "signature": fragment_signature(hit.fragment),
        "fragment": hit.fragment.to_dict(),
    }
