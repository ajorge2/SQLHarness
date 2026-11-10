# MCP workflow implementation and verification

Prepared 2026-11-08 by Codex. This follows the [earlier audit](mcp-workflow-audit-2026-11-08.md).

## What now runs

The local MCP implementation runs the sequence shown on the page:

```text
Question + evidence + inspected schema
  → model proposes intent graph
  → graph and schema bindings validated
  → one retrieval query for every directed graph relationship
  → distinct compatible catalog fragments ranked
  → model proposes SQL and cites its selected fragments
  → selections, SQL structure, graph bindings and predicates checked
  → shared read-only authority validates and executes
  → structured result and actual stage trace returned
```

`query_database(db_id, question, evidence)` orchestrates the model steps through the connected MCP client. Current clients can use resumable input requests over stateless HTTP. Compatible legacy clients can use their sampling backchannel. No separate model-provider account or API key is configured on the server.

Clients without model-request support use `workflow_contract`, `prepare_query`, and `execute_workflow`. The final tool recomputes graph validation and retrieval and checks the assembly itself. It does not accept an earlier success flag as authority. The original direct-SQL tools are explicitly separate and do not claim a graph/retrieval trace.

The trace records request, intent graph, graph validation, fragment retrieval, ranking, query assembly, authority, and result. Curated inputs are identified as client proposals; model-assisted inputs identify the connected model route. The browser examples disclose their fixed graph/SQL inputs and show real server rankings and results.

## Implementation locations

- [Workflow engine](../src/sqlharness/workflow.py): bounded graph contract, schema binding checks, assembly checks, authority invocation and trace.
- [Relationship retrieval](../src/sqlharness/workflow_retrieval.py): portable SQL-template catalog and deterministic role/operator/text ranking, with an explicit coverage result for every edge.
- [MCP adapter](../src/sqlharness/mcp_server.py): nine tools, connected-client model requests, synthetic demo, input/output bounds and privacy resource.
- [SQL validation](../src/sqlharness/validation.py): added scoped column resolution so an unqualified column is not accepted merely because it exists in an unrelated table.

The same source modules are synchronized into the actual distribution and HTTP runtime:

```text
/Users/ajorge/life/tmp/mcp-release/codearchitect/packages/sqlharness/src/sqlharness
/Users/ajorge/life/tmp/mcp-release/orcview/sqlharness
```

The attached writeup and demo client are in `codearchitect/mcp-public/sqlharness.html` and `codearchitect/mcp-public/assets/portal.js`. The installable `sqlharness_mcp-0.3.0-py3-none-any.whl` was rebuilt and tested directly from the archive with existing dependencies. It includes the graph and workflow modules and needs no research artifact directory or embedding download.

## Running local preview

- Writeup: [http://127.0.0.1:9020/mcp/sqlharness/](http://127.0.0.1:9020/mcp/sqlharness/)
- MCP endpoint through the preview proxy: [http://127.0.0.1:9020/mcp/sqlharness/server](http://127.0.0.1:9020/mcp/sqlharness/server)
- Synthetic runtime: `127.0.0.1:9021`
- Wheel: [download from the local preview](http://127.0.0.1:9020/mcp/install/sqlharness_mcp-0.3.0-py3-none-any.whl)

Preview installation/configuration links use the local origin, so they point at the implementation being reviewed. No production deployment was performed in this change.

To restart the two servers, run:

```sh
# In /Users/ajorge/life/tmp/mcp-release/orcview
PYTHONPATH=. /Users/ajorge/life/tmp/mcp-release/testenv/bin/python tests/preview_mcp.py

# In /Users/ajorge/life/tmp/mcp-release/codearchitect
node scripts/preview-mcp.mjs
```

## Evidence

| Check | Result |
|---|---|
| Complete research/package Python test suite | 84 passed. |
| Node MCP and public-page tests | 8 passed. |
| OrcView ASGI/MCP/privacy checks | 4 passed; an existing Starlette WSGI deprecation warning remains. |
| Browser revenue workflow | Graph → retrieval/ranking → assembly checks → authority/result; paid revenue 1,220. |
| Browser segment workflow | Enterprise 900 and Startup 320, with actual graph/rankings/trace displayed. |
| `query_database` through local HTTP proxy | Two connected-client model requests, all eight trace stages, Northeast/3. |
| Built wheel imported directly | Same automatic MCP route completed with Northeast/3. |
| Narrow browser layout | No main-content overflow observed. |
| Synchronized source copies | Distribution and HTTP runtime modules match the research source. |

Automatic-route protocol tests supplied controlled graph and assembly responses through the real MCP client callback. They test model-request sequencing and server enforcement, not an independent model's natural-language accuracy. Browser fixtures are similarly disclosed; their rankings and database results are computed by the server.

Regression cases stop on invalid graphs, request/evidence mismatches, unsupported catalog coverage, missing or unknown selections, dropped/wrong predicates, extra filters, wrong measured columns, wrong ordering, unsupported SQL scopes, and write attempts.

## Supported scope and remaining limits

The verified assembly contract currently supports a single SELECT scope with projections, COUNT/SUM/AVG/MIN/MAX, scalar conjunctive comparisons, grouping, ordering, limits, and equality joins. The graph format retains nine node kinds and twenty edge roles, but advanced executable semantics such as nested/compound queries, logic composition, ratios, optional relationships, scoped populations and membership stop explicitly when unsupported. A structurally valid graph is not a promise of executable coverage.

The ranker is deterministic and relationship-aware. It is not the separately trained research embedding/logistic ranker. Assembly uses the connected model and is checked against the retrieved plan; it is not an unrestricted direct-SQL fallback or a proof of correct business interpretation.

The region example now runs against the synthetic schema. Existing paid-revenue data and expected totals are preserved. Schema, request, evidence and plan are sent to the connected client for generation; database reads remain behind the authority. Input, result and deadline bounds remain in force. SQLHarness does not persist questions, graphs, SQL or results, although the host and hosting infrastructure have their own policies.
