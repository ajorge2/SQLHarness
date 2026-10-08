from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .benchmark import run_baseline
from .dataset import load_bird_examples
from .experiment import (
    PricingRates,
    build_preflight_manifest,
    select_readonly_examples,
    write_manifest,
)
from .intent_audit import select_diverse_examples, write_intent_audit_sample
from .intent_evaluation import load_intent_audit_sample, run_intent_generation_audit
from .fragments import FastEmbedFragmentRetriever, build_fragment_corpus, load_fragment_corpus
from .learned_retriever import (
    LearnedFragmentRetriever,
    LinearRankerModel,
    train_fragment_ranker,
)
from .official import export_bird_evaluator_inputs
from .providers.codex_cli import CodexCLISQLGenerator
from .providers.codex_cli_intent import CodexCLIIntentGraphGenerator
from .providers.codex_cli_assembler import CodexCLIFragmentAssembler
from .retrieval_evaluation import evaluate_fragment_retrieval
from .teacher_distribution import analyze_teacher_distribution
from .vertical_slice import load_graph_trace, run_vertical_slice
from .providers.openai import OpenAISQLGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sqlharness", description="SQLHarness benchmark harness")
    commands = parser.add_subparsers(dest="command", required=True)

    baseline = commands.add_parser("baseline", help="Run a direct-model BIRD baseline")
    baseline.add_argument("--dataset", type=Path, required=True)
    baseline.add_argument("--database-root", type=Path, required=True)
    baseline.add_argument(
        "--provider",
        choices=("openai", "codex-cli"),
        default="openai",
        help="Inference interface; codex-cli is a temporary development baseline",
    )
    baseline.add_argument("--model", required=True, help="Exact provider model ID")
    baseline.add_argument("--reasoning-effort")
    baseline.add_argument("--output", type=Path, required=True)
    baseline.add_argument("--limit", type=int)
    baseline.add_argument("--offset", type=int, default=0)
    baseline.add_argument(
        "--example-id",
        action="append",
        help="Run only the selected BIRD example ID; may be supplied more than once",
    )
    baseline.add_argument("--timeout-seconds", type=float, default=30.0)
    baseline.add_argument("--max-rows", type=int, default=100_000)
    baseline.add_argument(
        "--pricing-file",
        type=Path,
        help="JSON pricing snapshot; model ID must exactly match --model",
    )
    baseline.add_argument(
        "--manifest",
        type=Path,
        help="Defaults to OUTPUT with a .manifest.json suffix",
    )
    baseline.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and freeze the run manifest without calling a model",
    )
    baseline.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing output or manifest files",
    )

    official = commands.add_parser(
        "export-bird", help="Export a complete trace for the official BIRD evaluator"
    )
    official.add_argument("--trace", type=Path, required=True)
    official.add_argument("--dataset", type=Path, required=True)
    official.add_argument("--output-directory", type=Path, required=True)
    official.add_argument(
        "--example-id",
        action="append",
        help="Export a trace subset; examples are ordered to match the trace",
    )

    intent_audit = commands.add_parser(
        "select-intent-audit",
        help="Select a diverse BIRD sample for intent-graph contract review",
    )
    intent_audit.add_argument("--dataset", type=Path, required=True)
    intent_audit.add_argument("--output", type=Path, required=True)
    intent_audit.add_argument("--size", type=int, default=25)

    graph_audit = commands.add_parser(
        "audit-intent-graphs",
        help="Generate and structurally validate intent graphs for an audit sample",
    )
    graph_audit.add_argument("--sample", type=Path, required=True)
    graph_audit.add_argument("--database-root", type=Path, required=True)
    graph_audit.add_argument("--model", required=True)
    graph_audit.add_argument("--reasoning-effort")
    graph_audit.add_argument("--generation-timeout-seconds", type=float, default=120.0)
    graph_audit.add_argument("--output", type=Path, required=True)
    graph_audit.add_argument("--limit", type=int)
    graph_audit.add_argument(
        "--example-id",
        action="append",
        help="Run only the selected example ID; may be supplied more than once",
    )
    graph_audit.add_argument("--overwrite", action="store_true")

    fragment_corpus = commands.add_parser(
        "build-fragment-corpus",
        help="Extract parameterized SQL fragments from the training side of an audit sample",
    )
    fragment_corpus.add_argument("--sample", type=Path, required=True)
    fragment_corpus.add_argument("--output", type=Path, required=True)
    fragment_corpus.add_argument("--train-size", type=int, default=7)
    fragment_corpus.add_argument(
        "--exclude-example-id",
        action="append",
        default=[],
        help="Exclude a frozen held-out example ID; may be supplied more than once",
    )
    fragment_corpus.add_argument("--overwrite", action="store_true")

    vertical_slice = commands.add_parser(
        "run-vertical-slice",
        help="Run graph-conditioned fragment retrieval and SQL assembly",
    )
    vertical_slice.add_argument("--sample", type=Path, required=True)
    vertical_slice.add_argument("--database-root", type=Path, required=True)
    vertical_slice.add_argument(
        "--graph-trace",
        type=Path,
        action="append",
        required=True,
        help="Intent-graph trace; repeat to merge retries, with later traces winning",
    )
    vertical_slice.add_argument("--fragment-corpus", type=Path, required=True)
    vertical_slice.add_argument("--model", required=True)
    vertical_slice.add_argument("--reasoning-effort")
    vertical_slice.add_argument("--output", type=Path, required=True)
    vertical_slice.add_argument("--offset", type=int, default=7)
    vertical_slice.add_argument("--limit", type=int, default=3)
    vertical_slice.add_argument("--generation-timeout-seconds", type=float, default=120.0)
    vertical_slice.add_argument(
        "--retriever",
        choices=("lexical", "fastembed", "learned"),
        default="lexical",
    )
    vertical_slice.add_argument("--embedding-model", default="BAAI/bge-small-en-v1.5")
    vertical_slice.add_argument(
        "--model-cache",
        type=Path,
        default=Path("artifacts/models/fastembed"),
    )
    vertical_slice.add_argument("--ranker-model", type=Path)
    vertical_slice.add_argument("--top-k-per-intent", type=int, default=2)
    vertical_slice.add_argument("--max-retrieval-hits", type=int, default=12)
    vertical_slice.add_argument("--max-repair-attempts", type=int, default=1)
    vertical_slice.add_argument("--overwrite", action="store_true")

    retrieval_eval = commands.add_parser(
        "evaluate-fragment-retrieval",
        help="Measure held-out gold-fragment recall without SQL assembly",
    )
    retrieval_eval.add_argument("--sample", type=Path, required=True)
    retrieval_eval.add_argument("--graph-trace", type=Path, required=True)
    retrieval_eval.add_argument("--fragment-corpus", type=Path, required=True)
    retrieval_eval.add_argument("--output", type=Path, required=True)
    retrieval_eval.add_argument("--offset", type=int, default=7)
    retrieval_eval.add_argument("--limit", type=int, default=3)
    retrieval_eval.add_argument(
        "--recall-at",
        type=int,
        action="append",
        help="Recall cutoff; repeat for multiple values (defaults: 1, 3, 5, 10, 12)",
    )
    retrieval_eval.add_argument("--top-k-per-intent", type=int, default=2)
    retrieval_eval.add_argument(
        "--retriever",
        choices=("lexical", "fastembed", "learned"),
        default="lexical",
    )
    retrieval_eval.add_argument(
        "--embedding-model",
        default="BAAI/bge-small-en-v1.5",
        help="FastEmbed model name when --retriever=fastembed",
    )
    retrieval_eval.add_argument(
        "--model-cache",
        type=Path,
        default=Path("artifacts/models/fastembed"),
    )
    retrieval_eval.add_argument(
        "--ranker-model",
        type=Path,
        help="Learned ranker JSON when --retriever=learned",
    )
    retrieval_eval.add_argument("--overwrite", action="store_true")

    train_ranker = commands.add_parser(
        "train-fragment-ranker",
        help="Train an auditable task-specific intent-to-SQL-fragment reranker",
    )
    train_ranker.add_argument("--sample", type=Path, required=True)
    train_ranker.add_argument(
        "--graph-trace",
        type=Path,
        action="append",
        required=True,
        help="Training graph trace; repeat to merge multiple trace files",
    )
    train_ranker.add_argument("--fragment-corpus", type=Path, required=True)
    train_ranker.add_argument("--output", type=Path, required=True)
    train_ranker.add_argument("--offset", type=int, default=0)
    train_ranker.add_argument("--limit", type=int, default=20)
    train_ranker.add_argument("--embedding-model", default="BAAI/bge-small-en-v1.5")
    train_ranker.add_argument(
        "--model-cache",
        type=Path,
        default=Path("artifacts/models/fastembed"),
    )
    train_ranker.add_argument("--epochs", type=int, default=500)
    train_ranker.add_argument("--learning-rate", type=float, default=0.08)
    train_ranker.add_argument("--l2", type=float, default=0.01)
    train_ranker.add_argument("--overwrite", action="store_true")

    teacher_distribution = commands.add_parser(
        "analyze-teacher-distribution",
        help="Measure intent-graph variability across repeated teacher samples",
    )
    teacher_distribution.add_argument(
        "--graph-trace", type=Path, action="append", required=True
    )
    teacher_distribution.add_argument("--output", type=Path, required=True)
    teacher_distribution.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "baseline":
        examples = load_bird_examples(args.dataset)
        selected, omitted = select_readonly_examples(
            examples,
            offset=0 if args.example_id else args.offset,
            limit=None if args.example_id else args.limit,
        )
        if args.example_id:
            requested_ids = set(args.example_id)
            selected = [example for example in selected if example.example_id in requested_ids]
            missing_ids = requested_ids - {example.example_id for example in selected}
            if missing_ids:
                raise SystemExit(f"Unknown or non-readonly example IDs: {sorted(missing_ids)}")
        if not selected:
            raise SystemExit("No examples selected")

        manifest_path = args.manifest or args.output.with_suffix(".manifest.json")
        protected_paths = [manifest_path] if args.dry_run else [manifest_path, args.output]
        collisions = [path for path in protected_paths if path.exists()]
        if collisions and not args.overwrite:
            rendered = ", ".join(str(path) for path in collisions)
            raise SystemExit(f"Refusing to overwrite existing artifacts: {rendered}")

        pricing = PricingRates.from_json(args.pricing_file) if args.pricing_file else None
        if args.provider == "codex-cli" and pricing is not None:
            raise SystemExit(
                "API pricing cannot be applied to ChatGPT-authenticated Codex CLI usage"
            )
        manifest = build_preflight_manifest(
            dataset_path=args.dataset,
            database_root=args.database_root,
            all_examples=examples,
            selected_examples=selected,
            omitted_non_readonly=omitted,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            timeout_seconds=args.timeout_seconds,
            max_rows=args.max_rows,
            offset=0 if args.example_id else args.offset,
            limit=None if args.example_id else args.limit,
            pricing=pricing,
            provider=args.provider,
        )
        write_manifest(manifest_path, manifest)
        if args.dry_run:
            print(json.dumps(manifest, indent=2, sort_keys=True))
            return 0

        if args.provider == "openai":
            generator = OpenAISQLGenerator(
                model=args.model,
                reasoning_effort=args.reasoning_effort,
            )
        else:
            generator = CodexCLISQLGenerator(
                model=args.model,
                reasoning_effort=args.reasoning_effort,
            )
        summary = run_baseline(
            selected,
            database_root=args.database_root,
            generator=generator,
            output_path=args.output,
            timeout_seconds=args.timeout_seconds,
            max_rows=args.max_rows,
            pricing=pricing,
        )
        manifest["status"] = "completed"
        manifest["summary"] = summary
        write_manifest(manifest_path, manifest)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "export-bird":
        examples = load_bird_examples(args.dataset)
        selected, _ = select_readonly_examples(examples)
        if args.example_id:
            requested_ids = set(args.example_id)
            by_id = {example.example_id: example for example in selected}
            trace_records = [
                json.loads(line)
                for line in args.trace.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            trace_ids = [
                str(record.get("example_id", (record.get("example") or {}).get("example_id")))
                for record in trace_records
            ]
            if set(trace_ids) != requested_ids or any(example_id not in by_id for example_id in trace_ids):
                raise SystemExit("--example-id values must exactly match the trace example IDs")
            selected = [by_id[example_id] for example_id in trace_ids]
        outputs = export_bird_evaluator_inputs(
            trace_path=args.trace,
            examples=selected,
            output_directory=args.output_directory,
        )
        print(json.dumps(outputs, indent=2, sort_keys=True))
        return 0
    if args.command == "select-intent-audit":
        examples = load_bird_examples(args.dataset)
        selected = select_diverse_examples(examples, size=args.size)
        summary = write_intent_audit_sample(args.output, selected)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "audit-intent-graphs":
        protected_paths = [args.output, args.output.with_suffix(".summary.json")]
        collisions = [path for path in protected_paths if path.exists()]
        if collisions and not args.overwrite:
            rendered = ", ".join(str(path) for path in collisions)
            raise SystemExit(f"Refusing to overwrite existing artifacts: {rendered}")
        examples = load_intent_audit_sample(args.sample)
        if args.example_id:
            requested_ids = set(args.example_id)
            examples = [example for example in examples if example.example_id in requested_ids]
        if args.limit is not None:
            examples = examples[: max(args.limit, 0)]
        generator = CodexCLIIntentGraphGenerator(
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            timeout_seconds=args.generation_timeout_seconds,
        )
        summary = run_intent_generation_audit(
            examples,
            database_root=args.database_root,
            generator=generator,
            output_path=args.output,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "build-fragment-corpus":
        if args.output.exists() and not args.overwrite:
            raise SystemExit(f"Refusing to overwrite existing artifact: {args.output}")
        excluded_ids = set(args.exclude_example_id)
        examples = [
            example
            for example in load_intent_audit_sample(args.sample)
            if example.example_id not in excluded_ids
        ][: max(args.train_size, 0)]
        summary = build_fragment_corpus(examples, output_path=args.output)
        summary["excluded_example_ids"] = sorted(excluded_ids)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "run-vertical-slice":
        protected_paths = [args.output, args.output.with_suffix(".summary.json")]
        collisions = [path for path in protected_paths if path.exists()]
        if collisions and not args.overwrite:
            rendered = ", ".join(str(path) for path in collisions)
            raise SystemExit(f"Refusing to overwrite existing artifacts: {rendered}")
        examples = load_intent_audit_sample(args.sample)
        start = max(args.offset, 0)
        examples = examples[start : start + max(args.limit, 0)]
        assembler = CodexCLIFragmentAssembler(
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            timeout_seconds=args.generation_timeout_seconds,
        )
        corpus = load_fragment_corpus(args.fragment_corpus)
        retriever = None
        retriever_name = "lexical-bm25-control"
        if args.retriever == "fastembed":
            retriever = FastEmbedFragmentRetriever(
                corpus,
                model_name=args.embedding_model,
                cache_dir=args.model_cache,
            )
            retriever_name = f"fastembed/{args.embedding_model}"
        elif args.retriever == "learned":
            if args.ranker_model is None:
                raise SystemExit("--ranker-model is required when --retriever=learned")
            model = LinearRankerModel.load(args.ranker_model)
            retriever = LearnedFragmentRetriever(
                corpus,
                model=model,
                cache_dir=args.model_cache,
            )
            retriever_name = f"learned-linear/{model.embedding_model}"
        graph_records: dict[str, dict[str, object]] = {}
        for trace_path in args.graph_trace:
            graph_records.update(load_graph_trace(trace_path))
        summary = run_vertical_slice(
            examples,
            database_root=args.database_root,
            graph_records=graph_records,
            corpus=corpus,
            assembler=assembler,
            output_path=args.output,
            retriever=retriever,
            retriever_name=retriever_name,
            top_k_per_intent=max(args.top_k_per_intent, 1),
            max_retrieval_hits=max(args.max_retrieval_hits, 1),
            max_repair_attempts=max(args.max_repair_attempts, 0),
            parser_timeout_seconds=args.generation_timeout_seconds,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "evaluate-fragment-retrieval":
        protected_paths = [args.output, args.output.with_suffix(".summary.json")]
        collisions = [path for path in protected_paths if path.exists()]
        if collisions and not args.overwrite:
            rendered = ", ".join(str(path) for path in collisions)
            raise SystemExit(f"Refusing to overwrite existing artifacts: {rendered}")
        examples = load_intent_audit_sample(args.sample)
        start = max(args.offset, 0)
        examples = examples[start : start + max(args.limit, 0)]
        corpus = load_fragment_corpus(args.fragment_corpus)
        retriever = None
        retriever_name = "lexical-bm25-control"
        if args.retriever == "fastembed":
            retriever = FastEmbedFragmentRetriever(
                corpus,
                model_name=args.embedding_model,
                cache_dir=args.model_cache,
            )
            retriever_name = f"fastembed/{args.embedding_model}"
        elif args.retriever == "learned":
            if args.ranker_model is None:
                raise SystemExit("--ranker-model is required when --retriever=learned")
            model = LinearRankerModel.load(args.ranker_model)
            retriever = LearnedFragmentRetriever(
                corpus,
                model=model,
                cache_dir=args.model_cache,
            )
            retriever_name = f"learned-linear/{model.embedding_model}"
        summary = evaluate_fragment_retrieval(
            examples,
            graph_records=load_graph_trace(args.graph_trace),
            corpus=corpus,
            output_path=args.output,
            recall_at=tuple(args.recall_at or (1, 3, 5, 10, 12)),
            top_k_per_intent=max(args.top_k_per_intent, 1),
            retriever=retriever,
            retriever_name=retriever_name,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "train-fragment-ranker":
        if args.output.exists() and not args.overwrite:
            raise SystemExit(f"Refusing to overwrite existing artifact: {args.output}")
        examples = load_intent_audit_sample(args.sample)
        start = max(args.offset, 0)
        examples = examples[start : start + max(args.limit, 0)]
        graph_records: dict[str, dict[str, object]] = {}
        for trace_path in args.graph_trace:
            graph_records.update(load_graph_trace(trace_path))
        summary = train_fragment_ranker(
            examples,
            graph_records=graph_records,
            corpus=load_fragment_corpus(args.fragment_corpus),
            output_path=args.output,
            embedding_model=args.embedding_model,
            cache_dir=args.model_cache,
            epochs=max(args.epochs, 1),
            learning_rate=args.learning_rate,
            l2=max(args.l2, 0.0),
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.command == "analyze-teacher-distribution":
        if args.output.exists() and not args.overwrite:
            raise SystemExit(f"Refusing to overwrite existing artifact: {args.output}")
        summary = analyze_teacher_distribution(
            args.graph_trace,
            output_path=args.output,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
