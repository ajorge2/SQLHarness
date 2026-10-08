from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_preflight.py"
SPEC = importlib.util.spec_from_file_location("publish_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_public_preflight_omits_local_paths():
    manifest = {
        "status": "preflight",
        "benchmark": {
            "name": "BIRD Mini-Dev",
            "dialect": "sqlite",
            "source_examples": 500,
            "selected_examples": 500,
            "dataset_sha256": "a" * 64,
            "selection_sha256": "b" * 64,
            "official_evaluator_commit": "c" * 40,
            "databases": [{"path": "/private/database.sqlite"}],
            "gold_execution_audit": {
                "attempted": 500,
                "succeeded": 498,
                "failed": 2,
                "truncated": 0,
            },
        },
        "execution": {"timeout_seconds": 30, "max_rows": 100000},
        "model": {"id": "model"},
        "pricing": None,
    }
    public = MODULE.build_public_summary(manifest)
    assert public["databases"] == 1
    assert "/private/database.sqlite" not in str(public)
