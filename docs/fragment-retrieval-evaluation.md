# Fragment retrieval evaluation

## Latest controlled comparison: 20 train / 5 held out

The development split was expanded and frozen before comparing retrieval methods. The first 20 audit examples produced a 154-fragment catalog. The final five examples remained held out. Four produced valid intent graphs; three of those four had at least one exact required structure available in the catalog.

The dense arm uses the frozen `BAAI/bge-small-en-v1.5` encoder through a local quantized ONNX runtime. The learned arm fits an auditable logistic reranker over dense cosine similarity, token overlap, SQL-operator overlap, and intent/fragment-kind compatibility using 16 structurally valid training graphs. All arms receive the same intent fragments, catalog, relevance labels, and cutoffs. Repeated copies of the same parameterized SQL meaning are collapsed in the returned ranking while all wording variants remain available for scoring.

| Ranking measure | Lexical control | Dense BGE-small | Learned ranker |
|---|---:|---:|---:|
| Strict micro Recall@1 | 7.69% | 7.69% | **15.38%** |
| Strict micro Recall@3 | 15.38% | **23.08%** | 15.38% |
| Strict micro Recall@12 | **23.08%** | **23.08%** | 15.38% |
| Catalog-conditional Recall@3 | 33.33% | **50.00%** | 33.33% |
| Eligible-query Hit@3 | 66.67% | **100.00%** | 66.67% |
| Mean reciprocal rank | 0.511 | **0.667** | **0.667** |

The dense encoder does not increase the final exact-structure ceiling: lexical and dense retrieval both retrieve three of thirteen required gold signatures by rank 12. Dense retrieval does rank those useful candidates earlier, reaching the same recall by rank 3. The learned reranker moves an additional relevant structure to rank 1 but loses another relevant structure entirely from its top 12. Its largest coefficient is broad kind compatibility, evidence that the small supervision set has not yet learned sufficiently nuanced intent-to-SQL alignment.

Catalog coverage remains the larger ceiling. Across all five held-out queries, only 10 of 17 exact gold signatures exist among the 154 training fragments—58.82% structural coverage despite 100% coverage of broad SQL operation kinds. A generic sentence encoder improves candidate ordering, but cannot retrieve a SQL composition that the catalog does not contain.

This is still a small development comparison, not a benchmark conclusion. One of five intent graphs timed out, and only three examples contribute to the conditional ranking measures.

## Question

Before training an embedding retriever, can the transparent lexical control surface the SQL structures required by held-out gold queries?

This evaluation removes the final SQL assembler entirely. Each held-out gold query is decomposed into parameterized fragments such as:

- `projection|{column_1}`
- `filter|{column_1} between {value_1} and {value_2}`
- `aggregate|sum({column_1})`
- `join|{column_1} = {column_2}`

A retrieved candidate counts as a strict match only when both its fragment kind and parameterized template match a gold fragment. Schema names and literal values are therefore ignored, while the SQL operation and composition remain fixed.

## First 7-train / 3-held-out diagnostic

The original seven-example corpus contained 48 fragments. Evaluation used the same three held-out examples as the first vertical slice, although only two had usable intent graphs because the third parser call timed out. This smaller experiment established the evaluator and motivated the cleaner comparison above.

| Diagnostic | Result | Interpretation |
|---|---:|---|
| Broad SQL-kind catalog coverage | 12/12 · 100% | The corpus contains every needed operation family, such as projection, filter, join, and aggregate. |
| Exact structural catalog coverage | 7/16 · 43.75% | More than half of the held-out parameterized structures do not exist in the tiny corpus. |
| Intent-graph coverage | 2/3 · 66.67% | One held-out request cannot reach retrieval because parsing timed out. |
| Strict micro Recall@12 | 1/8 · 12.5% | Across the two evaluable graphs, retrieval surfaces one of eight required structures. |
| Catalog-conditional Recall@12 | 1/3 · 33.33% | Even when the exact structure exists in the catalog, lexical ranking finds only one of three. |
| Broad SQL-kind Recall@12 | 4/6 · 66.67% | The retriever often finds the right family while missing the right composition. |

## Per-example diagnosis

### Example 117 — percentage of fully paid loan amount

The gold query needs conditional summation, ordinary summation, and a ratio projection. None of those exact structures exists in the seven-example corpus. Retrieval returns broadly related aggregates and filters, but exact structural recall is zero. This is principally a **catalog breadth failure**, not something an improved ranking model can solve against the current corpus.

### Example 707 — highest-scoring comment within a post-view range

Three of five exact gold structures exist in the catalog: a `BETWEEN` filter, a projection, and a limit. Retrieval finds only the `BETWEEN` fragment. It misses the available projection and limit while returning semantically plausible alternatives such as a descending window rank. This is a genuine **ranking and representation failure**.

### Example 1239 — repeated high hematocrit examinations

Four of eight exact structures exist in the catalog, but no intent graph is available because parsing timed out. The retrieval stage is therefore unscored for this example. This remains an **upstream graph-availability failure**.

## What the result means

The first independent Model B test separates three problems that end-to-end accuracy had collapsed together:

1. **Corpus coverage:** the system needs more structural primitives than seven examples provide.
2. **Retrieval quality:** lexical similarity does not reliably connect semantic intent to the correct available SQL composition.
3. **Parser availability:** retrieval cannot help when no graph reaches it.

The learned Model B iteration confirms that gold-derived alignment is trainable but underpowered here: it changes ranking behavior without improving end-to-end correctness or beating the generic dense retriever overall. Catalog coverage and conditional recall remain separate so adding more fragments cannot be mistaken for better ranking.

## Scope limitation

This is pooled structural candidate recall. It does not yet judge whether each candidate was retrieved for the exact intent node that should consume it, whether the assembler used it, or whether the final SQL executed correctly. Those are separate downstream evaluations.
