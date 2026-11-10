# SQLHarness: page and MCP workflow audit

**Prepared for Andrew Jorge · 2026-11-08 · Codex**  
**Code reviewed:** `b4a7f72`, plus the small page-formatting changes described below.

> Historical snapshot before the implementation work. The full MCP workflow was subsequently added locally; see [implementation and verification notes](mcp-workflow-implementation-2026-11-08.md) and the [current MCP contract](mcp.md). The findings below describe the earlier version, not the updated local runtime.

## Finding

The MCP implements the **database authority and execution portion** of the workflow on the page. It does not currently run the intent graph, fragment retrieval, ranking, or query assembly stages.

Those earlier stages do exist in the research code. They are separate from the MCP entry point, and some work differently from the diagram. The page is therefore a useful explanation of the research architecture, but it should not be presented as a literal trace of what the current MCP does for each question.

There is no defensible single percentage for this match: schema inspection, model reasoning, SQL safety, and answer correctness are different capabilities. The stage-by-stage comparison below identifies which behavior is actually implemented and where.

## What happens when someone uses the MCP

```text
User asks a question in their AI application
                    ↓
The host model may inspect the database through MCP
                    ↓
The host model writes SQL
                    ↓
execute_readonly_sql(db_id, sql)
                    ↓
Resolve database → inspect schema → validate SQL
                    ↓
Block the query, or execute it through read-only SQLite
                    ↓
Return a structured decision, validation details, and bounded results
                    ↓
The host model may turn the result into a natural-language answer
```

The server exposes exactly five tools:

| Tool | Input | Responsibility |
|---|---|---|
| `list_databases` | None | List configured database IDs. |
| `inspect_schema` | Database ID | Return table and column names. |
| `validate_sql` | Database ID and SQL | Check a proposed SQL statement without executing it. |
| `explain_sql` | Database ID and SQL | Validate and return a bounded SQLite query plan. |
| `execute_readonly_sql` | Database ID and SQL | Validate again, then execute an approved read. |

None accepts a question, business rules, intent graph, node pair, fragment catalog, or ranking configuration. The MCP imports `DatabaseAuthority`; it does not import the research generator, retriever, or assembler. This is also stated accurately in [the MCP documentation](mcp.md): the host model proposes SQL and the server governs execution.

**Evidence:** [mcp_server.py](../src/sqlharness/mcp_server.py), lines 14 and 44–111; [authority.py](../src/sqlharness/authority.py), lines 44–92.

Inspecting the schema, validating separately, and explaining separately are optional client actions. A client can call `execute_readonly_sql` directly. SQL validation still happens inside that execution call, so skipping the optional tools does not skip the implemented authority check. However, the server does not require or prove that the host performed the earlier reasoning stages.

## Comparison with the page

| Page stage | Current MCP | Research implementation | Assessment |
|---|---|---|---|
| Read the request, database map, and business rules | Receives database IDs and SQL; exposes schema inspection. The question and rules stay with the host. | Graph-generation prompts receive question, evidence, and schema. | Only schema access is an MCP capability. |
| Build an intent graph | No graph-generation tool or graph input. | A Codex-backed generator produces structured graph JSON. | Implemented separately in research. |
| Validate the graph | No graph validation on MCP requests. | Graph structure and schema candidates are checked; invalid graphs stop the research vertical slice. | Real checks, absent from the MCP path. |
| Rank fragments for each pair of nodes | No fragment retrieval or ranking. | Retrieval queries describe eligible nodes and their neighborhoods; candidate SQL fragments are ranked and deduplicated. | Both an integration gap and a diagram/code mismatch. |
| Assemble the selected SQL pieces | The host supplies already-written SQL. | A model generates SQL using the graph and retrieved fragments as context. | Assembly exists, but is not a deterministic stitcher. |
| Apply the authority boundary | SQL is parsed and checked; execution uses the shared database authority. | The research vertical slice uses that same authority. | The strongest direct match. |
| Execute and return the answer | Returns a receipt with structured rows, columns, errors, timing, and truncation. | Research records execution and compares it with reference results. | Structured results match; final prose is the host's work. |

### 1. AMR is an inspiration, not the runtime graph format

The page's explanation of separating meaning from wording is appropriate as motivation. The implementation uses a custom graph contract, version `0.2`, rather than a standard AMR parser or standard AMR output.

The page groups concepts into four accessible categories. The code actually supports **nine node kinds**: `entity`, `attribute`, `value`, `operation`, `condition`, `logic`, `relation`, `scope`, and `output`. It defines **20 edge roles** with specific allowed source and target kinds.

That makes the four-category view an explanation, not the complete machine contract. Even arrow directions are sometimes explanatory: the page shows data “returned as” output, while the actual `returns` role points from an output node to the thing it returns. The displayed relationship catalog should not be copied directly into a graph JSON payload.

**Evidence:** [intent.py](../src/sqlharness/intent.py), lines 7–96; [codex_cli_intent.py](../src/sqlharness/providers/codex_cli_intent.py), lines 104–141.

### 2. Graph validation is substantial, but belongs to the research route

The validator checks the graph version, node IDs and kinds, concepts, exact source spans or inferred markers, one output node, supported edge signatures, duplicate connections, cycles, and connectivity. Schema-candidate validation separately checks proposed table and field matches. The research runner abstains when these checks fail.

This supports the graph-checking explanation on the page. It does not mean the MCP requires a validated graph before running SQL: its tools have no graph argument.

**Evidence:** [intent.py](../src/sqlharness/intent.py), lines 172–256; [intent_evaluation.py](../src/sqlharness/intent_evaluation.py), lines 165–178; [vertical_slice.py](../src/sqlharness/vertical_slice.py), lines 108–123.

### 3. Retrieval currently uses neighborhoods, not one independent pair per row

`serialize_intent_fragments` visits eligible root nodes: operations, conditions, logic, relations, scopes, and outputs. For each root, it combines its concept, source words, schema candidates, and **all its incoming and outgoing neighbors** into one retrieval query.

The repository's region example demonstrates the difference: its graph has **five edges**, but serialization produces **three retrieval queries**, rooted at `customer_count`, `largest_group`, and `answer`. The page shows five relationship rows ranked independently. That is not the current serializer's unit of work.

Research retrieval supports lexical, dense, and learned variants. The learned ranker considers semantic similarity, shared tokens, operator overlap, and kind compatibility, which broadly supports the page's description of its scoring signals. However, the vertical slice defaults to lexical retrieval unless another retriever is supplied.

Retrievers keep top candidates per eligible root, then deduplicate across roots and apply a total limit. They do not guarantee one winning fragment for each displayed relationship. The catalog also contains parameterized templates extracted from example SQL; the page's concrete snippets and highlighted winners are illustrative rather than a live ranking trace.

**Evidence:** [fragments.py](../src/sqlharness/fragments.py), lines 118–194, 245–292, and 310–335; [learned_retriever.py](../src/sqlharness/learned_retriever.py), lines 212–300; [vertical_slice.py](../src/sqlharness/vertical_slice.py), lines 65–76 and 125–136.

### 4. Assembly can generate SQL beyond the selected fragments

The assembler receives the question, evidence, schema, graph, and retrieved hits. Its prompt explicitly treats the fragments as structural hints, replaces placeholders, and avoids identifiers absent from the supplied schema. A model produces the completed SQL and can attempt repairs after validation or execution errors.

Consequently, the page's claim that a missing catalog piece makes completion impossible is stronger than the implementation supports. The research runner stops when there are **no retrieval hits**. It does not prove that every required piece is present, nor prevent the assembler from generating missing structure.

**Evidence:** [codex_cli_assembler.py](../src/sqlharness/providers/codex_cli_assembler.py), lines 28–65 and 138–157; [vertical_slice.py](../src/sqlharness/vertical_slice.py), lines 131–178.

### 5. The authority boundary is real, with specific limits

Both research execution and MCP execution use `DatabaseAuthority`. The MCP's checks and bounds include:

- Restricted database IDs and containment within an explicitly configured root.
- A single parsed read-only query; rejection of writes and administrative statements.
- Table and column checks against the inspected schema.
- SQLite opened with `mode=ro` and `PRAGMA query_only=ON`.
- A default five-second execution deadline and at most 1,000 returned rows, with a truncation flag.
- A 16,000-character SQL input limit, a SQLite scalar/record length limit, and a 512,000-byte serialized tool-result limit.

These are useful execution controls. They are not proof that a query captures the user's business intent. The server cannot compare SQL with a question it never receives.

There are also practical limits to the wording “block invalid table or field names.” Unqualified columns are checked against columns from **all tables**, not fully resolved within each SQL scope. A probe with `customers(id, name)` and `orders(id, amount_usd)` found that `SELECT amount_usd FROM customers` passed validation, although SQLite would reject it on execution. The boundary remains read-only, but validation is not a complete SQL name resolver.

Other qualifications: the row cap limits returned rows, not all work the query performs; the deadline uses SQLite progress callbacks rather than process isolation; the response-size check occurs after producing and serializing the result. There is no per-user, tenant, table, or column permission system in these tools beyond the configured root and read-only policy.

Finally, `database_touched: false` means the proposed query was not executed. The authority may already have read schema metadata. Receipt IDs identify a particular receipt payload; they are not immutable audit-log guarantees and may change between runs because execution timing changes.

**Evidence:** [validation.py](../src/sqlharness/validation.py), lines 20–90; [execution.py](../src/sqlharness/execution.py), lines 20–51; [authority.py](../src/sqlharness/authority.py), lines 65–92 and 124–141; [mcp_server.py](../src/sqlharness/mcp_server.py), lines 18–61.

### 6. The default MCP demo does not contain the page's region example

The default synthetic `shop` database contains:

```text
customers(id, segment)
orders(id, customer_id, amount_usd, status)
```

It has no `regions` table or `customers.region_id` column. Running the page's assembled region query through that demo is blocked for those missing references. “Northeast, 3 customers” is an example on the page, not the result of the default MCP demo.

The MCP returns a larger structured receipt containing validation and execution information. The page's `columns`/`rows` display is a simplified representation of that result. A natural-language sentence such as “The Northeast region…” would be produced by the host model, not this MCP server.

**Evidence:** [mcp_server.py](../src/sqlharness/mcp_server.py), lines 114–126; [authority.py](../src/sqlharness/authority.py), lines 85–92.

## Verification performed

The full repository test suite passed: **43 tests in 1.02 seconds**, using `.venv/bin/pytest`.

Additional probes used the real in-process MCP client and a temporary synthetic SQLite database, without external model calls:

| Probe | Observed result |
|---|---|
| List tools | Exactly the five tools above. |
| Inspect `shop` | Returned the `customers` and `orders` schema above. |
| Sum orders where `status = 'paid'` | Executed; total **1,220**. |
| Sum all orders, omitting that filter | Also executed and validated; total **1,300**. This is safe SQL but wrong for a paid-revenue question. |
| Delete from orders | Blocked. |
| Fetch orders with a two-row configured cap | Returned two rows and `truncated: true`. |
| Explain a customer query | Returned an explained decision and a `SCAN customers` plan. |
| Send 16,001 SQL characters | Rejected by the tool input bound. |
| Run the page's region query on the synthetic demo | Blocked for missing schema references. |
| Serialize the example intent graph | Five graph edges produced three retrieval queries. |
| Compare synthetic database hashes before and after the runtime probes | Unchanged. |

Existing tests also exercise blocked administrative/multiple statements, oversized blob results, invalid IDs, network denial, and unchanged sample database files. Research tests use fixtures, a fake encoder, or a fake assembler where appropriate. Passing them does not establish real-model answer accuracy, nor prove a full MCP pipeline that is not wired up.

**Coverage:** [test_mcp_server.py](../tests/test_mcp_server.py), [test_mcp_privacy.py](../tests/test_mcp_privacy.py), [test_vertical_slice.py](../tests/test_vertical_slice.py), [test_learned_retriever.py](../tests/test_learned_retriever.py).

## Recommended decisions

1. **Describe the current MCP as the execution adapter.** Suggested wording: “Your AI model writes the SQL. SQLHarness checks it and runs approved reads with execution limits.” Keep the full diagram identified as the research architecture.
2. **Choose the retrieval contract.** Either explain eligible nodes and their neighborhoods on the page, or implement per-edge retrieval before calling the five displayed rows a literal runtime trace.
3. **Qualify the assembly claim.** Explain that a model uses retrieved fragments to generate SQL. Replace the missing-piece guarantee unless coverage checks and constrained assembly are implemented.
4. **Make the examples reproducible together.** Supply a region-based demo fixture, or use the synthetic shop's paid-revenue question consistently for an MCP demonstration.
5. **If the goal is a full-workflow MCP, add explicit orchestration.** It should accept question, database ID, and evidence; generate and validate a graph; retrieve/rank; assemble; invoke the existing authority; and return a trace proving which stages ran and why any stage stopped. A SQL-only execution tool can remain available as a separate route.
6. **Add integration evidence before claiming equivalence.** Check graph failures, insufficient retrieval, assembly repair, valid-but-wrong business logic, and authority rejection. Improve scoped SQL validation if the product promises all invalid references are rejected before execution.

These are recommendations from the audit. No backend behavior or explanatory claims were changed as part of the formatting pass.

## Page formatting audit and changes

The audit covered the overview, four-box SQL example, architecture table, both carousel slides, both workflow columns, ranking lists, SQL assembly, authority/result containers, and closing sections. It also checked all six workflow selection buttons, toggle-off behavior, keyboard operation, read-only text state, and local link targets.

Small fixes made:

- Restored the arrow after the overview's technical-writeup link.
- Reflowed each relationship above its ranked SQL candidates on phones, removing an obsolete grid rule's practical effect that had squeezed SQL into single-character columns.
- Made locked graph positions respond to container resizing, preserving their saved proportions. Added narrow-screen sizing so nodes remain inside the panel.
- Removed narrow-screen negative panel offsets and prevented the authority pill from expanding to full page width.
- Put overview prose before its example on phones and adjusted its small-screen spacing.
- Increased small-screen algorithm text slightly; enlarged carousel controls for coarse pointers.
- Restored a keyboard-only focus indicator, preserved button-style pointer behavior, and synchronized label-background transitions with the graph panel.
- Honored reduced-motion preferences for the workflow highlight transitions.

The two-column workflow now stacks below **1,360 CSS pixels**, rather than 1,100. The fixed diagram widths plus their desktop offsets were clipping in that intermediate range; stacking earlier keeps them readable. The established wide-screen arrangement, colors, large section breaks, and selected-state behavior remain intact.

Six viewport settings were checked, from a 320-pixel requested browser width through 2,128 pixels. The browser's existing zoom makes its reported CSS viewport widths differ from those requested settings. Final DOM measurements found **no main-content elements extending past the viewport** at those sizes. Both carousel pages worked; all six buttons activated and toggled off without text selection; text editing remained disabled; all three relative link targets existed. `git diff --check` also passed. This is a visual/interaction pass, not an exhaustive accessibility certification or a cross-browser test matrix.

### Saved browser text versus repository text

The local page still restores earlier edits from browser storage even though editing is disabled. Some visible wording therefore differs from the source defaults: for example, the browser shows “How the intent model was created:” while the repository default says “How the semantic model was developed.” This audit considered both the rendered page and the source.

A Git push publishes repository files; it does not publish that browser's stored drafts. The formatting pass preserved those drafts. Before a final public-copy review, reconcile the saved wording with the source so a fresh visitor sees the intended version.
