"""Metrics helpers for bake-off (pure)."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class LangStats:
    passed: int = 0
    total: int = 0
    latencies_ms: list[int] = field(default_factory=list)

    @property
    def pass_at_1(self) -> float | None:
        if self.total == 0:
            return None
        return self.passed / self.total


@dataclass
class BakeoffSummary:
    model_id: str
    role: str
    by_lang: dict[str, LangStats]
    vram_mb: int | None = None
    tokens_per_sec: float | None = None
    notes: str = ""

    def pass_at_1(self, lang: str) -> str:
        stats = self.by_lang.get(lang)
        if stats is None or stats.pass_at_1 is None:
            return ""
        return f"{stats.pass_at_1:.2f}"

    def p50_ms(self) -> str:
        all_lat: list[int] = []
        for stats in self.by_lang.values():
            all_lat.extend(stats.latencies_ms)
        if not all_lat:
            return ""
        return str(int(statistics.median(all_lat)))

    def overall_pass(self) -> float | None:
        p = sum(s.passed for s in self.by_lang.values())
        t = sum(s.total for s in self.by_lang.values())
        if t == 0:
            return None
        return p / t
