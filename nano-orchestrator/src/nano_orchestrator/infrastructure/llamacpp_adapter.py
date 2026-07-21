"""llama.cpp server adapter with latency + token metadata + call log."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.infrastructure.llm_call_log import append_llm_call

DEFAULT_STOP = (
    "</s>",
    "<|im_end|>",
    "<|endoftext|>",
    "<end_of_turn>",
    "<think>",
    "</think>",
    "\n<think>",
)


@dataclass(frozen=True, slots=True)
class GenerationResult:
    text: str
    latency_ms: int
    tokens_predicted: int
    tokens_per_sec: float | None


class LlamaCppAdapter:
    """Talks to llama-server HTTP `/completion` API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8081",
        *,
        model_id: str = "unknown",
        timeout_s: float = 180.0,
        temperature: float = 0.2,
        stop: tuple[str, ...] = DEFAULT_STOP,
        log_calls: bool = True,
        log_path: Path | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_id = model_id
        self._timeout_s = timeout_s
        self._temperature = temperature
        self._stop = list(stop)
        self._log_calls = log_calls
        self._log_path = log_path

    def health(self) -> Result[bool, str]:
        try:
            req = urllib.request.Request(f"{self._base_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=min(5.0, self._timeout_s)) as resp:
                return Ok(200 <= resp.status < 300)
        except urllib.error.URLError as exc:
            return Err(f"llamacpp_unreachable:{exc}")
        except TimeoutError:
            return Err("llamacpp_health_timeout")

    def generate(self, prompt: str, *, max_tokens: int = 512) -> Result[str, str]:
        detailed = self.generate_detailed(prompt, max_tokens=max_tokens)
        if detailed.is_err():
            return Err(detailed.error)  # type: ignore[union-attr]
        return Ok(detailed.value.text)  # type: ignore[union-attr]

    def generate_detailed(
        self, prompt: str, *, max_tokens: int = 512
    ) -> Result[GenerationResult, str]:
        if not prompt.strip():
            return Err("empty_prompt")
        if max_tokens < 1:
            return Err("invalid_max_tokens")
        payload = json.dumps(
            {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": self._temperature,
                "stop": self._stop,
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
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._maybe_log(prompt, latency_ms, ok=False, error=f"llamacpp_http:{exc.code}")
            return Err(f"llamacpp_http:{exc.code}")
        except urllib.error.URLError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._maybe_log(prompt, latency_ms, ok=False, error=f"llamacpp_unreachable:{exc}")
            return Err(f"llamacpp_unreachable:{exc}")
        except TimeoutError:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._maybe_log(prompt, latency_ms, ok=False, error="llamacpp_timeout")
            return Err("llamacpp_timeout")
        except json.JSONDecodeError:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._maybe_log(prompt, latency_ms, ok=False, error="llamacpp_bad_json")
            return Err("llamacpp_bad_json")
        latency_ms = int((time.perf_counter() - started) * 1000)
        content = body.get("content")
        if not isinstance(content, str):
            self._maybe_log(prompt, latency_ms, ok=False, error="llamacpp_bad_response")
            return Err("llamacpp_bad_response")
        tokens = int(body.get("tokens_predicted") or body.get("completion_tokens") or 0)
        tps = None
        if isinstance(body.get("timings"), dict):
            pred = body["timings"].get("predicted_per_second")
            if isinstance(pred, (int, float)):
                tps = float(pred)
        elif tokens > 0 and latency_ms > 0:
            tps = tokens / (latency_ms / 1000.0)
        self._maybe_log(prompt, latency_ms, ok=True, tokens_predicted=tokens)
        return Ok(
            GenerationResult(
                text=content,
                latency_ms=latency_ms,
                tokens_predicted=tokens,
                tokens_per_sec=tps,
            )
        )

    def _maybe_log(
        self,
        prompt: str,
        latency_ms: int,
        *,
        ok: bool,
        tokens_predicted: int | None = None,
        error: str | None = None,
    ) -> None:
        if not self._log_calls:
            return
        append_llm_call(
            model_id=self._model_id,
            prompt=prompt,
            latency_ms=latency_ms,
            ok=ok,
            tokens_predicted=tokens_predicted,
            error=error,
            log_path=self._log_path,
        )
