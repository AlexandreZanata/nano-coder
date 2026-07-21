"""Domain entities — MicroTask contracts (pure, no I/O)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TargetLanguage(str, Enum):
    JAVASCRIPT = "javascript"
    HTML = "html"
    FREEMARKER = "freemarker"
    CSS = "css"


class WorkerRole(str, Enum):
    CODER = "coder"
    FORMATTER = "formatter"
    LINTER = "linter"


class MicroTask(BaseModel):
    id: str
    role: WorkerRole
    language: TargetLanguage
    prompt: str
    context: str | None = None
    constraints: list[str] = Field(default_factory=list)
    acceptance: list[str]
    max_tokens: int = 512


class WorkerResponse(BaseModel):
    task_id: str
    code: str
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str | None = None
    latency_ms: int
    tokens_used: int


class JudgeVerdict(BaseModel):
    task_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    checks: dict[str, bool]
    retry_recommended: bool
    feedback: str | None = None
