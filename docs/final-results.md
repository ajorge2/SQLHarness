# Frozen development comparison

## Result

On the frozen 20-train / 5-held-out BIRD Mini-Dev slice, direct GPT-6 Astra generation scored **4/5 (80%)**. SQLHarness scored **3/5 (60%)** with both the generic BGE-small retriever and the task-specific learned ranker. The pinned BIRD per-query execution evaluator at commit `abd11b6db92a1c9f809b32f7564c7c71b34d67f0` reproduced all three scores.

This is a useful negative result: the current structured system does not beat the direct call.

| Arm | Correct | Latency | Reported model tokens | Important failure |
|---|---:|---:|---:|---|
| Direct GPT-6 Astra | 4/5 | 5.61 s mean model latency | 77,327 across five | One result mismatch |
| SQLHarness + BGE-small | 3/5 | 67.99 s mean observed end-to-end | 142,809 across four completed pipelines | One parser abstention; one result mismatch |
| SQLHarness + learned ranker | 3/5 | 67.23 s mean observed end-to-end | 142,764 across four completed pipelines | Same two failures |

The SQLHarness token totals exclude the timed-out parser because the CLI returned no usage for it. They therefore understate the structured arm's true consumption. Latency is also not perfectly symmetric: the direct figure is provider generation latency, while the SQLHarness figure combines recorded parser and assembler latency. Cost is not fabricated because the authenticated Codex CLI is not an API billing surface.

## What the components taught us

### Intent parser

Four of five held-out requests produced usable graphs. The remaining request timed out at the fixed 120-second evaluation limit and remained unavailable even in a separate 240-second diagnostic retry. That single parser failure reduces maximum end-to-end accuracy on the slice to 80% before retrieval or assembly is considered.

Repeated teacher sampling also shows that a legal graph is not a stable graph. Across the two repeated examples with multiple valid samples, mean node-signature Jaccard similarity was **0.472**, while mean edge-signature Jaccard was only **0.102**. The teacher tends to preserve broad concepts more consistently than their exact relational structure. This supports treating teacher graphs as a distribution to refine, not as unquestioned labels.

### Fragment catalog and retrieval

The 20-example corpus contains 154 extracted fragments but covers only **58.82%** of the 17 exact held-out SQL signatures. On the four graph-evaluable queries, only 6 of 13 required exact signatures exist in the catalog. No ranker can retrieve structures that were never extracted, so catalog expansion is the first ceiling.

After duplicate SQL meanings are collapsed in the returned ranking:

| Retriever | Recall@1 | Recall@3 | Recall@12 | MRR |
|---|---:|---:|---:|---:|
| Lexical control | 7.69% | 15.38% | 23.08% | 0.511 |
| BGE-small dense | 7.69% | **23.08%** | **23.08%** | **0.667** |
| Learned linear ranker | **15.38%** | 15.38% | 15.38% | **0.667** |

The learned ranker moved an additional relevant structure to rank 1, but lost a different relevant structure by rank 12. Its strongest learned weight was broad intent/fragment-kind compatibility, indicating that 16 usable training graphs were insufficient for robust fine-grained ranking. This ablation is preserved rather than selected away.

### Assembly and execution

Among the four requests that reached assembly, both structured arms answered three correctly. The task-specific ranker changed several retrieved candidates and SQL surface forms but did not change final correctness. All generated proposals crossed the same `DatabaseAuthority` used by the MCP server: SQLGlot validation, schema checks, read-only SQLite, deadline, row cap, and a deterministic decision receipt. No repair call was needed in this slice.

## Research conclusion

Explicit semantic structure improves inspectability more clearly than accuracy at this scale. The experiment identifies three concrete next hypotheses:

1. Distill the intent parser so graph construction no longer requires a slower frontier-model call.
2. Increase structural catalog coverage before optimizing ranking further.
3. Train on graph-to-fragment alignments with more than 16 usable examples; broad type compatibility currently overwhelms nuanced semantic matching.

The project is complete as a reproducible development study and governed execution system. It is not presented as evidence that SQLHarness beats direct frontier generation, nor as a full BIRD leaderboard result.
