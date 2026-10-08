# Intent-graph semantic review rubric

Contract validation answers whether a graph is internally legal. It does not answer whether the graph means what the user asked. SQLHarness therefore keeps human semantic review as a separate evaluation layer.

## Dimensions

Each dimension receives 0, 1, or 2 points.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Request coverage | Omits a central requested meaning | Captures the main request but loses a qualifier | Captures every material request and qualifier |
| Operator correctness | Uses the wrong logical or quantitative operation | Broad operation is right but important semantics are underspecified | Operations, negation, ranking, and arithmetic match the request |
| Scope attachment | Meaning is attached to the wrong population or level | Scope is plausible but ambiguous | Every condition and operation is attached to the intended population |
| Output fidelity | Returns the wrong answer shape | Correct answer plus an unrequested field, or misses a secondary field | Requested outputs and optionality match exactly |
| Schema grounding | Central schema mapping is wrong | Mapping is valid but materially ambiguous | Candidates are valid and support the intended meaning |

A **strict semantic pass** requires 2 on every dimension. The total score remains useful diagnostically, but a high total cannot compensate for a wrong operator or output.

## Five-example pilot review

The review uses the corrected-direction retry when available; otherwise it uses the original generated graph. It is a diagnostic review, not a parser-accuracy estimate.

| BIRD ID | Coverage | Operator | Scope | Output | Schema | Verdict | Main finding |
|---:|---:|---:|---:|---:|---:|---|---|
| 27 | 2 | 2 | 2 | 2 | 2 | Pass | Preserves the `OR` filter and optional phone projection. |
| 1323 | 2 | 2 | 2 | 2 | 2 | Pass | Represents attendance threshold and fundraiser negation compositionally. |
| 1014 | 1 | 1 | 1 | 1 | 1 | Fail | Adds circuit output and per-circuit grouping where the gold task asks for the lap record; corrected retry timed out. |
| 1116 | 2 | 2 | 2 | 2 | 2 | Pass | Represents descending rank and explicitly retains all height ties. |
| 529 | 1 | 0 | 0 | 2 | 2 | Fail | Applies Korean and not-Japanese predicates to one translation record instead of modeling Korean existence and Japanese nonexistence separately. |

ID 529 also exposes a benchmark-label concern: the supplied gold SQL applies both language predicates to the same row and therefore does not cleanly implement the natural-language request. SQLHarness records this as a potential annotation issue rather than silently teaching the questionable pattern as semantic truth.

## Review protocol for the full audit

1. Hide the gold SQL during the first language-and-schema review.
2. Score the graph against the request, evidence, and schema using the five dimensions.
3. Reveal the gold SQL and record whether disagreement appears to be a graph error, valid alternative, or possible benchmark-label issue.
4. Require a second reviewer for every possible label issue and every graph considered as a training target.
5. Preserve the graph, scores, reviewer rationale, and contract-validation trace together.
