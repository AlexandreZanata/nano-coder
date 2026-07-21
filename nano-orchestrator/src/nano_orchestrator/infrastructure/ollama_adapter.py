"""Ollama adapter — alternate runtime for bake-off pulls."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from nano_orchestrator.domain.result import Err, Ok, Result


class OllamaAdapter:
    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        keep_alive: str = "0",
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._keep_alive = keep_alive

    def generate(self, prompt: str, *, max_tokens: int = 512) -> Result[str, str]:
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": self._keep_alive,
                "options": {"num_predict": max_tokens, "temperature": 0.2},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return Err(f"ollama_unreachable:{exc}")
        text = body.get("response")
        if not isinstance(text, str):
            return Err("ollama_bad_response")
        return Ok(text)
