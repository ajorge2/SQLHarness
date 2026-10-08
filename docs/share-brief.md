# SQLHarness: project context

SQLHarness is an Applied AI engineering and NLP research project investigating whether explicit semantic structure can improve natural-language-to-SQL systems over a direct frontier-LLM call.

## Core question

Can a system externalize the model's interpretation of a business request into a task-oriented intent graph, connect pieces of that graph to reusable SQL primitives, and use a lightweight model to assemble the final query—while preserving or improving execution accuracy and reducing cost and latency?

The project is not premised on the structured system automatically winning. Its purpose is to measure where explicit structure helps, where direct generation remains better, and which component causes each failure.

## Intended architecture

1. **Input:** a natural-language business question, database schema, and optional task evidence.
2. **Model A — intent parser:** converts the request into a task-specific semantic graph containing entities, operations, filters, comparisons, aggregation, ordering, and relationships. This is AMR-inspired but optimized for SQL-relevant intent rather than general linguistic coverage.
3. **Model B — fragment retriever:** embeds contextual pieces of the intent graph and retrieves parameterized SQL primitives. It maps local semantic meaning to possible SQL realizations rather than translating the entire graph at once.
4. **Lightweight assembler:** combines the graph, retrieved fragments, and schema into one executable SQL proposal.
5. **Governed execution boundary:** parses the SQL AST, checks schema references and read-only policy, applies time and row limits, and executes only allowed queries. The implemented MCP server owns this authority rather than merely wrapping an unrestricted database client.
6. **Evaluation:** compares executed results with gold answers and records accuracy, validation decisions, failure stage, latency, token usage, and cost.

## Training intuition

The first learning phase repeatedly samples a capable teacher model on unlabeled training inputs. The goal is to observe the teacher's current solution space: the alternative semantic decompositions and SQL patterns it associates with similar requests.

Those samples bootstrap two learnable relationships:

- natural language plus schema → task-oriented intent graph;
- contextual intent fragment → distribution over SQL fragments.

The gold training pairs then correct the teacher-inherited behavior. The current working plan is to use gold data first to improve fragment selection, then obtain SQL-consistent graph targets for the gold pairs, and finally use those targets to improve the intent parser. The exact graph induction and supervision procedure remains a research decision to validate, not a completed claim.

Free-form chain-of-thought is not treated as ground truth. Any teacher-generated semantic representation must follow a constrained schema and be checked against the generated SQL and database schema.

## Evaluation design

The principal benchmark is BIRD-SQL. Every system arm receives the same frozen question, evidence, database schema, execution limits, and evaluator.

- **Arm A:** direct, pinned frontier-model generation.
- **Arm B:** complete SQLHarness pipeline.
- **Ablations:** remove the intent graph, remove fragment retrieval, and vary the final assembler so the contribution of each component can be isolated.

Primary outcome: official BIRD execution accuracy.

Secondary outcomes: cost per correct query, total model tokens, end-to-end and per-stage latency, validation rejection rate, execution failure rate, abstention rate, and an error taxonomy covering intent parsing, schema linking, retrieval, assembly, and execution.

The untouched test set is reserved for the final comparison. Development uses training data and a separate validation split. Published BIRD claims will use the official evaluator rather than only the project's local comparator.

## What is implemented now

- BIRD-format JSON and JSONL loading.
- SQLite schema introspection.
- A provider-neutral SQL generation interface.
- A structured OpenAI Responses API baseline adapter.
- A separate ephemeral, read-only Codex CLI adapter for development runs without an API key.
- SQLGlot AST parsing, read-only enforcement, and schema checks.
- Read-only SQLite execution with time and row limits.
- Candidate-versus-gold execution-result comparison.
- Per-example JSONL traces and aggregate run summaries.
- Offline automated tests and deterministic, no-key showcase fixtures.
- A browser trace inspector showing both an accepted read and a rejected destructive proposal.
- A v0.2 phrase- and evidence-grounded intent-graph contract, revised against 25 diverse BIRD questions spanning all 11 databases and 27 SQL demands.
- Directed role-signature validation, exact schema-candidate checks, unique-span repair with raw-versus-repaired reporting, and bounded graph-generation timeouts.
- A five-example live intent-generation pilot that exposed edge-direction inconsistency and complexity-driven latency rather than hiding those failures.
- A separate five-dimension human rubric for request coverage, operator correctness, scope attachment, output fidelity, and schema grounding; the first diagnostic review produced three strict passes and flagged one possible BIRD annotation issue.
- A frozen Arm A preflight that fingerprints the 500-example dataset, 11 databases, prompt, source tree, environment, model settings, pricing snapshot, and official evaluator revision before inference.
- A five-query Codex CLI smoke test: 4/5 locally correct, 5/5 valid and executable, 6.34-second mean model latency, and 75,206 CLI-reported tokens. This is explicitly labeled as diagnostic evidence rather than a benchmark result.
- A first held-out end-to-end slice: seven development examples yielded 48 parameterized fragments, and three held-out examples compared direct generation with the intent-graph/retrieval/assembly path. Both scored 2/3. SQLHarness answered two correctly and abstained on one parser timeout, but was materially slower and used more reported inference tokens. The result is preserved as a diagnostic, not framed as a win.
- A concrete benchmark-quality finding from that slice: one direct error followed BIRD's supplied `COUNT > 2` evidence, while the question and gold SQL specify “two or more” / `COUNT >= 2`. The project records that case as conflicting supervision rather than silently calling it a clean model failure.
- An assembler-independent retrieval evaluator that extracts parameterized relevance targets from held-out gold SQL and reports catalog coverage, strict Recall@k, catalog-conditional Recall@k, and graph availability separately. The first three-example diagnostic finds 100% broad operation-kind coverage, 43.75% exact structural catalog coverage, and 12.5% strict micro Recall@12 on the two usable graphs (33.33% conditioned on the exact structure existing in the corpus).
- A frozen 20-train/5-held-out lexical/dense/learned retrieval comparison. BGE-small reaches 23.08% strict micro Recall@3 versus 15.38% for lexical and learned retrieval. The learned reranker raises Recall@1 to 15.38% but loses a relevant structure by rank 12, making the small-data failure visible rather than selecting it away.
- Repeated-teacher analysis: among two examples with multiple valid graphs, mean node-signature Jaccard is 0.472 and edge-signature Jaccard is only 0.102. Teacher graphs are therefore treated as a variable distribution rather than unquestioned labels.
- A real MCP v2 server with five typed tools backed by the same `DatabaseAuthority` used in evaluation. An in-memory client test proves that mutation is blocked before contact while an allowed read succeeds.
- A bounded one-retry correction path driven only by validator or database errors, plus explicit abstention.
- A final frozen five-example comparison reproduced by the pinned BIRD per-query executor: direct GPT-6 Astra scores 4/5, while SQLHarness with either dense or learned retrieval scores 3/5. The result rejects the performance hypothesis at this scale.

The offline showcase proves that the evaluation and policy paths execute. It is deliberately labeled as a fixture and is not presented as evidence of model quality.

## Study conclusion

The development study and governed execution system are complete. The direct call wins this slice. Explicit structure currently contributes inspectability, failure localization, and governed execution—not a better accuracy–latency–token frontier.

Future research is deliberately narrower: distill Model A so graph construction no longer requires a frontier-model call, expand exact SQL-fragment catalog coverage beyond 58.82%, and train fragment alignment on substantially more than 16 usable graphs. A full production-API BIRD run remains a separate benchmark-scale follow-on, not unfinished evidence hidden behind a resume claim.

## Portfolio intent

The same repository deliberately supports two readings. The research lens asks whether explicit semantic representations improve compositional language understanding. The Applied AI engineering lens demonstrates reproducible evaluation, model routing, structured intermediate state, safety policy, bounded execution, tracing, and honest measurement.

No benchmark-scale accuracy, cost-reduction, or latency-improvement claim is made from the five-example slice. Its measured loss is reported precisely because the current structured pipeline has not earned its additional inference cost.
