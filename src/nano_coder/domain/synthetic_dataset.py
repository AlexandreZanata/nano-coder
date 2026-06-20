"""SyntheticDataset publication state (Stage 7, UC-002)."""

from __future__ import annotations

from enum import StrEnum


class SyntheticDatasetState(StrEnum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"
