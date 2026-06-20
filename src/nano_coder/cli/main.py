"""nano-coder CLI entrypoint (PIPELINE-CONTRACT.md)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nano_coder.application.benchmark import run_benchmark
from nano_coder.application.train import run_train
from nano_coder.domain.benchmark_config import load_benchmark_config
from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.train_config import load_train_config
from nano_coder.domain.training_run import TrainingRunState
from nano_coder.infrastructure.mock_trainer import CheckpointNotFoundError

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TRAIN_CONFIG = ROOT / "config" / "train-v1.yaml"
DEFAULT_BENCHMARK_CONFIG = ROOT / "config" / "benchmark-v1.yaml"
DEFAULT_PUBLISHED = ROOT / "data" / "datasets"
DEFAULT_CHECKPOINTS = ROOT / "data" / "checkpoints"
DEFAULT_HELD_OUT = ROOT / "data" / "benchmarks" / "held-out-v1"
DEFAULT_BENCHMARK_OUTPUT = ROOT / "data" / "benchmarks"
DEFAULT_EVENTS = ROOT / "data" / "events" / "events.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nano-coder")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Start a TrainingRun (UC-003)")
    _add_train_args(train_parser)

    bench_parser = subparsers.add_parser("benchmark", help="Start a BenchmarkRun (UC-004)")
    _add_benchmark_args(bench_parser)

    args = parser.parse_args(argv)
    if args.command == "train":
        return _run_train_command(args)
    if args.command == "benchmark":
        return _run_benchmark_command(args)
    return 1


def _add_train_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--compression-method", "--method", dest="compression_method")
    parser.add_argument("--data-schedule", default="MixedLanguages")
    parser.add_argument("--lora-rank", type=int)
    parser.add_argument("--student-model")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--profile", default="smoke", choices=["ci", "smoke", "publication"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--config", type=Path, default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument("--published", type=Path, default=DEFAULT_PUBLISHED)
    parser.add_argument("--checkpoints", type=Path, default=DEFAULT_CHECKPOINTS)
    parser.add_argument("--events-log", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Attempt real GPU training (requires torch/transformers/peft)",
    )


def _add_benchmark_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--test-set-version", default="held-out-v1")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_BENCHMARK_CONFIG)
    parser.add_argument("--held-out", type=Path, default=DEFAULT_HELD_OUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_BENCHMARK_OUTPUT)
    parser.add_argument("--events-log", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Attempt real GPU inference (requires torch/transformers)",
    )


def _run_train_command(args: argparse.Namespace) -> int:
    config = load_train_config(args.config)
    method = CompressionMethod(args.compression_method or config.compression_method.value)
    student_model = args.student_model or config.student_model
    try:
        result = run_train(
            run_id=args.run_id,
            dataset_version=args.dataset_version,
            compression_method=method,
            student_model=student_model,
            data_schedule=DataSchedule(args.data_schedule),
            published_root=args.published,
            checkpoint_root=args.checkpoints,
            config=config,
            profile=args.profile,
            lora_rank=args.lora_rank,
            seed=args.seed,
            events_log=args.events_log,
            dry_run=not args.real,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"OK: trained {result.train_example_count} examples → "
        f"{result.checkpoint_dir} ({result.training_state.value})"
    )
    return 0 if result.training_state is TrainingRunState.COMPLETED else 1


def _run_benchmark_command(args: argparse.Namespace) -> int:
    config = load_benchmark_config(args.config)
    try:
        result = run_benchmark(
            run_id=args.run_id,
            checkpoint_dir=args.checkpoint,
            held_out_root=args.held_out,
            output_root=args.output,
            config=config,
            test_set_version=args.test_set_version,
            events_log=args.events_log,
            dry_run=not args.real,
        )
    except CheckpointNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"OK: benchmark Pass@1 {result.summary.pass_at_1:.1%} "
        f"Pass@5 {result.summary.pass_at_5:.1%} → {result.results_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
