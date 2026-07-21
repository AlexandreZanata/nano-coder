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
DEFAULT_STOP_GRACE_S = float(os.environ.get("NANO_ORCH_STOP_GRACE_S", "1.0"))


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


def stop_server(port: int = 8081, *, grace_s: float | None = None) -> Result[None, str]:
    wait = DEFAULT_STOP_GRACE_S if grace_s is None else max(0.0, float(grace_s))
    subprocess.run(
        ["fuser", "-k", f"{port}/tcp"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if wait > 0:
        time.sleep(wait)
    return Ok(None)


def start_server(
    model_id: str,
    *,
    port: int = 8081,
    force_stop: bool = True,
    stop_grace_s: float | None = None,
) -> Result[str, str]:
    if not START_SH.is_file():
        return Err("start_script_missing")
    if force_stop:
        stop_server(port, grace_s=stop_grace_s)
    env = os.environ.copy()
    env["PORT"] = str(port)
    # Python already handled port kill/grace — avoid duplicate sleep in the shell script
    env["SKIP_PRE_KILL"] = "1"
    grace = DEFAULT_STOP_GRACE_S if stop_grace_s is None else max(0.0, float(stop_grace_s))
    env["STOP_SLEEP"] = str(grace)
    env["HEALTH_SLEEP"] = os.environ.get("NANO_ORCH_HEALTH_SLEEP", "0.2")
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
    adapter = LlamaCppAdapter(f"http://127.0.0.1:{port}", model_id=model_id)
    poll = float(env.get("HEALTH_SLEEP") or 0.2)
    for _ in range(120):
        health = adapter.health()
        if health.is_ok():
            return Ok(model_id)
        time.sleep(max(0.05, poll))
    return Err("start_unhealthy")
