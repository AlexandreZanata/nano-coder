from typing import Any

from nano_coder.domain.scope_boundary import ScopeBoundary, detect_held_out_leak
from nano_coder.domain.seed_taxonomy import SeedTaxonomy
from nano_coder.domain.target_language import TargetLanguage

_LANG_PREFIX = {
    TargetLanguage.JAVASCRIPT: "js",
    TargetLanguage.HTML: "html",
    TargetLanguage.FREEMARKER: "fmt",
}


class SeedValidationError(Exception):
    """Gold seed record failed schema or taxonomy validation."""

    def __init__(self, seed_id: str, field: str, message: str) -> None:
        self.seed_id = seed_id
        self.field = field
        self.message = message
        super().__init__(f"SeedValidationError [{seed_id}] {field}: {message}")


def _require_string(record: dict[str, Any], field: str, seed_id: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SeedValidationError(seed_id, field, "must be a non-empty string")
    return value


def _validate_id(seed_id: str, taxonomy: SeedTaxonomy) -> None:
    if taxonomy.seed_id_pattern.match(seed_id) or taxonomy.reference_id_pattern.match(seed_id):
        return
    raise SeedValidationError(
        seed_id,
        "id",
        "must match seed-(js|html|fmt)-NNN or REF-(js|html|fmt)-NNN",
    )


def _validate_id_language_alignment(seed_id: str, language: TargetLanguage) -> None:
    prefix = _LANG_PREFIX[language]
    if f"-{prefix}-" in seed_id:
        return
    raise SeedValidationError(
        seed_id,
        "id",
        f"language prefix '{prefix}' must appear in id for {language.value}",
    )


def validate_gold_seed(
    record: dict[str, Any],
    taxonomy: SeedTaxonomy,
    *,
    scope: ScopeBoundary | None = None,
    require_metadata: bool = False,
) -> None:
    """Validate a GoldSeedExample dict. Raises SeedValidationError on failure."""
    seed_id = record.get("id", "<unknown>")
    if not isinstance(seed_id, str):
        raise SeedValidationError("<unknown>", "id", "must be a string")

    _validate_id(seed_id, taxonomy)

    lang_raw = record.get("targetLanguage")
    if lang_raw not in TargetLanguage.values():
        raise SeedValidationError(
            seed_id,
            "targetLanguage",
            "must be JavaScript, HTML, or FreeMarker",
        )
    language = TargetLanguage(lang_raw)
    _validate_id_language_alignment(seed_id, language)

    instruction = _require_string(record, "instruction", seed_id)
    if len(instruction) < taxonomy.instruction_min_length:
        raise SeedValidationError(
            seed_id,
            "instruction",
            f"must be at least {taxonomy.instruction_min_length} characters",
        )

    code = _require_string(record, "code", seed_id)
    if len(code) < taxonomy.code_min_length:
        raise SeedValidationError(
            seed_id,
            "code",
            f"must be at least {taxonomy.code_min_length} characters",
        )

    tags = record.get("tags")
    if not isinstance(tags, list) or len(tags) < taxonomy.tags_min_count:
        raise SeedValidationError(
            seed_id,
            "tags",
            f"must be an array with at least {taxonomy.tags_min_count} items",
        )

    tag_set = set()
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise SeedValidationError(seed_id, "tags", "each tag must be a non-empty string")
        tag_set.add(tag)

    difficulty_hits = tag_set & taxonomy.difficulty_tags
    if len(difficulty_hits) != 1:
        raise SeedValidationError(
            seed_id,
            "tags",
            "must include exactly one difficulty tag (L1-trivial … L4-edge-case)",
        )

    allowed_domain = taxonomy.domain_tags[language]
    if not tag_set & allowed_domain:
        raise SeedValidationError(
            seed_id,
            "tags",
            f"must include at least one domain tag for {language.value}",
        )

    metadata = record.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise SeedValidationError(seed_id, "metadata", "must be an object")
        for field in taxonomy.metadata_required_fields:
            value = metadata.get(field)
            if not isinstance(value, str) or not value.strip():
                raise SeedValidationError(seed_id, f"metadata.{field}", "is required")
        source = metadata["source"]
        if source not in taxonomy.allowed_sources:
            raise SeedValidationError(seed_id, "metadata.source", "invalid source value")
    elif require_metadata:
        raise SeedValidationError(seed_id, "metadata", "is required for promoted seeds")

    if scope is not None:
        detect_held_out_leak(
            scope,
            example_id=seed_id,
            instruction=instruction,
            code=code,
            target_language=language,
        )
