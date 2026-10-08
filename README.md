# SQLHarness

SQLHarness tests whether an explicit semantic pipeline can move the accuracy-cost frontier for natural-language-to-SQL generation.

> **Project status:** complete reproducible development study and governed execution system. On a frozen 20-train / 5-held-out BIRD Mini-Dev slice, direct GPT-6 Astra scored 4/5 while SQLHarness scored 3/5 with either generic dense retrieval or its learned ranker. The structured path exposed exactly where it lost—a parser timeout and a semantic result mismatch—but did not improve accuracy, latency, or token use. This is five-example development evidence, not a leaderboard claim.

The intended system is:

```text
natural-language request
  -> intent-graph parser
  -> graph-conditioned SQL-fragment retrieval
  -> lightweight SQL assembler
  -> governed MCP database boundary
  -> validation, bounded execution, and evaluation
```

The first implemented slice is the shared evaluation foundation. It runs a direct-model baseline against BIRD-format examples and records enough evidence to compare every later architecture against the same standard.

## Explore the project

The repository presents the same architecture through two connected lenses:

- **Applied AI engineering:** inspect a generated proposal crossing AST/schema policy checks into bounded, read-only execution.
- **Research:** inspect the hypothesis, controlled comparison, ablations, metrics, and measured error decomposition.

Build the deterministic showcase data and open the static project page without an API key:

```bash
uv run python scripts/build_showcase.py
python3 -m http.server 8000 -d docs
```

Then visit `http://localhost:8000`. The cached examples exercise the real harness code, but are explicitly fixtures—not BIRD performance evidence.

Supporting artifacts:

- [`docs/share.html`](docs/share.html) — browser-ready, one-click-copy context for an AI reviewer
- [`docs/share-brief.md`](docs/share-brief.md) — the same self-contained context as portable Markdown
- [`docs/final-results.md`](docs/final-results.md) — frozen direct/dense/learned comparison and error decomposition
- [`docs/research-plan.md`](docs/research-plan.md) — hypothesis, comparison arms, outcomes, and validity guardrails
- [`docs/vertical-slice.md`](docs/vertical-slice.md) — the first direct-versus-SQLHarness result, failure analysis, and next experimental target
- [`docs/fragment-retrieval-evaluation.md`](docs/fragment-retrieval-evaluation.md) — gold-derived catalog coverage and Recall@k for the lexical retrieval control
- [`docs/intent-graph-spec.md`](docs/intent-graph-spec.md) — the versioned interface between language understanding and fragment retrieval
- [`docs/intent-contract-audit.md`](docs/intent-contract-audit.md) — the frozen BIRD sample, contract gaps, and first generation findings
- [`docs/semantic-review-rubric.md`](docs/semantic-review-rubric.md) — a strict human rubric separating legal graphs from correct interpretations
- [`docs/safety-model.md`](docs/safety-model.md) — implemented controls and MCP authority boundary
- [`docs/demo-script.md`](docs/demo-script.md) — a concise walkthrough for the eventual project video
- [`docs/architecture.md`](docs/architecture.md) — current system architecture

## What exists now

- BIRD JSON/JSONL loading
- SQLite schema introspection
- A provider-neutral SQL generation interface
- An OpenAI Responses API baseline adapter
- A separately labeled, ephemeral Codex CLI adapter for development runs without an API key
- Read-only SQL AST and schema validation with SQLGlot
- Read-only SQLite execution with time and row limits
- Candidate-versus-gold execution-result comparison
- Per-example JSONL traces and an aggregate JSON summary
- A no-network test suite with a deterministic fake model
- A no-key, GitHub-Pages-ready trace inspector generated from the real harness
- A BIRD-audited v0.2 intent-graph contract with evidence grounding, explicit scope, and a machine-checkable example
- Deterministic SQL-fragment extraction, parameterized templates, local intent-fragment serialization, and a transparent lexical retrieval control
- A complete graph → fragment retrieval → model assembly → validation → bounded execution path
- A three-example held-out vertical slice with per-stage latency, token accounting, abstention, and direct-model comparison
- Local BGE-small retrieval and an auditable four-feature learned logistic reranker trained on gold-derived intent-to-fragment labels
- Repeated-teacher graph-variability analysis rather than treating a single generated graph as ground truth
- A real MCP v2 server exposing five governed database tools through the same authority used by evaluation
- One bounded validator/database-error repair attempt, with abstention when no safe query is available
- A frozen five-example direct/dense/learned comparison reproduced by the pinned BIRD per-query executor

## Quick start

```bash
uv sync --extra dev --extra retrieval --extra mcp
uv run pytest
```

Run a baseline after downloading BIRD Mini-Dev and setting `OPENAI_API_KEY`:

```bash
uv run sqlharness baseline \
  --dataset /path/to/mini_dev_sqlite.json \
  --database-root /path/to/dev_databases \
  --model YOUR_PINNED_MODEL_ID \
  --output artifacts/direct-baseline.jsonl \
  --limit 25 \
  --dry-run

# Inspect the generated manifest, then remove --dry-run to make paid calls.
uv run sqlharness baseline \
  --dataset /path/to/mini_dev_sqlite.json \
  --database-root /path/to/dev_databases \
  --model YOUR_PINNED_MODEL_ID \
  --output artifacts/direct-baseline.jsonl \
  --limit 25
```

For a temporary development run through an authenticated Codex CLI instead:

```bash
uv run sqlharness baseline \
  --dataset data/bird/mini_dev_sqlite.json \
  --database-root data/bird/minidev/MINIDEV/dev_databases \
  --provider codex-cli \
  --model gpt-6-astra \
  --reasoning-effort medium \
  --output artifacts/codex-cli-pilot.jsonl \
  --limit 5
```

The CLI path records CLI-reported tokens and latency, but deliberately leaves estimated API cost blank. Codex adds its own runtime context and consumes ChatGPT-plan usage, so this result is not interchangeable with the production API baseline.

Build the first fragment corpus and run the held-out vertical slice:

```bash
uv run sqlharness build-fragment-corpus \
  --sample artifacts/intent-contract-audit-25.json \
  --output artifacts/fragment-corpus-train-7.json \
  --train-size 7 \
  --overwrite

uv run sqlharness run-vertical-slice \
  --sample artifacts/intent-contract-audit-25.json \
  --graph-trace artifacts/vertical-slice-eval-graphs-3.jsonl \
  --fragment-corpus artifacts/fragment-corpus-train-7.json \
  --database-root data/bird/minidev/MINIDEV/dev_databases \
  --model gpt-6-astra \
  --reasoning-effort medium \
  --offset 7 \
  --limit 3 \
  --output artifacts/vertical-slice-sqlharness-3.jsonl \
  --overwrite
```

The lexical retriever is retained as a transparent control. The repository also implements local BGE-small dense retrieval and a task-specific learned reranker.

Evaluate retrieval independently of SQL assembly:

```bash
uv run sqlharness evaluate-fragment-retrieval \
  --sample artifacts/intent-contract-audit-25.json \
  --graph-trace artifacts/vertical-slice-eval-graphs-3.jsonl \
  --fragment-corpus artifacts/fragment-corpus-train-7.json \
  --offset 7 \
  --limit 3 \
  --output artifacts/fragment-retrieval-eval-3.json \
  --overwrite
```

The first diagnostic finds 100% broad SQL-operation-family coverage but only 43.75% exact structural catalog coverage. On the two examples with usable graphs, strict micro Recall@12 is 12.5%, or 33.33% when conditioned on the required structure actually existing in the catalog. This cleanly separates missing primitives from ranking failure; it is still only a three-example development result.

For the cleaner 20-train/5-held-out comparison, install the optional local retrieval runtime and run both arms against the same frozen inputs:

```bash
uv sync --extra dev --extra retrieval

uv run sqlharness evaluate-fragment-retrieval \
  --sample artifacts/intent-contract-audit-25.json \
  --graph-trace artifacts/fragment-retrieval-eval-graphs-5.jsonl \
  --fragment-corpus artifacts/fragment-corpus-train-20.json \
  --offset 20 --limit 5 \
  --retriever lexical \
  --output artifacts/fragment-retrieval-lexical-train-20-eval-5.json

uv run sqlharness evaluate-fragment-retrieval \
  --sample artifacts/intent-contract-audit-25.json \
  --graph-trace artifacts/fragment-retrieval-eval-graphs-5.jsonl \
  --fragment-corpus artifacts/fragment-corpus-train-20.json \
  --offset 20 --limit 5 \
  --retriever fastembed \
  --embedding-model BAAI/bge-small-en-v1.5 \
  --model-cache artifacts/models/fastembed \
  --output artifacts/fragment-retrieval-bge-small-train-20-eval-5.json
```

After repeated SQL meanings are collapsed in the returned ranking, the local [FastEmbed](https://qdrant.github.io/fastembed/Getting%20Started/) arm raises strict micro Recall@3 from 15.38% to 23.08% and mean reciprocal rank from 0.511 to 0.667. The learned reranker raises Recall@1 from 7.69% to 15.38%, but falls to 15.38% at Recall@3 and Recall@12; it does not beat dense retrieval overall. The five-example comparison remains development evidence: four graphs were available and three queries had at least one exact relevant fragment in the catalog.

Train and evaluate the task-specific reranker:

```bash
uv run sqlharness train-fragment-ranker \
  --sample artifacts/intent-contract-audit-25.json \
  --graph-trace artifacts/intent-graph-generation-pilot-5.jsonl \
  --graph-trace artifacts/intent-graphs-train-20-missing.jsonl \
  --fragment-corpus artifacts/fragment-corpus-train-20.json \
  --output artifacts/fragment-ranker-train-20.json

uv run sqlharness evaluate-fragment-retrieval \
  --sample artifacts/intent-contract-audit-25.json \
  --graph-trace artifacts/fragment-retrieval-eval-graphs-5.jsonl \
  --fragment-corpus artifacts/fragment-corpus-train-20.json \
  --offset 20 --limit 5 \
  --retriever learned \
  --ranker-model artifacts/fragment-ranker-train-20.json \
  --output artifacts/fragment-retrieval-learned-train-20-eval-5.json
```

Serve the governed database boundary through the official MCP Python SDK:

```bash
SQLHARNESS_DATABASE_ROOT=data/bird/minidev/MINIDEV/dev_databases uv run sqlharness-mcp
```

The server exposes `list_databases`, `inspect_schema`, `validate_sql`, `explain_sql`, and `execute_readonly_sql`. It never exposes raw filesystem paths or an unrestricted database connection.

The model ID is intentionally required. Baseline results should always identify the exact model snapshot or alias used.
The preflight filters the canonical Mini-Dev release to single-statement, SELECT-only gold queries because SQLHarness's authority boundary is intentionally read-only. It fingerprints the dataset, selected examples, database files, prompt, source code, environment, and optional pricing snapshot before any model call. It also executes every gold query under the configured time and row limits, preventing an incompatible database bundle or evaluation cap from silently corrupting the comparison.

To record estimated API cost, copy `configs/pricing.example.json`, fill it from the current official pricing page, and pass `--pricing-file`. The model identifier in that snapshot must exactly match `--model`. Reasoning tokens are reported separately for analysis but are already included in output tokens and are not billed twice by the estimator.

## Evaluation contract

Every system variant receives the same question, evidence, and database schema. Each trace records:

- generated SQL
- model token usage and latency
- AST/schema validation findings
- candidate and gold execution outcomes
- execution-result correctness
- failures and abstentions

The current result comparator is a transparent local implementation for development. Published BIRD claims must also be reproduced with the benchmark's official evaluator.
If a gold query times out or exceeds the configured row cap locally, that example is recorded as unscored and excluded from local accuracy; evaluation coverage is reported beside the score.

Select the deterministic 25-example intent-contract audit sample, then run a bounded graph-generation pilot:

```bash
uv run sqlharness select-intent-audit \
  --dataset data/bird/mini_dev_sqlite.json \
  --output artifacts/intent-contract-audit-25.json \
  --size 25

uv run sqlharness audit-intent-graphs \
  --sample artifacts/intent-contract-audit-25.json \
  --database-root data/bird/minidev/MINIDEV/dev_databases \
  --model gpt-6-astra \
  --reasoning-effort medium \
  --generation-timeout-seconds 120 \
  --output artifacts/intent-graph-audit.jsonl
```

This audit reports raw contract validity, deterministic unique-span repairs, directed role validity, schema-candidate validity, input fidelity, latency, and CLI-reported tokens. It does not score semantic graph correctness without human review.

After a complete run, export the prediction, gold, and difficulty files expected by the pinned official evaluator:

```bash
uv run sqlharness export-bird \
  --trace artifacts/arm-a-gpt-6.1-sol.jsonl \
  --dataset data/bird/mini_dev_sqlite.json \
  --output-directory artifacts/arm-a-gpt-6.1-sol-official
```

## What the completed study says

The direct model wins the frozen development slice, 4/5 to 3/5. SQLHarness's value today is diagnostic and operational: its explicit graph, retrieved fragments, failure stages, authority receipts, and abstention make each decision inspectable. The experiment rejects the claim that this first structured implementation already moves the accuracy–latency–token frontier.

The evidence points to three future research targets rather than more harness decoration: distill the intent parser, expand exact structural catalog coverage beyond 58.82%, and train fragment alignment on substantially more than 16 usable graphs. See [`docs/final-results.md`](docs/final-results.md) for the frozen results and limitations.
