# Query safely using your existing AI chat

SQLHarness exposes five governed database tools to the model you already use in an IDE, Codex CLI, Claude Code or another MCP host. Your model proposes SQL; this server validates it and performs bounded, read-only execution. There is no API-key field, model login, cloud model call or telemetry in this MCP entry point.

## Try synthetic data

Requires Python 3.11+ and uv. From a repository checkout:

```sh
uv sync --extra mcp --extra dev
uv run python -B -m sqlharness.mcp_server
```

The default stdio server exposes only a synthetic `shop` database. Connect it through your MCP host instead of typing questions into its terminal. With absolute paths, either installed CLI can register it:

```sh
codex mcp add sqlharness -- /absolute/path/SQLHarness/.venv/bin/python -B -m sqlharness.mcp_server
claude mcp add --transport stdio --scope local sqlharness -- /absolute/path/SQLHarness/.venv/bin/python -B -m sqlharness.mcp_server
```

Restart the CLI session after registration. IDE users can configure the same stdio command in their host's MCP settings.

Ask:

- “Use SQLHarness to inspect the shop schema and find total paid revenue.” Expected total: **$1220**.
- “Break paid revenue down by customer segment.” Expected: **Startup $320**, **Enterprise $900**.
- “Validate `DELETE FROM orders` and explain why it is blocked. Do not execute it.”

The first request should inspect schema and then execute a single read-only query. Responses include policy decisions, schema/AST validation, bounded results and a deterministic receipt identifier. No model-based grading or generation is performed by these tools.

## Use local databases

Add an explicit root to the server command:

```sh
/absolute/path/SQLHarness/.venv/bin/python -B -m sqlharness.mcp_server --database-root /absolute/path/databases
```

Expected layout:

```text
databases/
  shop/
    shop.sqlite
```

Database IDs contain letters, digits, underscores and hyphens. Tools receive IDs, never unrestricted filesystem paths. Existing clients may explicitly set `SQLHARNESS_DATABASE_ROOT`; otherwise the server uses synthetic data rather than discovering personal databases. Personal roots are available only over local stdio.

## Tools

| Tool | Purpose |
|---|---|
| `list_databases` | Discover IDs under the configured root |
| `inspect_schema` | Inspect table and column names |
| `validate_sql` | Apply AST, schema and read-only policy without executing the proposed query |
| `explain_sql` | Inspect a bounded query plan |
| `execute_readonly_sql` | Validate and execute through the same database authority |

Queries are capped at 16000 characters, 1000 returned rows and a 5-second execution timeout by default. Serialized tool results larger than 512 KB are rejected with guidance to narrow the query. Invalid IDs and operation failures produce bounded errors without leaking server filesystem paths. These are prototype execution limits, not a general resource-isolation sandbox.

## Privacy

The MCP server does not persist query text, tool inputs, result rows or receipts, and makes no model/API calls. Personal database files are opened read-only. The no-account demo materializes synthetic sample data in a temporary directory and removes it on normal shutdown; it never writes request content into those files. Logs and telemetry are disabled for the command-line entry point.

Results enter your AI application's conversation and may be stored or sent to its model provider under that application's policies. Existing SQLHarness research commands can write evaluation artifacts and call models; those are separate from the MCP server.

Read `privacy://policy` through MCP for the machine-readable policy.

## Verify or run an HTTP demo

```sh
uv run python -B -m pytest tests/test_mcp_server.py tests/test_mcp_privacy.py tests/test_authority.py -q
uv run python -B -m sqlharness.mcp_server --http-demo --port 8001
```

The HTTP command serves synthetic data on `http://127.0.0.1:8001/mcp` only. It rejects personal database roots. This is a local Streamable HTTP demo, not a deployed public service. Tests exercise actual MCP calls, blocked mutations, row limits, input bounds and unchanged sample database content with networking denied.

Updated 2026-10-23 by Codex.
