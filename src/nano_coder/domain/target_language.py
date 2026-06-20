from enum import StrEnum


class TargetLanguage(StrEnum):
    JAVASCRIPT = "JavaScript"
    HTML = "HTML"
    FREEMARKER = "FreeMarker"

    @classmethod
    def values(cls) -> frozenset[str]:
        return frozenset(member.value for member in cls)
