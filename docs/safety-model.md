# SQLHarness safety model

## Governing principle

The model proposes SQL. The execution boundary decides whether that proposal is allowed to reach a database.

## Implemented controls

- Parse exactly one SQL statement with SQLGlot.
- Reject mutation and control operations including `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, and transactions.
- Check referenced physical tables and columns against the introspected database schema.
- Open SQLite databases in read-only mode and enable `PRAGMA query_only`.
- Interrupt execution after a configured deadline.
- Truncate returned rows at a configured maximum.
- Record the proposal, validation decision, execution outcome, latency, and correctness in a structured trace.
- Resolve database identifiers only inside a configured authority root; path-like identifiers are rejected.
- Expose schema inspection, validation, query-plan inspection, and execution as five typed MCP tools backed by the same authority used in evaluation.
- Attach a deterministic receipt identifier to each execution decision. This supports trace correlation; it is explicitly not an immutability claim.

## Implemented MCP authority boundary

`DatabaseAuthority` owns database resolution, validation, read-only connections, execution limits, and trace receipts. The MCP server exposes only that capability through `list_databases`, `inspect_schema`, `validate_sql`, `explain_sql`, and `execute_readonly_sql`; it does not expose a raw connection or filesystem path. The SQLHarness evaluation path invokes the same authority before candidate execution, so the server is not a showcase-only wrapper.

An in-memory MCP client integration test proves that a mutation is rejected with `database_touched=false` and that an allowed read returns results through the server. The standalone `sqlharness-mcp` command serves the boundary over MCP's default stdio transport.

## Non-guarantees

Read-only validation does not prove that a query is cheap, semantically correct, privacy-preserving, or appropriate for a particular user. Production use would also require database-native identities and permissions, resource governance, sensitivity policies, and dialect-specific testing. MCP supplies an interface boundary; the policies implemented behind that boundary provide the actual control.
