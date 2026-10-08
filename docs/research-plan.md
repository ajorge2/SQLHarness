# SQLHarness research plan

## Question

Can an explicit semantic compiler—intent graph, SQL-fragment retrieval, and lightweight assembly—move the execution-accuracy versus cost and latency frontier relative to direct frontier-model SQL generation?

## Hypothesis

The structured system should help most when a request combines several interacting constraints that are individually familiar but difficult to compose reliably. Its advantage should come from exposing intermediate decisions, retrieving schema-grounded primitives, and correcting recurring failure modes with targeted supervision rather than longer prompts.

## Controlled comparison

All systems receive the same frozen BIRD examples, database schema, task evidence, execution limits, and correctness evaluator.

The first governed comparison uses the canonical SQLite Mini-Dev release's single-statement, SELECT-only examples. Newer Mini-Dev material includes CRUD operations, but SQLHarness's initial authority boundary is read-only; mutation workflows require a separate reversible-state benchmark rather than counting deliberate policy rejection as model failure.

| Arm | System | Purpose |
|---|---|---|
| A | Direct pinned frontier model | Establish the strongest simple baseline |
| B | Intent graph + fragment retrieval + lightweight assembler | Test the complete SQLHarness hypothesis |
| C1 | SQLHarness without intent graph | Measure the parser's contribution |
| C2 | SQLHarness without fragment retrieval | Measure retrieval's contribution |
| C3 | SQLHarness with frontier assembler | Separate representation gains from small-model limits |

## Outcomes

- **Primary:** official BIRD execution accuracy
- **Efficiency:** total model input/output tokens, estimated API cost, and cost per correct query
- **Operations:** end-to-end latency and per-stage latency
- **Reliability:** validation rejection, execution failure, recovery, and abstention rates
- **Diagnosis:** intent-parsing, retrieval, assembly, schema-linking, and execution error counts

## Guardrails against a misleading result

- Freeze examples and prompts before the final comparison.
- Pin exact model identifiers and decoding parameters.
- Persist hashes for the dataset, selected examples, database files, prompt, and source tree before inference.
- Keep the final test split untouched during development.
- Report uncertainty and paired per-example differences, not only aggregate point estimates.
- Publish unsuccessful ablations and the cases where direct generation is better.
- Treat local result comparison as development feedback; use the official BIRD evaluator for final reported results.
- Report local-comparator coverage separately; a timed-out or truncated gold query is unscored, never automatically counted as a model error.

## Completed work

The provider-neutral baseline runner, OpenAI API and Codex CLI adapters, AST/schema validator, bounded read-only SQLite executor, trace format, and offline tests are implemented. A five-query Codex CLI development pilot exercised the live path: 4/5 queries were locally correct and all five produced valid, executable SQL. The v0.2 intent contract has also been revised through a 25-example representational audit spanning every BIRD database and 27 SQL demands.

The first end-to-end held-out slice is now measured. Seven development examples produced 48 parameterized fragments; the remaining three examples were run through both direct generation and the graph-plus-retrieval pipeline. Both scored 2/3. SQLHarness answered two queries correctly and abstained after an intent-parser timeout on the third, but required substantially more latency and reported tokens. The failed direct case also exposed conflicting supervision between the question and gold SQL (`COUNT >= 2`) and supplied evidence (`COUNT > 2`). See [the vertical-slice report](vertical-slice.md).

Model B is now evaluated independently of assembly. Gold SQL is decomposed into schema-independent parameterized fragment signatures, making catalog coverage and Recall@k directly measurable. The seven-example catalog covers all broad operation kinds but only 43.75% of exact held-out structures. Across the two examples with valid graphs, the lexical control reaches 12.5% strict micro Recall@12 and 33.33% catalog-conditional Recall@12. See [the retrieval evaluation](fragment-retrieval-evaluation.md).

A frozen 20-train/5-held-out comparison measures lexical, local BGE-small, and a task-specific learned reranker. Dense retrieval reaches 23.08% strict micro Recall@3 versus 15.38% for lexical and learned retrieval. The learned model improves Recall@1 to 15.38%, but drops to 15.38% at Recall@12; it does not beat the generic dense encoder overall. Exact catalog coverage is 58.82%, four of five graphs are available, and three queries contribute to conditional ranking metrics.

The frozen end-to-end comparison is also complete. Direct GPT-6 Astra scores 4/5; SQLHarness with either dense or learned retrieval scores 3/5 and abstains on one parser timeout. The structured arms are roughly an order of magnitude slower by the recorded latency fields and consume more reported model tokens even though the timed-out parser returns no usage. The pinned official BIRD per-query executor reproduces the 80% versus 60% scores. See [the final results](final-results.md).

The development study therefore rejects its initial performance hypothesis at this scale. Its engineering contribution—the shared MCP/database authority, deterministic policy receipts, bounded recovery, traces, and offline tests—is complete. Future research should focus on parser distillation and structural catalog coverage rather than claiming the existing system has moved the frontier.
