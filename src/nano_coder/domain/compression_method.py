"""Compression methods for training runs (TRAINING-METHODS.md)."""

from enum import StrEnum


class CompressionMethod(StrEnum):
    FEW_SHOT = "FewShot"
    LORA = "LoRA"
    QLORA = "QLoRA"
    DORA = "DoRA"
