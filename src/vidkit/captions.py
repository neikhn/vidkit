from __future__ import annotations

import re
from typing import Any

from .models import CaptionCue, CaptionToken


def build_caption_cues(
    words: list[dict[str, Any]],
    max_chars: int = 34,
    max_words: int = 7,
    gap_threshold: float = 0.38,
) -> list[CaptionCue]:
    cues: list[CaptionCue] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        if not current:
            return
        text = _render_text([item["text"] for item in current])
        tokens = [
            CaptionToken(item["text"], round(item["start"] * 1000), round(item["end"] * 1000))
            for item in current
        ]
        cues.append(CaptionCue(text, tokens[0].start_ms, tokens[-1].end_ms, tokens))
        current.clear()

    for word in words:
        if not str(word.get("text", "")).strip():
            continue
        if current:
            gap = float(word["start"]) - float(current[-1]["end"])
            candidate = _render_text([item["text"] for item in current] + [word["text"]])
            if gap >= gap_threshold or len(current) >= max_words or len(candidate) > max_chars:
                flush()
        current.append(word)
        if re.search(r"[.!?…]$", str(word["text"])):
            flush()
    flush()
    return cues


def _render_text(tokens: list[str]) -> str:
    output = ""
    for token in tokens:
        if output and not re.match(r"^[,.;:!?)]", token):
            output += " "
        output += token
    return output
