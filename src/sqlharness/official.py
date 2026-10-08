from __future__ import annotations

import json
from pathlib import Path

from .types import BirdExample


BIRD_SEPARATOR = "\t----- bird -----\t"


def export_bird_evaluator_inputs(
    *,
    trace_path: str | Path,
    examples: list[BirdExample],
    output_directory: str | Path,
) -> dict[str, str]:
    trace_file = Path(trace_path)
    records = [
        json.loads(line)
        for line in trace_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(records) != len(examples):
        raise ValueError(
            f"Trace has {len(records)} records but dataset selection has {len(examples)} examples"
        )

    predictions: dict[str, str] = {}
    for index, (record, example) in enumerate(zip(records, examples, strict=True)):
        traced_example = record.get("example", {})
        traced_id = record.get("example_id", traced_example.get("example_id"))
        if str(traced_id) != example.example_id:
            raise ValueError(
                f"Trace/dataset order mismatch at {index}: "
                f"{traced_id!r} != {example.example_id!r}"
            )
        sql = str(record.get("generation", {}).get("sql", "")).strip()
        predictions[str(index)] = f"{sql}{BIRD_SEPARATOR}{example.db_id}"

    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "predictions.json"
    gold_path = output_dir / "gold.sql"
    difficulty_path = output_dir / "difficulty.jsonl"

    predictions_path.write_text(
        json.dumps(predictions, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    gold_path.write_text(
        "".join(f"{example.gold_sql}\t{example.db_id}\n" for example in examples),
        encoding="utf-8",
    )
    difficulty_path.write_text(
        "".join(
            json.dumps(
                {
                    "question_id": example.example_id,
                    "difficulty": example.difficulty or "unknown",
                },
                ensure_ascii=False,
            )
            + "\n"
            for record, example in zip(records, examples, strict=True)
        ),
        encoding="utf-8",
    )
    return {
        "predictions": str(predictions_path),
        "gold": str(gold_path),
        "difficulty": str(difficulty_path),
    }
