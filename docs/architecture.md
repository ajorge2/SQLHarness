# Architecture contract

SQLHarness has two inseparable goals:

1. Test whether an explicit semantic intermediate representation improves NL-to-SQL generalization.
2. Wrap probabilistic generation in a governed, observable execution system.

## Research path

```text
Repeated teacher samples
  -> text + intent graph + SQL pseudo-triples
  -> initialize Model A and fragment mappings
  -> refine mappings with gold SQL
  -> select gold-compatible latent graphs
  -> train Model A on text-to-selected-graph pairs
```

Model A is a task-oriented semantic parser that emits a serialized, AMR-inspired SQL intent graph. Model B is a graph-conditioned semantic retriever: it maps contextualized graph fragments to parameterized SQL-fragment meanings stored in a vector index. A lightweight model assembles the selected fragments into complete SQL.

## Execution path

```text
request
  -> semantic pipeline
  -> SQL candidate
  -> parse and policy validation
  -> schema validation
  -> bounded read-only execution
  -> verified result or abstention
```

The MCP server is the implemented authority boundary. It owns database resolution, tool schemas, read-only policy, timeouts, row limits, structured errors, and deterministic trace receipts. The model proposes; the boundary decides what may execute. The command-line evaluation path calls the same `DatabaseAuthority`, preventing policy drift between the demo, benchmark, and MCP surfaces.

```text
model or evaluator
  -> MCP tool / internal authority call
  -> database-id resolution inside configured root
  -> SQLGlot AST + schema validation
  -> read-only SQLite connection + deadline + row cap
  -> result or explicit blocked receipt
```

## Required ablations

- Direct frontier-model generation
- Fragment retrieval plus lightweight assembly
- Intent graph plus fragment retrieval plus lightweight assembly
- Full system with validation and bounded recovery

All variants use the same held-out examples and are compared on execution accuracy, provider-native token usage, monetary cost, end-to-end latency, and cost per correct query. Offline teacher and training costs are reported separately.
