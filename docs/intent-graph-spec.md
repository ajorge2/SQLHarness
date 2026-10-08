# Intent graph contract v0.2

The intent graph is SQLHarness's interface between language understanding and SQL-fragment retrieval. It is deliberately narrower than general-purpose AMR: every concept must help explain or construct the requested database operation without merely copying a SQL AST.

Version 0.2 is the first contract revised against a frozen, diverse BIRD Mini-Dev sample. The audit covered 25 questions, all 11 databases, all three difficulty levels, and 27 SQL demands. The selection and findings are documented in [`intent-contract-audit.md`](intent-contract-audit.md).

## Design requirements

1. **Phrase- or evidence-grounded:** explicit meanings point to exact character spans in either the request or supplied evidence.
2. **Honest about inference:** a non-output concept without a source span must carry `attributes.inferred: true`.
3. **Schema-aware but not prematurely committed:** a node may retain several ranked schema candidates until retrieval or assembly resolves the choice.
4. **Compositional:** edges capture local semantic relationships, including Boolean operands, arithmetic parts, grouping, ranking, and scope.
5. **SQL-independent:** concepts describe intent (`count`, `percentage`, `argmax`, `or`) rather than SQL clauses or AST nodes.
6. **Machine-checkable:** the representation is versioned and validated before becoming retrieval input.

## Node types

| Kind | Meaning | Examples |
|---|---|---|
| `entity` | A set of real-world or database objects | customer, order, product |
| `attribute` | A dimension or property | region, order date, revenue |
| `value` | A literal or referenced value | 2025, Northeast, $100 |
| `operation` | A compositional transformation or reduction | count, average, percentage, argmax |
| `condition` | An atomic predicate or comparison | greater than 20, between two dates |
| `logic` | Composition or negation of conditions | and, or, not |
| `relation` | A semantic relationship that may require a join | customer purchased item, hero published by company |
| `scope` | The semantic boundary of a nested computation | comparison population, per-group ranking |
| `output` | The requested answer projection | returned region and count |

Each node may contain source spans, ranked schema candidates, and typed attributes such as `distinct`, `limit`, `tie_policy`, or `inferred`.

## Grounding

Every source span specifies `source: request` or `source: evidence` plus exact character offsets and text. The validator checks the span against the corresponding string. Output and scope nodes may be structural and therefore ungrounded. Any other ungrounded node must explicitly declare that it was inferred.

This separates three claims that should not be conflated:

- the user literally expressed a meaning;
- supplied evidence expressed or clarified it;
- the parser inferred it from schema or task structure.

## Edge roles

The original roles remain: `theme`, `attribute`, `value`, `source`, `target`, `group_by`, `filter`, `compare`, `measure`, `order_by`, `constrained_by`, and `returns`.

Version 0.2 adds:

- `operand` for Boolean composition;
- `numerator` and `denominator` for ratios and percentages;
- `member_of` for set membership;
- `joined_by` for semantic relationships;
- `scoped_to` for nested computations;
- `optional` for requested values that may be absent;
- `tie_breaker` for ranking semantics not captured by the primary measure.

Edges are directed and role-typed. For example, `entity → attribute`, `relation → source/target entity`, `logic → operand`, and `output → returns` are valid; reversing those edges is not an equivalent graph. The validator enforces the high-confidence role signatures so superficially well-formed graphs cannot silently change the representation convention between examples.

## Worked example

For “Which region has the most customers?” the graph contains:

- a `region` attribute grounded in “region”;
- a `customer` entity grounded in “customers”;
- a `count` operation whose theme is the customer entity and whose grouping attribute is region;
- an `argmax` operation grounded in “most” whose measure is the customer count;
- an output node that returns region under the `argmax` constraint.

The machine-readable example is [`examples/intent_graph_region.json`](../examples/intent_graph_region.json). The implementation rejects unsupported versions, duplicate nodes or edges, invalid spans, unknown kinds or roles, unmarked implicit concepts, missing endpoints, self-edges, multiple or missing output nodes, cycles, and disconnected graphs.

## Boundary with Model B

Model B does not translate the whole graph. It receives contextual subgraphs—for example, `count(theme=customer, group_by=region)` or `percentage(numerator=marvel_heroes, denominator=height_filtered_heroes)`—and retrieves a distribution over compatible parameterized SQL fragments. Scope and relation context prevent local phrases from being interpreted as isolated keywords. The assembler resolves dependencies and schema choices across the complete graph.

## Remaining research questions

- Which graph equivalences should count as the same semantic target during training?
- How much schema linking belongs in Model A versus the retriever?
- Should role labels remain discrete or acquire learned embeddings?
- Which inferred nodes can be checked deterministically against the schema or gold SQL?
- Does the acyclic restriction improve target consistency or exclude useful recursive semantics?

This contract establishes representational coverage and validation rules. It does not establish that a learned parser can produce correct graphs.
