from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .dataset import find_sqlite_database
from .execution import execute_sqlite_readonly
from .providers.openai import SYSTEM_PROMPT
from .types import BirdExample, TokenUsage


BIRD_MINI_DEV_SOURCE = "https://huggingface.co/datasets/birdsql/bird_mini_dev"
BIRD_MINI_DEV_CODE = "https://github.com/bird-bench/mini_dev"
BIRD_MINI_DEV_EVALUATOR_COMMIT = "abd11b6db92a1c9f809b32f7564c7c71b34d67f0"
OPENAI_PRICING_SOURCE = "https://developers.openai.com/api/docs/pricing"


@dataclass(frozen=True)
class PricingRates:
    model: str
    input_usd_per_million: float
    cached_input_usd_per_million: float
    output_usd_per_million: float
    captured_at: str
    source_url: str = OPENAI_PRICING_SOURCE

    @classmethod
    def from_json(cls, path: str | Path) -> PricingRates:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            model=str(payload["model"]),
            input_usd_per_million=float(payload["input_usd_per_million"]),
            cached_input_usd_per_million=float(payload["cached_input_usd_per_million"]),
            output_usd_per_million=float(payload["output_usd_per_million"]),
            captured_at=str(payload["captured_at"]),
            source_url=str(payload.get("source_url", OPENAI_PRICING_SOURCE)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_usage_cost(usage: TokenUsage, pricing: PricingRates) -> float:
    uncached_input = max(usage.input_tokens - usage.cached_input_tokens, 0)
    total = (
        uncached_input * pricing.input_usd_per_million
        + usage.cached_input_tokens * pricing.cached_input_usd_per_million
        + usage.output_tokens * pricing.output_usd_per_million
    ) / 1_000_000
    return round(total, 8)


def is_select_only(sql: str, *, dialect: str = "sqlite") -> bool:
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError as error:
        raise RuntimeError("SQL classification requires the sqlglot dependency") from error
    try:
        statements = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.ParseError:
        return False
    if len(statements) != 1:
        return False
    expression = statements[0]
    blocked_types = tuple(
        expression_type
        for name in (
            "Alter",
            "Command",
            "Create",
            "Delete",
            "Drop",
            "Insert",
            "Merge",
            "Transaction",
            "Update",
        )
        if (expression_type := getattr(exp, name, None)) is not None
    )
    return not any(isinstance(node, blocked_types) for node in expression.walk())


def select_readonly_examples(
    examples: Iterable[BirdExample],
    *,
    offset: int = 0,
    limit: int | None = None,
    dialect: str = "sqlite",
) -> tuple[list[BirdExample], int]:
    all_examples = list(examples)
    readonly = [example for example in all_examples if is_select_only(example.gold_sql, dialect=dialect)]
    omitted = len(all_examples) - len(readonly)
    start = max(offset, 0)
    stop = None if limit is None else start + max(limit, 0)
    return readonly[start:stop], omitted


def build_preflight_manifest(
    *,
    dataset_path: str | Path,
    database_root: str | Path,
    all_examples: list[BirdExample],
    selected_examples: list[BirdExample],
    omitted_non_readonly: int,
    model: str,
    reasoning_effort: str | None,
    timeout_seconds: float,
    max_rows: int,
    offset: int,
    limit: int | None,
    pricing: PricingRates | None,
    provider: str = "openai",
) -> dict[str, Any]:
    dataset = Path(dataset_path).resolve()
    database_root_path = Path(database_root).resolve()
    databases = []
    for db_id in sorted({example.db_id for example in selected_examples}):
        database_path = find_sqlite_database(database_root_path, db_id)
        databases.append(
            {
                "db_id": db_id,
                "path": _relative_or_absolute(database_path, database_root_path),
                "bytes": database_path.stat().st_size,
                "sha256": _sha256_file(database_path),
            }
        )

    pricing_payload: dict[str, Any] | None = None
    if pricing is not None:
        if pricing.model != model:
            raise ValueError(
                f"Pricing model {pricing.model!r} does not match baseline model {model!r}"
            )
        pricing_payload = pricing.to_dict()

    gold_execution_audit = _audit_gold_execution(
        selected_examples,
        database_root=database_root_path,
        timeout_seconds=timeout_seconds,
        max_rows=max_rows,
    )

    return {
        "manifest_version": 1,
        "status": "preflight",
        "created_at": datetime.now(UTC).isoformat(),
        "benchmark": {
            "name": "BIRD Mini-Dev",
            "dialect": "sqlite",
            "subset_policy": "single-statement SELECT-only gold queries",
            "source_url": BIRD_MINI_DEV_SOURCE,
            "official_code_url": BIRD_MINI_DEV_CODE,
            "official_evaluator_commit": BIRD_MINI_DEV_EVALUATOR_COMMIT,
            "dataset_path": str(dataset),
            "dataset_sha256": _sha256_file(dataset),
            "source_examples": len(all_examples),
            "omitted_non_readonly_or_unparseable": omitted_non_readonly,
            "selected_examples": len(selected_examples),
            "selection_offset": max(offset, 0),
            "selection_limit": limit,
            "selection_sha256": _selection_hash(selected_examples),
            "databases": databases,
            "gold_execution_audit": gold_execution_audit,
        },
        "model": {
            "provider": provider,
            "id": model,
            "reasoning_effort": reasoning_effort,
            "store": False if provider == "openai" else None,
            "interface": "responses-api" if provider == "openai" else "codex-exec",
            "ephemeral": provider == "codex-cli",
        },
        "prompt": {
            "version": "direct-sql-v1",
            "system_prompt_sha256": _sha256_text(SYSTEM_PROMPT),
        },
        "execution": {
            "timeout_seconds": timeout_seconds,
            "max_rows": max_rows,
            "database_mode": "read-only",
        },
        "pricing": pricing_payload,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": {
                name: _package_version(name) for name in ("openai", "sqlglot")
            },
            "source_sha256": _source_hash(Path(__file__).resolve().parent),
        },
    }


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _selection_hash(examples: list[BirdExample]) -> str:
    payload = [asdict(example) for example in examples]
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _audit_gold_execution(
    examples: list[BirdExample],
    *,
    database_root: Path,
    timeout_seconds: float,
    max_rows: int,
) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    truncated_ids: list[str] = []
    total_latency_ms = 0.0
    succeeded = 0
    for example in examples:
        database_path = find_sqlite_database(database_root, example.db_id)
        result = execute_sqlite_readonly(
            database_path,
            example.gold_sql,
            timeout_seconds=timeout_seconds,
            max_rows=max_rows,
        )
        total_latency_ms += result.latency_ms
        if result.succeeded:
            succeeded += 1
        else:
            failures.append(
                {
                    "example_id": example.example_id,
                    "db_id": example.db_id,
                    "error": result.error or "unknown execution error",
                }
            )
        if result.truncated:
            truncated_ids.append(example.example_id)
    return {
        "ready": not failures and not truncated_ids,
        "attempted": len(examples),
        "succeeded": succeeded,
        "failed": len(failures),
        "truncated": len(truncated_ids),
        "total_latency_ms": round(total_latency_ms, 3),
        "failures": failures,
        "truncated_example_ids": truncated_ids,
    }


def _source_hash(source_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(source_root.rglob("*.py")):
        digest.update(path.relative_to(source_root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None
