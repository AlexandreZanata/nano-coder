import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class SeedTaxonomy:
    version: str
    difficulty_tags: frozenset[str]
    domain_tags: dict[TargetLanguage, frozenset[str]]
    metadata_required_fields: tuple[str, ...]
    allowed_sources: frozenset[str]
    seed_id_pattern: re.Pattern[str]
    reference_id_pattern: re.Pattern[str]
    synthetic_id_pattern: re.Pattern[str]
    instruction_min_length: int
    code_min_length: int
    tags_min_count: int


def load_seed_taxonomy(path: Path) -> SeedTaxonomy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    domain_tags: dict[TargetLanguage, frozenset[str]] = {}
    for lang_name, tags in raw["domainTags"].items():
        domain_tags[TargetLanguage(lang_name)] = frozenset(tags)

    return SeedTaxonomy(
        version=raw["version"],
        difficulty_tags=frozenset(raw["difficultyTags"]),
        domain_tags=domain_tags,
        metadata_required_fields=tuple(raw["metadata"]["requiredFields"]),
        allowed_sources=frozenset(raw["metadata"]["allowedSources"]),
        seed_id_pattern=re.compile(raw["idPatterns"]["seed"]),
        reference_id_pattern=re.compile(raw["idPatterns"]["reference"]),
        synthetic_id_pattern=re.compile(raw["idPatterns"]["synthetic"]),
        instruction_min_length=raw["limits"]["instructionMinLength"],
        code_min_length=raw["limits"]["codeMinLength"],
        tags_min_count=raw["limits"]["tagsMinCount"],
    )
