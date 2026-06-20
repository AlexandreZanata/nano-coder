"""Data schedule for training runs (TRAINING-METHODS.md, BR-012)."""

from enum import StrEnum


class DataSchedule(StrEnum):
    MIXED_LANGUAGES = "MixedLanguages"
    INCREMENTAL_BY_LANGUAGE = "IncrementalByLanguage"
