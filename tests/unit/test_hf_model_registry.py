"""Unit tests for HF model id resolution."""

from __future__ import annotations

import pytest

from nano_coder.infrastructure.hf_model_registry import resolve_hf_model_id


def test_resolve_hf_model_id_short_name() -> None:
    assert resolve_hf_model_id("Qwen2.5-Coder-0.5B") == "Qwen/Qwen2.5-Coder-0.5B"


def test_resolve_hf_model_id_passthrough() -> None:
    assert resolve_hf_model_id("org/custom-model") == "org/custom-model"


def test_resolve_hf_model_id_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown student model"):
        resolve_hf_model_id("Not-A-Model")
