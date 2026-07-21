"""Sandbox executor port."""

from __future__ import annotations

from typing import Protocol

from nano_orchestrator.domain.entities import MicroTask
from nano_orchestrator.domain.result import Result


class SandboxExecutor(Protocol):
    def run_checks(self, task: MicroTask, code: str) -> Result[dict[str, bool], str]:
        """Return map of check_name -> passed."""
        ...
