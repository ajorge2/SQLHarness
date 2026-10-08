# Intent-contract audit

## Purpose

This audit asks whether SQLHarness's intent representation can express the semantic decisions demanded by real BIRD questions before Model A is trained. It is a representational audit, not a parsing-accuracy result.

## Frozen sample

The deterministic selector chose 25 BIRD Mini-Dev examples spanning:

- all 11 databases;
- 8 challenging, 10 moderate, and 7 simple questions;
- 27 observed SQL demands, including joins, outer joins, nested queries, CTEs, windows, set operations, conditional aggregation, ratios, grouping, ranking, optional outputs, and temporal transformations.

The selector rewards new SQL demands, then balances databases and difficulty levels while penalizing repeatedly selected feature profiles. The frozen sample is stored as `artifacts/intent-contract-audit-25.json` when generated locally.

## What v0.1 exposed

| Pressure from real questions | Representative BIRD IDs | Why v0.1 was inadequate | v0.2 response |
|---|---:|---|---|
| `OR`, negation, and set exclusion | 27, 529, 1323 | One generic condition node could not preserve how predicates compose. | `logic` nodes and `operand` edges |
| Ratios and derived measures | 760, 788, 1471 | A generic operation hid numerator, denominator, and comparison population. | `numerator`, `denominator`, and `scoped_to` edges |
| Nested populations and ranking | 1014, 1116, 1239, 1498 | Local meanings could be correct while attached to the wrong query level. | explicit `scope` nodes and ranking attributes |
| Optional projections | 27 | “If there is any” changes missing-value and join behavior but had no representation. | `optional` edges |
| Evidence-supplied semantics | multiple BIRD examples | Spans could only point into the question even when BIRD evidence defined the operation. | request/evidence source channels |
| Schema-implied relationships | 1014, 1239 | Required joins and transformations may be absent from the wording, making fake phrase grounding tempting. | `relation` nodes plus required `inferred` markers |

## What the audit does and does not prove

The revised contract can now represent every semantic-demand family observed in the 25-example sample without introducing nodes named after SQL clauses. The validator also prevents disconnected or silently ungrounded structures.

It does **not** yet prove:

- that one graph is the unique correct interpretation;
- that a teacher model will produce consistent graphs;
- that Model A can learn the representation;
- that the representation improves SQL execution accuracy.

The next test is empirical: generate candidate v0.2 graphs for the frozen sample, measure structural validity and semantic consistency, and catalog disagreements before creating training targets.

## First generation pilot

A five-example Codex CLI pilot produced a graph for every request and preserved all five input/evidence pairs exactly. Under the initial structural checks, four graphs passed directly and the most complex graph passed after five uniquely resolvable span-offset repairs.

A cross-graph read then found inconsistent edge direction in three graphs. After adding directed role signatures to the contract:

- 2/5 original graphs passed the stricter contract;
- the three failures were retried with explicit direction conventions;
- two retries completed and both passed the contract and exact schema-candidate checks;
- the complex Formula 1 retry exceeded the five-minute generation bound.

This is useful negative evidence. It shows that output-schema validity alone overstates graph consistency, that role typing catches a real teacher failure mode, and that semantic graph generation latency can become impractical on complex schemas. Future runs use a 120-second bound and retain timeouts as explicit failures.

Contract validity still does not imply semantic correctness. Applying the separate [`semantic-review-rubric.md`](semantic-review-rubric.md) produced three strict passes in the five-example diagnostic set. The two failures exposed different problems: one changed projection and scope, while the other failed to represent nonexistence across related records. The latter also flagged a possible defect in the benchmark's gold SQL.
