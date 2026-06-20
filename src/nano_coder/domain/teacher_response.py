import json
import re
from typing import Any, Protocol


class TeacherResponse:
    __slots__ = ("text", "input_tokens", "output_tokens", "model")

    def __init__(self, text: str, input_tokens: int, output_tokens: int, model: str) -> None:
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model = model


class TeacherClient(Protocol):
    def complete(self, *, system: str, user: str) -> TeacherResponse: ...


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a single JSON object from teacher output."""
    cleaned = text.strip()
    cleaned = _JSON_FENCE.sub("", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in teacher response")
    return json.loads(cleaned[start : end + 1])
