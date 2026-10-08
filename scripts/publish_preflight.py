from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_public_summary(manifest: dict) -> dict:
    benchmark = manifest["benchmark"]
    audit = benchmark["gold_execution_audit"]
    return {
        "artifact": "Arm A preflight",
        "status": manifest["status"],
        "benchmark": benchmark["name"],
        "dialect": benchmark["dialect"],
        "source_examples": benchmark["source_examples"],
        "selected_examples": benchmark["selected_examples"],
        "databases": len(benchmark["databases"]),
        "dataset_sha256": benchmark["dataset_sha256"],
        "selection_sha256": benchmark["selection_sha256"],
        "official_evaluator_commit": benchmark["official_evaluator_commit"],
        "gold_execution_audit": {
            "attempted": audit["attempted"],
            "succeeded_under_local_limits": audit["succeeded"],
            "timed_out_under_local_limits": audit["failed"],
            "truncated": audit["truncated"],
        },
        "local_limits": manifest["execution"],
        "model": manifest["model"],
        "pricing": manifest["pricing"],
        "disclosure": (
            "This is a reproducibility preflight, not model-performance evidence. "
            "The official BIRD evaluator remains authoritative for the headline score."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    summary = build_public_summary(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
