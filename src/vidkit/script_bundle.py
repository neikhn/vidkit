from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


REQUIRED_TEXT_FIELDS = ("editorial_text", "expected_spoken_text", "tts_input")
ELEVEN_V3_CHARACTER_LIMIT = 5_000


def validate_script_bundle(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TEXT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    tts_input = payload.get("tts_input")
    expected = payload.get("expected_spoken_text")
    if not isinstance(tts_input, str) or not isinstance(expected, str):
        return errors
    if len(tts_input) > ELEVEN_V3_CHARACTER_LIMIT:
        errors.append(
            f"tts_input exceeds the Eleven v3 limit of {ELEVEN_V3_CHARACTER_LIMIT} characters"
        )
    if tts_input.count("[") != tts_input.count("]"):
        errors.append("tts_input contains an unbalanced Eleven v3 audio tag")

    spoken_tts = re.sub(r"\[[^\]\r\n]+\]", " ", tts_input)
    similarity = SequenceMatcher(None, _canonical(expected), _canonical(spoken_tts)).ratio()
    if similarity < 0.97:
        errors.append(
            "tts_input spoken text does not match expected_spoken_text after removing audio tags"
        )
    return errors


def _canonical(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())
