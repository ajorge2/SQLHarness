# SQLHarness MCP: from question to governed result

SQLHarness exposes a complete question workflow alongside its original five database tools. It reads the schema, builds and validates an intent graph, ranks reusable SQL templates for every relationship, checks query assembly, and executes through the read-only database authority. Its trace records which stages actually ran and where a request stopped.

Your connected AI application supplies the model for graph generation and assembly. No separate API key or server-side model-provider account is required. Your application's normal model usage and retention policies apply.

## Full workflow

For clients supporting MCP model requests, call `query_database` with `db_id`, `question`, and optional `evidence`. The server requests a graph from the host model, validates it, ranks candidates for each directed edge, asks the host to assemble SQL with fragment citations, checks the assembly, and runs the approved read. Invalid or unsupported intermediate output stops the workflow instead of falling back to direct SQL.

Current MCP clients can use the SDK's resumable input requests; compatible older clients use their sampling backchannel. For clients without model-request support, use the same deterministic gates in stages:

1. `workflow_contract(db_id, question, evidence)` returns the schema and graph-generation contract.
2. The host model produces the graph; `prepare_query(db_id, question, graph, evidence)` validates it and ranks per-relationship fragments.
3. The host assembles `{sql, selections}`, where `selections` contains one `{relation_id, fragment_id}` per relationship.
4. `execute_workflow(db_id, question, graph, assembly, evidence)` recomputes the graph checks and ranking, checks the assembly, and invokes the authority.

The execution tool does not trust an earlier success flag or a client-supplied trace. The workflow is stateless; no plan or query file is stored by the server.

### Supported scope

The graph contract retains nine node kinds and twenty edge roles. The live MCP uses a bundled schema-neutral SQL-template catalog and a deterministic relationship/operator/text ranker; it does not download embeddings or claim to run the research trained ranker. Each directed edge gets its own candidate list, unlike the research neighborhood serializer.

The current verified assembly contract supports a single SELECT with projections, supported aggregates, comparisons, grouping, ordering, limits, and equality joins. Advanced graph constructs requiring nested scopes, compound queries, ratios, logic composition, optional relationships, or membership abstain explicitly. Graph validation alone does not imply that every supported graph role has executable SQL coverage.

Assembly must cite valid ranked candidates for every relationship and pass the implemented graph/SQL checks. These checks do not prove that the model understood every business requirement. The original five SQL tools remain an explicitly separate route for already-written SQL and do not claim a graph/retrieval trace.

The website's buttons use curated graph and SQL fixtures to demonstrate actual preparation and execution without a browser model account. Those fixtures demonstrate the pipeline, not model answer accuracy.

## Try synthetic data

Requires Python 3.11+ and uv. From a repository checkout:

```sh
uv sync --extra mcp --extra dev
uv run python -B -m sqlharness.mcp_server
```

The default stdio server exposes only a temporary synthetic `shop` database. It includes customers, orders, and regions: paid revenue is $1,220 and the region example returns Northeast with three customers. Connect it through your MCP host instead of typing questions into its terminal. With absolute paths, either installed CLI can register it:

```sh
codex mcp add sqlharness -- /absolute/path/SQLHarness/.venv/bin/python -B -m sqlharness.mcp_server
claude mcp add --transport stdio --scope local sqlharness -- /absolute/path/SQLHarness/.venv/bin/python -B -m sqlharness.mcp_server
```

Restart the CLI session after registration. IDE users can configure the same stdio command in their host's MCP settings.

Ask:

- “Use SQLHarness to inspect the shop schema and find total paid revenue.” Expected total: **$1220**.
- “Break paid revenue down by customer segment.” Expected: **Startup $320**, **Enterprise $900**.
- “Validate `DELETE FROM orders` and explain why it is blocked. Do not execute it.”

For natural-language questions, ask the host to use `query_database`, or the staged workflow if sampling is unavailable. Responses include the graph, rankings, assembly checks, stage trace, authority decision, bounded results, and a receipt identifier. Direct SQL validation/execution tools still perform no model generation themselves.

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
| `workflow_contract` | Inspect schema and obtain the exact graph/assembly instructions |
| `prepare_query` | Validate a proposed graph and rank fragments for every edge |
| `execute_workflow` | Recompute and enforce all workflow gates before execution |
| `query_database` | Orchestrate graph and assembly model requests through the connected client |
| `list_databases` | Discover IDs under the configured root |
| `inspect_schema` | Inspect table and column names |
| `validate_sql` | Apply AST, schema and read-only policy without executing the proposed query |
| `explain_sql` | Inspect a bounded query plan |
| `execute_readonly_sql` | Validate and execute through the same database authority |

Questions and evidence are each capped at 8,000 characters; graphs are bounded at 64 KB, 64 nodes, and 96 edges. Queries are capped at 16,000 characters, 1,000 returned rows and a five-second execution timeout by default. Serialized tool results larger than 512,000 bytes are rejected. Invalid IDs and operation failures produce bounded errors without leaking server filesystem paths. These are prototype execution limits, not process isolation or per-user authorization.

## Privacy

The MCP server does not persist questions, graphs, query text, inputs, result rows, or receipts. `query_database` sends the question, evidence, schema, and plan to the connected MCP client for model generation; it does not connect to an independent model API. Protocol continuation state travels with the client. Personal database files are opened read-only. The synthetic demo creates sample data in a temporary directory and removes it on normal shutdown; it never writes request content into those files. Logs and telemetry are disabled for the entry point.

Workflow context and results enter your AI application and may be stored or sent to its model provider under that application's policies. Research commands can separately write evaluation artifacts and call configured providers.

Read `privacy://policy` through MCP for the machine-readable policy.

## Verify or run an HTTP demo

```sh
uv run python -B -m pytest
uv run python -B -m sqlharness.mcp_server --http-demo --port 8001
```

The HTTP command serves synthetic data on `http://127.0.0.1:8001/mcp` only. It rejects personal database roots. This is a local Streamable HTTP demo, not a deployed public service. Tests exercise actual MCP calls, blocked mutations, row limits, input bounds and unchanged sample database content with networking denied.

Updated 2026-11-08 by Codex.
