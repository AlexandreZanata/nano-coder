# Paper Narrative — nano-coder

**Status:** Draft for v0.1.0 benchmark paper.  
**Paper entry:** `paper/main.tex`  
**Audience:** Workshop / arXiv (cs.LG + cs.SE)

---

## Headline claim

Holdout-fair comparison of **parameter-efficient fine-tuning methods** (LoRA through quantum-**inspired** tensor networks) for **sub-1B code SLMs** on **JavaScript, HTML, and FreeMarker**, trained exclusively on **teacher-distilled synthetic data**, with honest evidence labeling and bond dimension χ as the central compression axis.

---

## Research questions (paper abstract bullets)

1. How small can a student model be before Pass@1 collapses per language?
2. Which `CompressionMethod` delays collapse at matched parameter budget?
3. Does bond dimension χ explain cross-language differences better than LoRA rank alone?
4. Do tensor methods (TTLoRA, TRG, MPO) improve VRAM or wall-clock vs LoRA on RTX 4060-class hardware?

---

## In-scope experiments (main paper)

| ID | Role |
|----|------|
| exp_001 | LoRA baseline (Established) |
| exp_002 | QLoRA VRAM baseline |
| exp_003 | DoRA vs LoRA matched rank |
| exp_004 | TTLoRA + χ sweep {4,8,16,32} |
| exp_005 | TRG training speed vs LoRA |
| exp_006 | GaLore gradient subspace memory |
| exp_007 | MPO compression vs LoRA |
| exp_008 | QTHA at low χ vs LoRA |
| exp_009 | IncrementalByLanguage vs MixedLanguages |
| exp_010 | DecoherenceRegularization (L4 — report null if no effect) |

### Wave Q — quantun-ia proven transfers (appendix / follow-up)

| ID | Role |
|----|------|
| exp_011 | GV-ALR + LoRA — training efficiency (quantun-ia exp_054/075) |
| exp_012 | DataReupload + LoRA — multi-pass schedule (quantun-ia exp_008) |
| exp_013 | FrozenBackbone + LoRA — partial adapters (quantun-ia exp_037+) |

See [QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md).

---

## Deferred / appendix (do not headline in v0.1)

| Item | Reason |
|------|--------|
| iPEPS 2D tensor network | L3 — run after W3 if MPO/TTLoRA show signal |
| LowRankSketching meta-method | Appendix — rank estimation protocol |
| FullFineTune at 1.5B+ | Hardware appendix only if VRAM allows |
| HTTP API / dashboard | Out of scope phase 1 |

---

## Honesty policy (methods section)

- Label **L2 QuantumInspired** methods as classical simulation — not quantum hardware
- Cite original tensor-network / RG literature — do not claim novel physics
- **L4 Speculative** (exp_010) gets its own subsection with pre-registered falsification
- Negative results (sub-1B collapse) are primary contributions

---

## Publication pipeline

```bash
make check                  # CI gate locally
make check-real             # RTX 4060 (before claiming GPU numbers)
make paper-build            # paper/main.pdf
# Future:
# make latex-tables
# make figures
# make arxiv-bundle
# make finalize-citation DOI=10.5281/zenodo.XXXXXXX
```

---

## Enforcement

Contract tests:

- `tests/contracts/test_research_structure.py` — YAML ↔ folders ↔ this narrative
- `tests/unit/test_hypothesis.py` — no placeholder hypotheses

---

## Related

- [TRAINING-METHODS.md](TRAINING-METHODS.md) — method catalog + evidence tiers
- [EVALUATION-METHOD.md](EVALUATION-METHOD.md) — Pass@k, χ heatmaps
- [REPRODUCIBILITY.md](REPRODUCIBILITY.md) — seeds, profiles, replay commands
