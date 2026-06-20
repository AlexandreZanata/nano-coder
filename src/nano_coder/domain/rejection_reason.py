"""Rejection reason codes for synthetic quality gates (Stage 5, playbook)."""

from enum import StrEnum


class RejectionReasonCode(StrEnum):
    SCHEMA_INVALID = "SCHEMA_INVALID"
    SYNTAX_FAIL = "SYNTAX_FAIL"
    LINT_FAIL = "LINT_FAIL"
    HELD_OUT_LEAK = "HELD_OUT_LEAK"
    DUPLICATE = "DUPLICATE"
    LOW_JUDGE_SCORE = "LOW_JUDGE_SCORE"
    QUALITY_BAR = "QUALITY_BAR"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
