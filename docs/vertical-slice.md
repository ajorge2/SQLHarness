# First held-out SQLHarness vertical slice

## Result

The first complete development comparison is a tie on end-to-end correctness: both direct generation and SQLHarness answered **2 of 3** held-out BIRD examples correctly.

That does **not** mean the structured system is already competitive. SQLHarness answered only two examples, took much longer, and used more reported inference tokens on those two completed pipelines than direct generation used on all three. Its third case ended in a parser timeout rather than an incorrect SQL answer.

| Measure | Direct model | SQLHarness v0.1 |
|---|---:|---:|
| Held-out execution accuracy | 2/3 | 2/3 |
| Queries answered | 3/3 | 2/3 |
| Accuracy when answered | 2/3 | 2/2 |
| Abstentions | 0 | 1 parser timeout |
| Mean model/pipeline latency | 6.35 s | 46.19 s on completed pipelines |
| Reported tokens | 45,546 across all 3 | 70,197 across 2 completed pipelines |

These three examples form a development slice, not a benchmark. The token totals are also not perfectly symmetric: Codex CLI includes its runtime context, and the timed-out SQLHarness parser returned no usage record.

## What was actually built

Seven BIRD training examples were converted into 48 parameterized SQL fragments. A transparent lexical retriever was deliberately used as the first control, so later embedding retrieval has something concrete to beat.

For each held-out question, the current pipeline:

1. generates and validates a task-oriented intent graph;
2. serializes local graph meaning into retrieval queries;
3. retrieves parameterized SQL fragments without exposing the training queries' concrete identifiers;
4. asks the assembler to compose a candidate using the graph, schema, and retrieved primitives;
5. validates the SQL AST and schema references;
6. executes it inside the bounded read-only harness; and
7. compares its result with the gold query's result.

## Per-example behavior

- **117 — financial:** both systems produced the same correct conditional-aggregation query.
- **707 — Stack Exchange:** both systems correctly composed a filtered maximum over joined posts and comments. SQLHarness expressed the intermediate population as a CTE.
- **1239 — thrombosis prediction:** direct generation returned a valid but gold-mismatching query; SQLHarness's intent parser timed out and abstained.

The third case uncovered an evaluation issue worth tracking. The natural-language question asks for patients with “two or more” qualifying examinations and the gold SQL uses `COUNT >= 2`, but BIRD's supplied evidence states `COUNT > 2`. The direct model followed that evidence and omitted the patient with exactly two qualifying records. This should be classified as a supervision conflict, not treated as an ordinary clean model error.

## What this changes next

The project now has a real measured bottleneck: explicit parsing is expensive, and the first retriever is only a lexical control. The next iteration must earn the extra structure rather than merely demonstrate it. The most informative next steps are to:

- cache or replace expensive teacher-generated graphs with a smaller trained parser;
- compare lexical retrieval against an embedding retriever on fragment recall;
- define confidence-based abstention separately from timeout failure; and
- expand the frozen development set before making any architectural conclusion.

The main value of this slice is that the research question is now executable and falsifiable. It already shows where the proposed architecture fails, how that failure differs from direct generation, and which measurement should drive the next design decision.

## Model B isolated

The follow-up [fragment retrieval evaluation](fragment-retrieval-evaluation.md) removes SQL assembly and derives relevance directly from held-out gold SQL. The seven-example catalog covers every broad SQL operation family needed by the three examples, but only 7 of 16 exact parameterized structures. For the two examples with usable graphs, the lexical control retrieves 1 of 8 required structures by rank 12, including only 1 of the 3 exact structures that were available in the catalog.

This shows two independent constraints: the corpus is too small, and lexical ranking is weak even when the answer exists. Future embedding retrieval should be compared using the same fixed relevance definition rather than only through final execution accuracy.
