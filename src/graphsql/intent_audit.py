from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .types import BirdExample


def extract_sql_features(sql: str, *, dialect: str = "sqlite") -> frozenset[str]:
    """Return coarse semantic demands represented by a gold SQL query.

    These labels select a broad contract-audit sample; they are not targets for
    Model A and deliberately avoid encoding a full SQL AST.
    """
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError as error:
        raise RuntimeError("Intent audit selection requires sqlglot") from error

    expression = sqlglot.parse_one(sql, read=dialect)
    nodes = list(expression.walk())
    features: set[str] = {"projection"}

    joins = [node for node in nodes if isinstance(node, exp.Join)]
    if joins:
        features.add("join")
    if len(joins) > 1:
        features.add("multi_join")
    for join in joins:
        side = str(join.args.get("side") or "").lower()
        kind = str(join.args.get("kind") or "").lower()
        if side in {"left", "right", "full"}:
            features.add("outer_join")
        if kind == "cross":
            features.add("cross_join")

    checks = (
        ("filter", exp.Where),
        ("grouping", exp.Group),
        ("having", exp.Having),
        ("ordering", exp.Order),
        ("top_k", exp.Limit),
        ("subquery", exp.Subquery),
        ("cte", exp.CTE),
        ("window", exp.Window),
        ("case", exp.Case),
        ("between", exp.Between),
        ("membership", exp.In),
        ("pattern_match", exp.Like),
    )
    for label, expression_type in checks:
        if any(isinstance(node, expression_type) for node in nodes):
            features.add(label)

    set_operations = tuple(
        expression_type
        for expression_type in (getattr(exp, "Union", None), getattr(exp, "Intersect", None), getattr(exp, "Except", None))
        if expression_type is not None
    )
    if set_operations and any(isinstance(node, set_operations) for node in nodes):
        features.add("set_operation")

    aggregates = [node for node in nodes if isinstance(node, exp.AggFunc)]
    if aggregates:
        features.add("aggregation")
    if any(isinstance(node, exp.Count) for node in aggregates):
        features.add("count")
    if any(isinstance(node, (exp.Sum, exp.Avg, exp.Min, exp.Max)) for node in aggregates):
        features.add("numeric_aggregation")
    if any(any(isinstance(child, exp.Case) for child in aggregate.walk()) for aggregate in aggregates):
        features.add("conditional_aggregation")

    selects = [node for node in nodes if isinstance(node, exp.Select)]
    if any(select.args.get("distinct") is not None for select in selects):
        features.add("distinct")

    arithmetic_types = (exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod)
    if any(isinstance(node, arithmetic_types) for node in nodes):
        features.add("arithmetic")
    if any(isinstance(node, exp.Div) for node in nodes):
        features.add("ratio")

    function_names = {
        type(node).__name__.lower()
        for node in nodes
        if isinstance(node, exp.Func)
    }
    if function_names & {"substring", "substr", "strtodate", "date", "datetime", "year", "month"}:
        features.add("temporal_or_string_transform")

    comparisons = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE)
    if any(isinstance(node, comparisons) for node in nodes):
        features.add("comparison")
    if any(isinstance(node, exp.Is) for node in nodes):
        features.add("null_check")

    return frozenset(features)


def select_diverse_examples(
    examples: Iterable[BirdExample],
    *,
    size: int = 25,
    dialect: str = "sqlite",
) -> list[tuple[BirdExample, frozenset[str]]]:
    """Select a deterministic SQL-feature, database, and difficulty audit sample."""
    if size <= 0:
        return []
    candidates = [(example, extract_sql_features(example.gold_sql, dialect=dialect)) for example in examples]
    if size >= len(candidates):
        return candidates

    feature_frequency = Counter(feature for _, features in candidates for feature in features)
    selected: list[tuple[BirdExample, frozenset[str]]] = []
    remaining = list(candidates)
    covered_features: set[str] = set()
    covered_databases: set[str] = set()
    covered_difficulties: set[str] = set()
    database_counts: Counter[str] = Counter()
    difficulty_counts: Counter[str] = Counter()
    selected_feature_counts: Counter[str] = Counter()
    database_cap = math.ceil(size / len({example.db_id for example, _ in candidates}))
    difficulty_targets: dict[str, int] = {}
    if size >= 10 and {example.difficulty for example, _ in candidates} >= {
        "challenging",
        "moderate",
        "simple",
    }:
        difficulty_targets = {
            "challenging": round(size * 0.32),
            "moderate": round(size * 0.40),
        }
        difficulty_targets["simple"] = size - sum(difficulty_targets.values())

    while remaining and len(selected) < size:
        eligible = [
            candidate
            for candidate in remaining
            if database_counts[candidate[0].db_id] < database_cap
            and (
                not difficulty_targets
                or difficulty_counts[candidate[0].difficulty]
                < difficulty_targets.get(candidate[0].difficulty, size)
            )
        ]
        if not eligible:
            eligible = remaining

        def score(candidate: tuple[BirdExample, frozenset[str]]) -> tuple[float, int, int]:
            example, features = candidate
            rare_new_features = sum(
                1.0 / feature_frequency[feature]
                for feature in features - covered_features
            )
            database_bonus = 1.0 if example.db_id not in covered_databases else 0.0
            difficulty_bonus = 0.75 if example.difficulty not in covered_difficulties else 0.0
            feature_balance = (
                sum(1.0 / (selected_feature_counts[feature] + 1) for feature in features)
                / len(features)
            )
            difficulty_weight = {"challenging": 3, "moderate": 2, "simple": 1}.get(
                example.difficulty, 0
            )
            return (
                rare_new_features * 100
                + database_bonus * 6
                + difficulty_bonus * 3
                + 1.0 / (database_counts[example.db_id] + 1)
                + feature_balance * 2,
                difficulty_weight,
                -int(example.example_id) if example.example_id.isdigit() else 0,
            )

        chosen = max(eligible, key=score)
        selected.append(chosen)
        remaining.remove(chosen)
        example, features = chosen
        covered_features.update(features)
        covered_databases.add(example.db_id)
        covered_difficulties.add(example.difficulty)
        database_counts[example.db_id] += 1
        difficulty_counts[example.difficulty] += 1
        selected_feature_counts.update(features)

    return selected


def write_intent_audit_sample(
    path: str | Path,
    selected: list[tuple[BirdExample, frozenset[str]]],
) -> dict[str, object]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sample_version": 1,
        "purpose": "Stress-test the intent-graph contract; not a model evaluation split.",
        "examples": [
            {**asdict(example), "sql_features": sorted(features)}
            for example, features in selected
        ],
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "examples": len(selected),
        "databases": len({example.db_id for example, _ in selected}),
        "difficulties": sorted({example.difficulty for example, _ in selected}),
        "features": sorted({feature for _, features in selected for feature in features}),
        "output": str(target),
    }
