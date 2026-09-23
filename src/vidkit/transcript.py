from __future__ import annotations

import json
import math
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .models import TimedWord, ValidationFinding


LANGUAGE_ALIASES = {"eng": "en", "vie": "vi", "en-us": "en", "en-gb": "en"}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("Transcript JSON must be an object")
    return payload


def normalize_transcript(payload: dict[str, Any]) -> dict[str, Any]:
    raw_language = str(payload.get("language_code") or payload.get("language") or "unknown")
    language = LANGUAGE_ALIASES.get(raw_language.lower(), raw_language.lower())
    words: list[TimedWord] = []

    if isinstance(payload.get("segments"), list):
        for segment_index, segment in enumerate(payload["segments"]):
            for word_index, raw_word in enumerate(segment.get("words") or []):
                word = _parse_word(raw_word, segment_index, word_index)
                if word:
                    words.append(word)
    elif isinstance(payload.get("words"), list):
        for word_index, raw_word in enumerate(payload["words"]):
            word = _parse_word(raw_word, None, word_index)
            if word:
                words.append(word)
    else:
        raise ValueError("Unsupported transcript shape: expected words or segments[].words")

    spoken_words = [word for word in words if word.text.strip() and word.kind == "word"]
    events = [word for word in words if word.kind != "word"]
    text = payload.get("text") or _join_words(spoken_words)
    return {
        "schema_version": 1,
        "provider": "elevenlabs",
        "language": language,
        "raw_language": raw_language,
        "text": text,
        "words": [word.to_dict() for word in spoken_words],
        "events": [word.to_dict() for word in events],
        "source_shape": "segments" if "segments" in payload else "words",
    }


def validate_transcript(
    normalized: dict[str, Any],
    expected_spoken_text: str | None = None,
    audio_duration: float | None = None,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    previous_start = -1.0
    for index, word in enumerate(normalized.get("words", [])):
        start = word.get("start")
        end = word.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            findings.append(ValidationFinding("invalid-time", "error", f"Word {index} has non-numeric timing"))
            continue
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
            findings.append(ValidationFinding("invalid-time", "error", f"Word {index} has invalid timing {start}-{end}"))
        if start < previous_start:
            findings.append(ValidationFinding("out-of-order", "error", f"Word {index} starts before the previous word"))
        if audio_duration is not None and end > audio_duration + 0.1:
            findings.append(ValidationFinding("past-audio", "error", f"Word {index} ends after the audio"))
        previous_start = start

    if not normalized.get("words"):
        findings.append(ValidationFinding("no-words", "error", "Transcript contains no spoken word timing"))

    if expected_spoken_text:
        actual = " ".join(word["text"] for word in normalized.get("words", []))
        ratio = SequenceMatcher(None, _canonical(expected_spoken_text), _canonical(actual)).ratio()
        if ratio < 0.90:
            severity = "error" if ratio < 0.75 else "warning"
            findings.append(
                ValidationFinding(
                    "script-mismatch",
                    severity,
                    f"Transcript similarity to expected speech is {ratio:.1%}; review names, quantities and omissions",
                )
            )
    return findings


def _parse_word(raw: dict[str, Any], segment_index: int | None, word_index: int) -> TimedWord | None:
    text = str(raw.get("text", ""))
    if not text.strip():
        return None
    start = raw.get("start", raw.get("start_time"))
    end = raw.get("end", raw.get("end_time"))
    if start is None or end is None:
        return None
    raw_type = str(raw.get("type", "word"))
    kind = "word" if raw_type in {"word", "spacing"} else raw_type
    return TimedWord(text, float(start), float(end), segment_index, word_index, kind)


def _join_words(words: list[TimedWord]) -> str:
    output = ""
    for word in words:
        if output and not re.match(r"^[,.;:!?)]", word.text):
            output += " "
        output += word.text
    return output.strip()


def _canonical(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())
