from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a frozen subset through a pinned BIRD Mini-Dev evaluator checkout"
    )
    parser.add_argument("--evaluator-directory", type=Path, required=True)
    parser.add_argument("--evaluator-commit", required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--difficulty", type=Path, required=True)
    parser.add_argument("--database-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    evaluation_directory = args.evaluator_directory.resolve()
    sys.path.insert(0, str(evaluation_directory))
    evaluation = importlib.import_module("evaluation_ex")
    utilities = importlib.import_module("evaluation_utils")

    database_root = str(args.database_root.resolve()) + "/"
    predicted_sql, _ = utilities.package_sqls(
        str(args.predictions), database_root, mode="pred"
    )
    gold_sql, database_paths = utilities.package_sqls(
        str(args.gold), database_root, mode="gt"
    )
    difficulties = [
        json.loads(line)["difficulty"]
        for line in args.difficulty.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not (len(predicted_sql) == len(gold_sql) == len(database_paths) == len(difficulties)):
        raise ValueError("Prediction, gold, database, and difficulty counts must match")

    results = [
        evaluation.execute_model(
            predicted,
            gold,
            database,
            index,
            args.timeout_seconds,
            "SQLite",
        )
        for index, (predicted, gold, database) in enumerate(
            zip(predicted_sql, gold_sql, database_paths, strict=True)
        )
    ]
    by_difficulty: dict[str, list[int]] = defaultdict(list)
    for difficulty, result in zip(difficulties, results, strict=True):
        by_difficulty[difficulty].append(int(result["res"]))
    scores = [int(result["res"]) for result in results]
    summary = {
        "evaluator": "BIRD Mini-Dev evaluation_ex.calculate_ex",
        "evaluator_commit": args.evaluator_commit,
        "examples": len(scores),
        "execution_correct": sum(scores),
        "execution_accuracy": sum(scores) / len(scores) if scores else 0.0,
        "difficulty_counts": dict(Counter(difficulties)),
        "accuracy_by_observed_difficulty": {
            difficulty: sum(values) / len(values)
            for difficulty, values in sorted(by_difficulty.items())
        },
        "per_example": results,
        "aggregation_disclosure": (
            "Uses the pinned official per-query executor and set-based execution-match function. "
            "Subset aggregation is local because this frozen slice contains no challenging examples, "
            "which makes the official full-benchmark difficulty printer divide by zero."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
