"""GPU stack availability checks."""

from __future__ import annotations


class GpuStackUnavailableError(Exception):
    """Required torch/transformers/peft stack is not installed or CUDA missing."""


def is_gpu_stack_available(*, require_cuda: bool = True) -> bool:
    try:
        import torch
    except ImportError:
        return False
    if require_cuda and not torch.cuda.is_available():
        return False
    try:
        import peft  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def require_gpu_stack(*, require_cuda: bool = True) -> None:
    if not is_gpu_stack_available(require_cuda=require_cuda):
        raise GpuStackUnavailableError(
            "Install GPU stack: pip install -r requirements-gpu.txt && make health-gpu"
        )


def peak_vram_gb() -> float:
    import torch

    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated() / (1024**3)


def reset_peak_vram_stats() -> None:
    import torch

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()
