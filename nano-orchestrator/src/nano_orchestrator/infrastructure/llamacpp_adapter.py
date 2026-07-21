"""llama.cpp OpenAI-compatible /completion adapter (Phase 2)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from nano_orchestrator.domain.result import Err, Ok, Result


class LlamaCppAdapter:
    """Talks to llama-server HTTP API (same stack as bonsai-chat)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8081") -> None:
        self._base_url = base_url.rstrip("/")

    def generate(self, prompt: str, *, max_tokens: int = 512) -> Result[str, str]:
        payload = json.dumps(
            {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": 0.2,
                "stop": ["</s>", "<|im_end|>"],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/completion",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return Err(f"llamacpp_unreachable:{exc}")
        except TimeoutError:
            return Err("llamacpp_timeout")
        content = body.get("content")
        if not isinstance(content, str):
            return Err("llamacpp_bad_response")
        return Ok(content)
