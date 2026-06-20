#!/usr/bin/env python3
"""Generate experiment hypothesis.md, run.py, results.md for registered experiments."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPERIMENTS = [
    {
        "id": "exp_001_lora_baseline",
        "num": "001",
        "title": "LoRA Baseline",
        "method": "LoRA",
        "evidence": "Established",
        "expect": "LoRA rank 16 reaches Pass@1 ≥ 60% on smoke held-out for all three TargetLanguage values.",
        "why": "LoRA is the established PEFT anchor; all advanced methods compare against it at matched rank or param budget.",
        "wrong": "Pass@1 below 50% on any language after smoke profile, or peak VRAM above 7 GB on 0.5B QLoRA-class budget.",
        "metrics": ["Pass@1", "Pass@5", "Peak VRAM", "Trainable params", "Wall-clock time"],
    },
    {
        "id": "exp_002_qlora_baseline",
        "num": "002",
        "title": "QLoRA Baseline",
        "method": "QLoRA",
        "evidence": "Established",
        "expect": "QLoRA achieves within 2% Pass@1 of LoRA at ≥20% lower peak VRAM on RTX 4060.",
        "why": "4-bit base weights are the standard VRAM-friendly baseline for solo GPU setups.",
        "wrong": "VRAM savings below 10% or Pass@1 drop above 5% vs LoRA at same dataset version.",
        "metrics": ["Pass@1", "Peak VRAM", "Model size on disk"],
    },
    {
        "id": "exp_003_dora_baseline",
        "num": "003",
        "title": "DoRA vs LoRA",
        "method": "DoRA",
        "evidence": "Established",
        "expect": "DoRA at rank 16 outperforms LoRA-r=16 on HTML and FreeMarker Pass@1 by ≥3% at matched param count.",
        "why": "Magnitude-direction decomposition improves convergence on structured template outputs.",
        "wrong": "DoRA worse than LoRA on all languages, or param count differs by more than 10% without footnote.",
        "metrics": ["Pass@1 per language", "Trainable params", "Convergence step"],
    },
    {
        "id": "exp_004_ttloRA_bond_sweep",
        "num": "004",
        "title": "TT-LoRA Bond Sweep",
        "method": "TTLoRA",
        "evidence": "QuantumInspired",
        "expect": "TTLoRA at χ=16 matches LoRA-r=16 Pass@1 with fewer trainable parameters on JavaScript.",
        "why": "Tensor train (DMRG-style) factorization may allocate rank budget more efficiently across layers.",
        "wrong": "All χ values below LoRA Pass@1 by >5%, or VRAM higher than LoRA at matched params.",
        "metrics": ["Pass@1 vs χ", "Trainable params", "Peak VRAM", "χ × language heatmap"],
    },
    {
        "id": "exp_005_trg_training_speed",
        "num": "005",
        "title": "TRG Training Speed",
        "method": "TRG",
        "evidence": "QuantumInspired",
        "expect": "TRG fine-tuning completes in ≥30% less wall-clock time than LoRA at similar Pass@1 on mixed dataset.",
        "why": "Renormalization-group coarse-graining reported ~45-50% training time reduction in tensorized FT literature.",
        "wrong": "Speedup below 15% or Pass@1 drop above 3% vs LoRA.",
        "metrics": ["Wall-clock seconds", "Pass@1", "Peak VRAM"],
    },
    {
        "id": "exp_006_galore_memory",
        "num": "006",
        "title": "GaLore Memory",
        "method": "GaLore",
        "evidence": "Established",
        "expect": "GaLore peak VRAM stays within 120% of LoRA while updating full weights on 0.5B model.",
        "why": "Gradient low-rank projection targets full fine-tune expressivity at adapter-like memory.",
        "wrong": "OOM on 4060 at ci/smoke profile, or Pass@1 below LoRA by >5%.",
        "metrics": ["Peak VRAM", "Pass@1", "Trainable params (full vs adapter)"],
    },
    {
        "id": "exp_007_mpo_compression",
        "num": "007",
        "title": "MPO Compression",
        "method": "MPO",
        "evidence": "QuantumInspired",
        "expect": "MPO at χ=16 reduces trainable params by ≥30% vs LoRA-r=16 with ≤2% Pass@1 drop.",
        "why": "Matrix product operators compress attention/MLP maps aggressively in recent LLM compression work.",
        "wrong": "Pass@1 drop above 5% or param reduction below 15%.",
        "metrics": ["Trainable params", "Pass@1", "Peak VRAM", "Inference tokens/s"],
    },
    {
        "id": "exp_008_qtha_rank_limit",
        "num": "008",
        "title": "QTHA Low Rank",
        "method": "QTHA",
        "evidence": "QuantumInspired",
        "expect": "QTHA at χ=8 beats LoRA-r=8 on JavaScript Pass@1 (quantum-inspired, classical GPU simulation).",
        "why": "Simulated superposition may exceed classical LoRA rank limits at equal param budget.",
        "wrong": "QTHA worse than LoRA-r=8 on all languages — report as negative result.",
        "metrics": ["Pass@1 JS vs HTML vs FMT", "Train loss curve", "Trainable params"],
    },
    {
        "id": "exp_009_incremental_vs_mixed",
        "num": "009",
        "title": "Incremental vs Mixed",
        "method": "LoRA",
        "evidence": "Established",
        "expect": "IncrementalByLanguage training beats MixedLanguages Pass@1 on FreeMarker for 0.5B by ≥4%.",
        "why": "Small models may suffer interference when languages are shuffled; sequential specialization may help.",
        "wrong": "MixedLanguages wins on all languages — incremental provides no benefit.",
        "metrics": ["Pass@1 per language", "DataSchedule tag", "Total training time"],
    },
    {
        "id": "exp_010_decoherence_regularization",
        "num": "010",
        "title": "Decoherence Regularization",
        "method": "DecoherenceRegularization",
        "evidence": "Speculative",
        "expect": "Decoherence penalty (λ=0.1) reduces overfit on synthetic data — Pass@1 held-out +2% vs LoRA alone.",
        "why": "Speculative borrow from QM: penalize rising activation entropy during fine-tune.",
        "wrong": "No change or degradation — null result is valid and must be reported honestly as L4.",
        "metrics": ["Pass@1", "DecoherenceScore trajectory", "λ sensitivity"],
    },
    {
        "id": "exp_011_gv_alr_lora_transfer",
        "num": "011",
        "title": "GV-ALR LoRA Transfer",
        "method": "GradientVarianceAdaptiveLR",
        "evidence": "NovelApplication",
        "expect": "GV-ALR on LoRA adapters reduces wall-clock training time by ≥25% vs fixed Adam at ≤1 pp Pass@1 drop.",
        "why": "quantun-ia exp_054/075 accepted: same AUC/PR-AUC with 58% wall-time and 5/8 epochs on RTX 4060.",
        "wrong": "No time savings or Pass@1 drop >2 pp vs fixed LR LoRA baseline (exp_001).",
        "metrics": ["Pass@1", "Wall-clock seconds", "Epochs to convergence", "Peak VRAM"],
    },
    {
        "id": "exp_012_reupload_schedule_lora",
        "num": "012",
        "title": "Data Reupload Schedule",
        "method": "DataReupload",
        "evidence": "NovelApplication",
        "expect": "Multi-pass DataReupload schedule improves Pass@1 by ≥3 pp vs single-pass LoRA at matched total token budget.",
        "why": "quantun-ia exp_008: reupload beat basic QNN by +5.6 pp (Holm p=0.012); depth via re-injection.",
        "wrong": "Single-pass LoRA wins on all languages or matched-token budget not honored.",
        "metrics": ["Pass@1 per language", "reuploadPasses", "Total tokens seen"],
    },
    {
        "id": "exp_013_frozen_backbone_lora",
        "num": "013",
        "title": "Frozen Backbone LoRA",
        "method": "FrozenBackboneHybridHead",
        "evidence": "NovelApplication",
        "expect": "LoRA on head + last 2 blocks only stays within 2 pp of full-layer LoRA with ≥20% VRAM savings.",
        "why": "quantun-ia exp_037/051/062/071: hybrid head accepted on all 4 domain anchors with ~289 trainable params.",
        "wrong": "Pass@1 drop >2 pp or VRAM savings <15% vs exp_001 full LoRA.",
        "metrics": ["Pass@1", "Trainable params", "Peak VRAM", "Frozen layer count"],
    },
]


def write_hypothesis(exp: dict, path: Path) -> None:
    metrics = "\n".join(f"- [ ] {m}" for m in exp["metrics"])
    path.write_text(
        f"""# Hypothesis — EXP {exp['num']}

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** {exp['evidence']}

## What I expect to happen
{exp['expect']}

## Why I expect this
{exp['why']}

## What would prove me wrong
{exp['wrong']}

## Metrics I will measure
{metrics}
""",
        encoding="utf-8",
    )


def write_run(exp: dict, path: Path) -> None:
    path.write_text(
        f'''#!/usr/bin/env python3
"""EXP {exp['num']} — {exp['title']}. Thin orchestrator; training logic goes in src/."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _stub_runner import run_stub


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="ci", choices=["ci", "smoke", "publication"])
    args, _ = parser.parse_known_args(argv)
    return run_stub(
        "{exp['id']}",
        "{exp['method']}",
        "{exp['evidence']}",
        args.profile,
    )


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def write_results(exp: dict, path: Path) -> None:
    path.write_text(
        f"""# Results — EXP {exp['num']} ({exp['title']})

**Status:** Pending — stub run only until training stack is implemented.

## What happened
Not yet executed with real GPU training.

## Comparison with hypothesis
N/A

## Unexpected finding
N/A

## Suggested next experiment
Run Wave 1 anchors (exp_001–003) before tensor methods.
""",
        encoding="utf-8",
    )


def main() -> None:
    for exp in EXPERIMENTS:
        d = ROOT / "experiments" / exp["id"]
        d.mkdir(parents=True, exist_ok=True)
        write_hypothesis(exp, d / "hypothesis.md")
        write_run(exp, d / "run.py")
        write_results(exp, d / "results.md")
    print(f"Generated {len(EXPERIMENTS)} experiments")


if __name__ == "__main__":
    main()
