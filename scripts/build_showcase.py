from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from graphsql.benchmark import run_baseline  # noqa: E402
from graphsql.authority import DatabaseAuthority  # noqa: E402
from graphsql.types import BirdExample, Generation  # noqa: E402


class OfflineShowcaseGenerator:
    """A deterministic generator used only to exercise the real harness offline."""

    RESPONSES = {
        "Which region has the most customers?": (
            "SELECT r.name, COUNT(*) AS customer_count "
            "FROM customers AS c JOIN regions AS r ON c.region_id = r.id "
            "GROUP BY r.id, r.name ORDER BY customer_count DESC LIMIT 1"
        ),
        "How many customers made at least one purchase over $100?": (
            "SELECT COUNT(DISTINCT customer_id) AS customer_count "
            "FROM purchases WHERE amount > 100"
        ),
    }

    def generate(self, *, question: str, evidence: str, schema: str) -> Generation:
        del evidence, schema
        return Generation(
            sql=self.RESPONSES[question],
            model="deterministic-offline-fixture",
            latency_ms=0.0,
        )


def build_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE regions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                region_id INTEGER NOT NULL REFERENCES regions(id)
            );
            CREATE TABLE purchases (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                amount REAL NOT NULL,
                purchased_at TEXT NOT NULL
            );

            INSERT INTO regions VALUES
                (1, 'Northeast'), (2, 'West'), (3, 'South');
            INSERT INTO customers VALUES
                (1, 'Ada', 1), (2, 'Grace', 1), (3, 'Linus', 2),
                (4, 'Margaret', 1), (5, 'Edsger', 3);
            INSERT INTO purchases VALUES
                (1, 1, 140.00, '2026-01-02'),
                (2, 1, 35.00, '2026-01-08'),
                (3, 2, 220.00, '2026-01-09'),
                (4, 3, 85.00, '2026-01-11'),
                (5, 5, 105.00, '2026-01-12');
            """
        )


def main() -> None:
    data_dir = ROOT / "docs" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    examples = [
        BirdExample(
            example_id="showcase-001",
            db_id="commerce",
            question="Which region has the most customers?",
            evidence="Count customers by region and return only the largest group.",
            gold_sql=(
                "SELECT r.name, COUNT(c.id) AS customer_count "
                "FROM regions r JOIN customers c ON r.id = c.region_id "
                "GROUP BY r.id, r.name ORDER BY customer_count DESC LIMIT 1"
            ),
        ),
        BirdExample(
            example_id="showcase-002",
            db_id="commerce",
            question="How many customers made at least one purchase over $100?",
            evidence="A customer should be counted once even if they have multiple purchases.",
            gold_sql=(
                "SELECT COUNT(DISTINCT customer_id) AS customer_count "
                "FROM purchases WHERE amount > 100"
            ),
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="graphsql-showcase-") as temporary:
        database_root = Path(temporary)
        database_dir = database_root / "commerce"
        database_dir.mkdir()
        database_path = database_dir / "commerce.sqlite"
        build_database(database_path)

        trace_path = data_dir / "offline-demo.jsonl"
        summary = run_baseline(
            examples,
            database_root=database_root,
            generator=OfflineShowcaseGenerator(),
            output_path=trace_path,
        )
        authority = DatabaseAuthority(database_root, max_rows=100)
        enriched_traces = []
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            trace = json.loads(line)
            trace["authority_receipt"] = authority.execute(
                trace["example"]["db_id"],
                trace["generation"]["sql"],
            )
            enriched_traces.append(trace)
        trace_path.write_text(
            "".join(json.dumps(trace, default=str) + "\n" for trace in enriched_traces),
            encoding="utf-8",
        )

        blocked_sql = "DELETE FROM purchases WHERE amount < 10"
        policy_trace = authority.execute("commerce", blocked_sql)
        policy_trace.update({
            "request": "Clean up purchases below $10.",
            "proposed_sql": blocked_sql,
        })
        (data_dir / "policy-demo.json").write_text(
            json.dumps(policy_trace, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    manifest = {
        "artifact": "SQLHarness offline showcase",
        "generated_by": "scripts/build_showcase.py",
        "uses_production_harness_code": True,
        "uses_database_authority": True,
        "requires_api_key": False,
        "benchmark_claim": False,
        "disclosure": (
            "These deterministic fixtures prove the evaluation and safety paths are runnable. "
            "They are not BIRD benchmark results or evidence of model quality."
        ),
        "trace_examples": summary["examples"],
        "execution_accuracy": summary["execution_accuracy"],
        "validation_rate": summary["validation_rate"],
    }
    (data_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Built showcase artifacts in {data_dir}")


if __name__ == "__main__":
    main()
