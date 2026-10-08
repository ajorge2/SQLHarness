from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .authority import DatabaseAuthority


DEFAULT_DATABASE_ROOT = Path("data/bird/minidev/MINIDEV/dev_databases")


def create_server(
    database_root: str | Path,
    *,
    timeout_seconds: float = 5.0,
    max_rows: int = 1_000,
) -> Any:
    try:
        from mcp.server import MCPServer
    except ImportError as error:
        raise RuntimeError("Install the MCP extra: uv sync --extra mcp") from error

    authority = DatabaseAuthority(
        database_root,
        timeout_seconds=timeout_seconds,
        max_rows=max_rows,
    )
    server = MCPServer(
        "SQLHarness Database Authority",
        version="0.1.0",
        instructions=(
            "Inspect schemas, validate proposed SQL, and execute only single-statement "
            "read-only SQLite queries through bounded SQLHarness policy checks."
        ),
    )

    @server.tool()
    def list_databases() -> dict[str, Any]:
        """List databases governed by this server."""

        return authority.list_databases()

    @server.tool()
    def inspect_schema(db_id: str) -> dict[str, Any]:
        """Return tables and columns for one governed database."""

        return authority.schema(db_id)

    @server.tool()
    def validate_sql(db_id: str, sql: str) -> dict[str, Any]:
        """Parse SQL and check schema references and read-only policy without execution."""

        return authority.validate(db_id, sql)

    @server.tool()
    def explain_sql(db_id: str, sql: str) -> dict[str, Any]:
        """Validate a read-only query and return SQLite's bounded query plan."""

        return authority.explain(db_id, sql)

    @server.tool()
    def execute_readonly_sql(db_id: str, sql: str) -> dict[str, Any]:
        """Validate and execute one read-only query with time and row limits."""

        return authority.execute(db_id, sql)

    return server


def _configured_server() -> Any:
    database_root = Path(os.environ.get("SQLHARNESS_DATABASE_ROOT", DEFAULT_DATABASE_ROOT))
    timeout_seconds = float(os.environ.get("SQLHARNESS_QUERY_TIMEOUT_SECONDS", "5"))
    max_rows = int(os.environ.get("SQLHARNESS_MAX_ROWS", "1000"))
    return create_server(
        database_root,
        timeout_seconds=timeout_seconds,
        max_rows=max_rows,
    )


try:
    mcp = _configured_server()
except RuntimeError:
    mcp = None


def main() -> None:
    server = mcp or _configured_server()
    server.run()


if __name__ == "__main__":
    main()
