# Compute Environment — nano-coder

> Primary development GPU: **NVIDIA RTX 4060** (quantun-ia reference setup).

---

## Target hardware

| Component | Spec | Notes |
|-----------|------|-------|
| GPU | RTX 4060 (8 GB VRAM) | Real gate `make check-real` |
| CPU | Any modern x64 | CI runs on `ubuntu-latest` |
| RAM | 16 GB+ recommended | QLoRA + 0.5B fits; 1.5B tight |

---

## VRAM guidance by method

| CompressionMethod | 0.5B student | 1.5B student |
|-------------------|--------------|--------------|
| LoRA | ✅ ~4–6 GB | ⚠️ 7–8 GB |
| QLoRA | ✅ ~3–5 GB | ✅ ~5–7 GB |
| DoRA | ✅ similar LoRA | ⚠️ |
| GaLore | ⚠️ higher than LoRA | ❌ likely OOM |
| TTLoRA / TRG / MPO | ✅ target methods | ⚠️ reduce χ |
| FullFineTune | ✅ possible | ❌ skip — document N/A |

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `MLFLOW_DISABLE=1` | Disable MLflow in local/CI runs |
| `NANO_CODER_DATA_DIR` | Override data root |
| `TEACHER_API_KEY` | Teacher LLM (never in CI) |
| `HF_TOKEN` | HuggingFace downloads |
| `CUDA_VISIBLE_DEVICES=0` | Single GPU selection |

---

## Profiles vs hardware

| Profile | Use when |
|---------|----------|
| `ci` | GitHub Actions CPU — wiring only |
| `smoke` | Phase 2 student selection on GPU |
| `publication` | Final paper numbers on RTX 4060 |

---

## Health probes

```bash
make health       # disk, logs/
make health-gpu   # + torch.cuda.is_available()
nvidia-smi        # manual VRAM check before long runs
```

---

## Docker (future)

quantun-ia uses `docker-compose.test.yml` for reproducible CI. nano-coder will add GPU compose when training stack is pinned — track in ADR when added.
