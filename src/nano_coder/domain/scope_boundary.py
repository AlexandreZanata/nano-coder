import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class TrainingTopic:
    id: str
    language: TargetLanguage
    difficulty: str
    tags: tuple[str, ...]
    pattern: str


@dataclass(frozen=True)
class HeldOutTopic:
    id: str
    language: TargetLanguage
    pattern: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class ScopeBoundary:
    version: str
    held_out_test_set_version: str
    training_topics: tuple[TrainingTopic, ...]
    held_out_topics: tuple[HeldOutTopic, ...]
    out_of_scope_phase1: dict[TargetLanguage, tuple[str, ...]]

    @property
    def held_out_topic_ids(self) -> frozenset[str]:
        return frozenset(topic.id for topic in self.held_out_topics)

    @property
    def training_topic_ids(self) -> frozenset[str]:
        return frozenset(topic.id for topic in self.training_topics)

    def held_out_topics_for(self, language: TargetLanguage) -> tuple[HeldOutTopic, ...]:
        return tuple(t for t in self.held_out_topics if t.language == language)


class HeldOutLeakDetected(Exception):
    """BR-004 — training or synthetic input overlaps held-out boundary."""

    def __init__(self, example_id: str, topic_id: str, matched_keyword: str) -> None:
        self.example_id = example_id
        self.topic_id = topic_id
        self.matched_keyword = matched_keyword
        super().__init__(
            f"HeldOutLeakDetected: example '{example_id}' matches held-out topic "
            f"'{topic_id}' via keyword '{matched_keyword}'"
        )


def _keyword_matches(keyword: str, haystack: str) -> bool:
    """Match phrases literally; match tokens on identifier boundaries to reduce false positives."""
    if " " in keyword:
        return keyword in haystack
    if len(keyword) < 4:
        return False
    pattern = rf"(?<![a-z0-9_]){re.escape(keyword)}(?![a-z0-9_])"
    return re.search(pattern, haystack) is not None


def load_scope_boundary(path: Path) -> ScopeBoundary:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    out_of_scope: dict[TargetLanguage, tuple[str, ...]] = {}
    for lang_name, config in raw["targetLanguages"].items():
        language = TargetLanguage(lang_name)
        out_of_scope[language] = tuple(config.get("outOfScopePhase1", []))

    training_topics = tuple(
        TrainingTopic(
            id=item["id"],
            language=TargetLanguage(item["language"]),
            difficulty=item["difficulty"],
            tags=tuple(item["tags"]),
            pattern=item["pattern"],
        )
        for item in raw["trainingTopics"]
    )

    held_out_topics = tuple(
        HeldOutTopic(
            id=item["id"],
            language=TargetLanguage(item["language"]),
            pattern=item["pattern"],
            keywords=tuple(k.lower() for k in item["keywords"]),
        )
        for item in raw["heldOutTopics"]
    )

    return ScopeBoundary(
        version=raw["version"],
        held_out_test_set_version=raw["heldOutTestSetVersion"],
        training_topics=training_topics,
        held_out_topics=held_out_topics,
        out_of_scope_phase1=out_of_scope,
    )


def detect_held_out_leak(
    scope: ScopeBoundary,
    *,
    example_id: str,
    instruction: str,
    code: str,
    topic_id: str | None = None,
    target_language: TargetLanguage | None = None,
) -> None:
    """Raise HeldOutLeakDetected when example overlaps held-out boundary (BR-004)."""
    if topic_id and topic_id in scope.held_out_topic_ids:
        raise HeldOutLeakDetected(example_id, topic_id, topic_id)

    haystack = f"{instruction}\n{code}".lower()
    topics = scope.held_out_topics
    if target_language is not None:
        topics = scope.held_out_topics_for(target_language)

    for topic in topics:
        for keyword in topic.keywords:
            if _keyword_matches(keyword, haystack):
                raise HeldOutLeakDetected(example_id, topic.id, keyword)
