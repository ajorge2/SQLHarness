from __future__ import annotations

import json

import pytest

pytest.importorskip("sqlglot")

from graphsql.fragments import extract_sql_fragments, serialize_intent_fragments
from graphsql.intent import IntentGraph
from graphsql.learned_retriever import (
    LearnedFragmentRetriever,
    LinearRankerModel,
    train_fragment_ranker,
)
from graphsql.retrieval_evaluation import fragment_signature
from graphsql.types import BirdExample


class _FakeEncoder:
    def passage_embed(self, texts):
        for text in texts:
            yield self._vector(text)

    def query_embed(self, texts):
        for text in texts:
            yield self._vector(text)

    @staticmethod
    def _vector(text):
        lowered = text.lower()
        return [float("count" in lowered), float("state" in lowered), 1.0]


def _graph_payload():
    return {
        "graph_version": "0.2",
        "request": "Count accounts by state.",
        "evidence": "",
        "nodes": [
            {
                "node_id": "count",
                "kind": "operation",
                "concept": "count accounts",
                "spans": [{"source": "request", "start": 0, "end": 5, "text": "Count"}],
                "schema_candidates": ["accounts.account_id"],
            },
            {
                "node_id": "state",
                "kind": "attribute",
                "concept": "state",
                "spans": [{"source": "request", "start": 18, "end": 23, "text": "state"}],
                "schema_candidates": ["accounts.state"],
            },
            {
                "node_id": "output",
                "kind": "output",
                "concept": "return grouped counts",
                "spans": [],
                "schema_candidates": [],
            },
        ],
        "edges": [
            {"source": "count", "role": "group_by", "target": "state"},
            {"source": "output", "role": "returns", "target": "count"},
            {"source": "output", "role": "returns", "target": "state"},
        ],
    }


def test_trains_and_reloads_task_specific_ranker(tmp_path):
    example = BirdExample(
        "train",
        "bank",
        "Count accounts by state.",
        "",
        "SELECT state, COUNT(account_id) FROM accounts GROUP BY state",
    )
    corpus = extract_sql_fragments(
        example.gold_sql,
        example_id=example.example_id,
        db_id=example.db_id,
    ) + extract_sql_fragments(
        "SELECT name FROM accounts WHERE balance > 100",
        example_id="negative",
        db_id="bank",
    )
    model_path = tmp_path / "ranker.json"
    summary = train_fragment_ranker(
        [example],
        graph_records={"train": {"graph": _graph_payload()}},
        corpus=corpus,
        output_path=model_path,
        embedding_model="fake",
        encoder=_FakeEncoder(),
        epochs=100,
    )
    assert summary["positive_pairs"] > 0
    payload = json.loads(model_path.read_text())
    assert payload["feature_names"] == [
        "dense_cosine",
        "token_jaccard",
        "operator_jaccard",
        "kind_compatible",
    ]

    graph = IntentGraph.from_dict(_graph_payload())
    retriever = LearnedFragmentRetriever(
        corpus,
        model=LinearRankerModel.load(model_path),
        encoder=_FakeEncoder(),
    )
    hits = retriever.retrieve(serialize_intent_fragments(graph), max_total=5)
    gold_signatures = {
        fragment_signature(fragment)
        for fragment in extract_sql_fragments(
            example.gold_sql,
            example_id="gold",
            db_id="bank",
        )
    }
    assert any(fragment_signature(hit.fragment) in gold_signatures for hit in hits)
