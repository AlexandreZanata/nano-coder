# Hypothesis Workflow — nano-coder

> Mandatory for every experiment. Adapted from quantun-ia.

---

## The three files

```
experiments/exp_NNN_<name>/
├── hypothesis.md   ← Write BEFORE running
├── run.py          ← Thin orchestrator (logic in src/)
└── results.md      ← Fill AFTER running
```

---

## Step 1 — Write the hypothesis

```markdown
# Hypothesis — EXP 004

**Date:** 2026-06-20
**Author:** pipeline-operator

## What I expect to happen
TT-LoRA at bond dimension χ=16 will match or beat LoRA-rank-16 Pass@1 on JavaScript
held-out tasks at lower peak VRAM.

## Why I expect this
Tensor train decomposition shares parameter budget more efficiently across layers
(DMRG / 1D tensor network literature).

## What would prove me wrong
If TTLoRA Pass@1 is >5% below LoRA at matched trainable param count,
or peak VRAM exceeds LoRA by >20%.

## Metrics I will measure
- [ ] Pass@1 / Pass@5 per TargetLanguage
- [ ] Peak VRAM (GB)
- [ ] Wall-clock training time
- [ ] Trainable parameter count
- [ ] EvidenceLevel = QuantumInspired
```

**Agents must not implement `run.py` until `hypothesis.md` has real content.**

CI enforces via `tests/unit/test_hypothesis.py`.

---

## Step 2 — Run the experiment

```bash
MLFLOW_DISABLE=1 python experiments/exp_004_ttloRA_bond_sweep/run.py --profile ci
```

Results append to `logs/experiments.jsonl` (never delete — append only).

---

## Step 3 — Document results

Fill `results.md`:

- What happened (objective)
- Comparison with hypothesis
- Unexpected finding
- Suggested next experiment

Negative results are **valid** — document collapse at sub-1B or L4 null outcomes.

---

## Log discipline

| Rule | Reason |
|------|--------|
| Append-only JSONL | Audit trail for paper replication |
| Never commit `logs/` | Local/DVC artifacts |
| Log `evidenceLevel`, `bondDimension`, `compressionMethod` | BR-013 |
| Never log API keys | Security |

---

## Working with agents

**Before:** "I'm running EXP 007 MPO. What falsification criteria am I missing?"

**During:** "Is bond χ=4 fair comparison to LoRA-rank-8 by param count?"

**After:** "MPO beat LoRA on HTML but not JS. What χ sweep should come next?"
