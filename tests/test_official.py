from __future__ import annotations

import json

import pytest

from graphsql.official import BIRD_SEPARATOR, export_bird_evaluator_inputs
from graphsql.types import BirdExample


def test_exports_official_bird_input_contract(tmp_path):
    examples = [
        BirdExample(
            example_id="7",
            db_id="shop",
            question="Count customers",
            evidence="",
            gold_sql="SELECT COUNT(*) FROM customers",
            difficulty="simple",
        )
    ]
    trace = tmp_path / "trace.jsonl"
    trace.write_text(
        json.dumps(
            {
                "example": {"example_id": "7"},
                "generation": {"sql": "SELECT COUNT(id) FROM customers"},
            }
        )
        + "\n"
    )
    outputs = export_bird_evaluator_inputs(
        trace_path=trace,
        examples=examples,
        output_directory=tmp_path / "official",
    )
    predictions = json.loads((tmp_path / "official" / "predictions.json").read_text())
    assert predictions == {"0": f"SELECT COUNT(id) FROM customers{BIRD_SEPARATOR}shop"}
    assert (tmp_path / "official" / "gold.sql").read_text() == (
        "SELECT COUNT(*) FROM customers\tshop\n"
    )
    difficulty = json.loads((tmp_path / "official" / "difficulty.jsonl").read_text())
    assert difficulty == {"question_id": "7", "difficulty": "simple"}
    assert set(outputs) == {"predictions", "gold", "difficulty"}


def test_rejects_partial_trace(tmp_path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text("")
    with pytest.raises(ValueError, match="Trace has 0 records"):
        export_bird_evaluator_inputs(
            trace_path=trace,
            examples=[
                BirdExample(
                    example_id="1",
                    db_id="shop",
                    question="Question",
                    evidence="",
                    gold_sql="SELECT 1",
                )
            ],
            output_directory=tmp_path / "official",
        )
