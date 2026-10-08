from __future__ import annotations

import pytest

pytest.importorskip("sqlglot")

from graphsql.intent_audit import extract_sql_features, select_diverse_examples
from graphsql.types import BirdExample


def example(example_id: str, db_id: str, difficulty: str, sql: str) -> BirdExample:
    return BirdExample(
        example_id=example_id,
        db_id=db_id,
        question="Question",
        evidence="",
        gold_sql=sql,
        difficulty=difficulty,
    )


def test_extracts_compositional_sql_demands():
    features = extract_sql_features(
        """
        SELECT region, SUM(CASE WHEN currency = 'EUR' THEN amount ELSE 0 END) AS eur
        FROM payments
        WHERE paid_at BETWEEN '2025-01-01' AND '2025-12-31'
        GROUP BY region
        HAVING SUM(amount) > 100
        ORDER BY eur DESC
        LIMIT 3
        """
    )
    assert {
        "filter",
        "between",
        "aggregation",
        "conditional_aggregation",
        "grouping",
        "having",
        "ordering",
        "top_k",
    } <= features


def test_diverse_selector_rewards_new_features_and_databases():
    examples = [
        example("1", "a", "simple", "SELECT id FROM people"),
        example("2", "a", "moderate", "SELECT COUNT(*) FROM people"),
        example("3", "b", "challenging", "SELECT id FROM people WHERE id IN (SELECT person_id FROM orders)"),
    ]
    selected = select_diverse_examples(examples, size=2)
    selected_ids = {item.example_id for item, _ in selected}
    assert "3" in selected_ids
    assert len({item.db_id for item, _ in selected}) == 2
