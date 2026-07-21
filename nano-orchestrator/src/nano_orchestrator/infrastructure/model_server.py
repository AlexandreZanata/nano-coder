"""Start/stop llama-server for VRAM policy (orchestrator unload)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter

ROOT = Path(__file__).resolve().parents[3]  # nano-orchestrator/
START_SH = ROOT / "scripts" / "start_model_server.sh"


def vram_used_mb() -> int | None:
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode != 0:
            return None
        vals = [int(x.strip()) for x in proc.stdout.splitlines() if x.strip()]
        return max(vals) if vals else None
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return None


def stop_server(port: int = 8081) -> Result[None, str]:
    subprocess.run(
        ["fuser", "-k", f"{port}/tcp"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)
    return Ok(None)


def start_server(model_id: str, *, port: int = 8081) -> Result[str, str]:
    if not START_SH.is_file():
        return Err("start_script_missing")
    stop_server(port)
    env = os.environ.copy()
    env["PORT"] = str(port)
    proc = subprocess.run(
        ["bash", str(START_SH), model_id],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
        env=env,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return Err(f"start_failed:{detail}")
    adapter = LlamaCppAdapter(f"http://127.0.0.1:{port}")
    for _ in range(60):
        health = adapter.health()
        if health.is_ok():
            return Ok(model_id)
        time.sleep(0.5)
    return Err("start_unhealthy")
