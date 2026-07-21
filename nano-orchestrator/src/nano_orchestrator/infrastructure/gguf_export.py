"""Merge QLoRA adapter and export GGUF Q4_K_M for llama-server."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONVERT = REPO_ROOT / ".local" / "llama.cpp-prism" / "convert_hf_to_gguf.py"
DEFAULT_QUANTIZE = REPO_ROOT / ".local" / "llama-prism-cuda" / "llama-quantize"


@dataclass(frozen=True, slots=True)
class GgufExportResult:
    merged_dir: Path
    f16_gguf: Path
    q4_gguf: Path
    model_id: str


def merge_adapter_to_hf(
    *,
    base_hf_id: str,
    adapter_dir: Path,
    merged_dir: Path,
) -> Path:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    merged_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(
        base_hf_id,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
        token=os.environ.get("HF_TOKEN") or None,
    )
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    merged = model.merge_and_unload()
    merged.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)
    return merged_dir


def convert_hf_to_gguf(
    merged_dir: Path,
    out_gguf: Path,
    *,
    convert_script: Path = DEFAULT_CONVERT,
    out_type: str = "f16",
) -> Path:
    if not convert_script.is_file():
        raise FileNotFoundError(f"convert script missing: {convert_script}")
    out_gguf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        os.environ.get("NANO_ORCH_PYTHON", "python3"),
        str(convert_script),
        str(merged_dir),
        "--outfile",
        str(out_gguf),
        "--outtype",
        out_type,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"convert_hf_to_gguf failed ({proc.returncode}): {proc.stderr[-2000:]}"
        )
    if not out_gguf.is_file():
        # Some convert scripts name by model; search sibling.
        candidates = list(out_gguf.parent.glob("*.gguf"))
        if not candidates:
            raise FileNotFoundError(f"GGUF not written: {out_gguf}")
        return candidates[0]
    return out_gguf


def quantize_gguf(
    src: Path,
    dst: Path,
    *,
    quantize_bin: Path = DEFAULT_QUANTIZE,
    quant_type: str = "Q4_K_M",
) -> Path:
    if not quantize_bin.is_file():
        raise FileNotFoundError(f"llama-quantize missing: {quantize_bin}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    cuda_candidates = [
        Path.home()
        / ".pyenv"
        / "versions"
        / "3.12.2"
        / "lib"
        / "python3.12"
        / "site-packages"
        / "nvidia"
        / "cuda_runtime"
        / "lib",
        REPO_ROOT / ".venv-gpu" / "lib" / "python3.12" / "site-packages" / "nvidia" / "cuda_runtime" / "lib",
    ]
    cublas_candidates = [
        Path.home()
        / ".pyenv"
        / "versions"
        / "3.12.2"
        / "lib"
        / "python3.12"
        / "site-packages"
        / "nvidia"
        / "cublas"
        / "lib",
        REPO_ROOT / ".venv-gpu" / "lib" / "python3.12" / "site-packages" / "nvidia" / "cublas" / "lib",
    ]
    extras = [str(REPO_ROOT / ".local" / "llama-prism-cuda")]
    for path in cuda_candidates + cublas_candidates:
        if path.is_dir():
            extras.append(str(path))
    env["LD_LIBRARY_PATH"] = ":".join(extras + [env.get("LD_LIBRARY_PATH", "")])
    proc = subprocess.run(
        [str(quantize_bin), str(src), str(dst), quant_type],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if proc.returncode != 0 or not dst.is_file():
        raise RuntimeError(
            f"llama-quantize failed ({proc.returncode}): {proc.stderr[-2000:]}"
        )
    return dst


def export_worker_gguf(
    *,
    language: str,
    base_hf_id: str,
    adapter_dir: Path,
    export_root: Path,
    model_id: str | None = None,
) -> GgufExportResult:
    mid = model_id or f"qwen25-coder-0.5b-{language}-ft"
    work = export_root / mid
    merged_dir = work / "merged-hf"
    f16_path = work / f"{mid}-f16.gguf"
    q4_path = work / f"{mid}-Q4_K_M.gguf"

    merge_adapter_to_hf(
        base_hf_id=base_hf_id, adapter_dir=adapter_dir, merged_dir=merged_dir
    )
    # Prefer GPU venv python for convert deps if available.
    convert_python = os.environ.get("NANO_ORCH_PYTHON")
    if not convert_python:
        gpu_py = REPO_ROOT / ".venv-gpu" / "bin" / "python"
        if gpu_py.is_file():
            os.environ["NANO_ORCH_PYTHON"] = str(gpu_py)

    f16 = convert_hf_to_gguf(merged_dir, f16_path)
    q4 = quantize_gguf(f16, q4_path)
    manifest = {
        "model_id": mid,
        "language": language,
        "base_hf_id": base_hf_id,
        "adapter_dir": str(adapter_dir),
        "merged_dir": str(merged_dir),
        "f16_gguf": str(f16),
        "q4_gguf": str(q4),
    }
    (work / "export-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return GgufExportResult(
        merged_dir=merged_dir, f16_gguf=f16, q4_gguf=q4, model_id=mid
    )


def register_in_bonsai_models(
    *,
    models_json: Path,
    model_id: str,
    gguf_path: Path,
    label: str,
    ngl: int = 99,
    ctx: int = 8192,
) -> None:
    """Register or update a GGUF entry in bonsai-chat models.json."""
    payload = json.loads(models_json.read_text(encoding="utf-8"))
    models = payload.setdefault("models", [])
    # Store path relative to repo .local when possible.
    local_root = REPO_ROOT / ".local"
    try:
        rel = gguf_path.resolve().relative_to(local_root.resolve())
        path_value = str(rel).replace("\\", "/")
    except ValueError:
        path_value = str(gguf_path.resolve())

    entry = {
        "id": model_id,
        "label": label,
        "kind": "gguf",
        "path": path_value if path_value.startswith("models/") else str(gguf_path.resolve()),
        "bin": "llama-prism-cuda/llama-server",
        "ngl": ngl,
        "ctx": ctx,
        "vision": False,
        "thinking": False,
        "notes": "nano-orchestrator Phase 3 fine-tuned worker",
    }
    # Prefer copying into .local/models/<id>/ for consistent layout.
    dest_dir = local_root / "models" / model_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_gguf = dest_dir / gguf_path.name
    if gguf_path.resolve() != dest_gguf.resolve():
        shutil.copy2(gguf_path, dest_gguf)
    entry["path"] = f"models/{model_id}/{dest_gguf.name}"

    replaced = False
    for i, existing in enumerate(models):
        if existing.get("id") == model_id:
            models[i] = {**existing, **entry}
            replaced = True
            break
    if not replaced:
        models.append(entry)
    models_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def register_in_orchestrator_config(
    *,
    config_path: Path,
    language: str,
    model_id: str,
    gguf_path: Path,
) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {}
    if config_path.is_file():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    workers = payload.setdefault("fine_tuned_workers", {})
    workers[language] = {
        "model_id": model_id,
        "gguf_path": str(gguf_path.resolve()),
        "base": "qwen25-coder-0.5b",
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
