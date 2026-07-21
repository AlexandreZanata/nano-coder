"""LLM backend port — Application depends on this, not on Ollama/llama.cpp."""

from __future__ import annotations

from typing import Protocol

from nano_orchestrator.domain.result import Result


class LlmBackend(Protocol):
    def generate(self, prompt: str, *, max_tokens: int = 512) -> Result[str, str]:
        """Return model text or Err with a stable error code string."""
        ...
