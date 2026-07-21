"""Judge-approved training example schema (Phase 3)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SourceKind = Literal[
    "judge_log",
    "proposal",
    "gold_seed",
    "teacher_distill",
]


class TrainExample(BaseModel):
    """One SFT pair for a specialized worker."""

    id: str
    language: Literal["javascript", "html", "freemarker"]
    instruction: str
    code: str
    source: SourceKind
    task_id: str | None = None
    model_id: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_sft_text(self) -> str:
        return (
            "### Instruction:\n"
            f"{self.instruction.strip()}\n\n"
            "### Response:\n"
            f"{self.code.strip()}"
        )

    def to_jsonl_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
