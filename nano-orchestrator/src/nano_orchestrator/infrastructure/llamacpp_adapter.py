"""llama.cpp server adapter with latency + token metadata."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from nano_orchestrator.domain.result import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class GenerationResult:
    text: str
    latency_ms: int
    tokens_predicted: int
    tokens_per_sec: float | None


class LlamaCppAdapter:
    """Talks to llama-server HTTP `/completion` API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8081") -> None:
        self._base_url = base_url.rstrip("/")

    def health(self) -> Result[bool, str]:
        try:
            req = urllib.request.Request(f"{self._base_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return Ok(resp.status == 200)
        except urllib.error.URLError as exc:
            return Err(f"llamacpp_unreachable:{exc}")

    def generate(self, prompt: str, *, max_tokens: int = 512) -> Result[str, str]:
        detailed = self.generate_detailed(prompt, max_tokens=max_tokens)
        if detailed.is_err():
            return Err(detailed.error)  # type: ignore[union-attr]
        return Ok(detailed.value.text)  # type: ignore[union-attr]

    def generate_detailed(
        self, prompt: str, *, max_tokens: int = 512
    ) -> Result[GenerationResult, str]:
        payload = json.dumps(
            {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": 0.2,
                "stop": [
                    "</s>",
                    "<|im_end|>",
                    "<|endoftext|>",
                    "<end_of_turn>",
                    "<think>",
                    "</think>",
                    "\n<think>",
                ],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/completion",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return Err(f"llamacpp_unreachable:{exc}")
        except TimeoutError:
            return Err("llamacpp_timeout")
        latency_ms = int((time.perf_counter() - started) * 1000)
        content = body.get("content")
        if not isinstance(content, str):
            return Err("llamacpp_bad_response")
        tokens = int(body.get("tokens_predicted") or body.get("completion_tokens") or 0)
        tps = None
        if isinstance(body.get("timings"), dict):
            pred = body["timings"].get("predicted_per_second")
            if isinstance(pred, (int, float)):
                tps = float(pred)
        elif tokens > 0 and latency_ms > 0:
            tps = tokens / (latency_ms / 1000.0)
        return Ok(
            GenerationResult(
                text=content,
                latency_ms=latency_ms,
                tokens_predicted=tokens,
                tokens_per_sec=tps,
            )
        )
