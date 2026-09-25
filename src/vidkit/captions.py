from __future__ import annotations

import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import ImageFont
from .models import CaptionCue, CaptionToken


WEAK_END = {"a", "an", "the", "and", "or", "but", "of", "to", "at", "for", "with",
            "in", "on", "by", "from", "và", "là", "của", "ở", "với", "cho", "từ", "đến"}
UNITS = {"ms", "milliseconds", "seconds", "tokens", "px", "%", "usd", "dollars", "triệu", "giây"}


def _render_text(tokens: list[str]) -> str:
    output = ""
    for token in tokens:
        token = unicodedata.normalize("NFC", str(token).strip())
        if output and not re.match(r"^[,.;:!?…%)\]}]", token) and not output.endswith(("(", "$")):
            output += " "
        output += token
    return output


@lru_cache(maxsize=1)
def _caption_font() -> ImageFont.FreeTypeFont:
    font = Path(__file__).resolve().parents[2] / "renderer" / "library" / "fonts" / "NotoSans-Bold.ttf"
    return ImageFont.truetype(str(font), 48)


def _width(value: str) -> float:
    return _caption_font().getlength(value)


def _line_split(tokens: list[str], max_width: int = 756) -> list[str] | None:
    text = _render_text(tokens)
    if _width(text) <= max_width:
        return [text]
    options: list[tuple[float, list[str]]] = []
    for pivot in range(2, len(tokens) - 1):
        left = _render_text(tokens[:pivot])
        right = _render_text(tokens[pivot:])
        if max(_width(left), _width(right)) > max_width:
            continue
        penalty = abs(_width(left) - _width(right)) * 0.025
        if tokens[pivot - 1].casefold().strip(".,") in WEAK_END:
            penalty += 30
        if tokens[pivot].casefold().strip(".,") in UNITS and re.search(r"\d$", left):
            penalty += 30
        if len(tokens[pivot:]) == 1:
            penalty += 50
        options.append((penalty, [left, right]))
    return min(options, key=lambda option: option[0])[1] if options else None


def _cue_cost(words: list[dict[str, Any]], start: int, end: int) -> tuple[float, list[str] | None]:
    if any(re.search(r"[.!?…]$", str(words[index]["text"])) and
           float(words[index + 1]["start"]) - float(words[index]["end"]) > 0.25
           for index in range(start, end - 1)):
        return math.inf, None
    tokens = [str(word["text"]) for word in words[start:end]]
    lines = _line_split(tokens)
    if lines is None:
        return math.inf, None
    duration = float(words[end - 1]["end"]) - float(words[start]["start"])
    if duration > 4.2 or len(tokens) > 14:
        return math.inf, None
    cost = abs(duration - 1.9) * 2
    if duration < 0.45:
        cost += 18
    if len(tokens) == 1:
        cost += 28
    if len(lines) == 2:
        cost += abs(_width(lines[0]) - _width(lines[1])) * 0.025
    last = tokens[-1].casefold().strip(".,")
    if last in WEAK_END:
        cost += 28
    if re.search(r"[.!?…]$", tokens[-1]):
        cost -= 9
    if end < len(words):
        gap = float(words[end]["start"]) - float(words[end - 1]["end"])
        if gap > 0.32:
            cost -= min(gap * 12, 12)
        elif re.search(r"[.!?…]$", tokens[-1]):
            cost -= 2
    return cost, lines


def build_caption_cues(
    words: list[dict[str, Any]],
    max_chars: int = 37,
    max_words: int = 14,
    gap_threshold: float = 0.38,
    plan: dict[str, Any] | None = None,
) -> list[CaptionCue]:
    del max_chars, max_words, gap_threshold
    words = [word for word in words if str(word.get("text", "")).strip()]
    if not words:
        return []
    ranges: list[tuple[int, int]]
    if plan:
        groups = plan.get("groups")
        if not isinstance(groups, list) or not groups:
            raise ValueError("Caption plan requires non-empty groups")
        ranges = []
        next_start = 0
        for group in groups:
            start = group.get("startWord")
            end = group.get("endWord")
            if not isinstance(start, int) or not isinstance(end, int) or start != next_start or end < start or end >= len(words):
                raise ValueError("Caption groups must cover transcript words once, in order")
            ranges.append((start, end + 1))
            next_start = end + 1
        if next_start != len(words):
            raise ValueError("Caption groups must cover every transcript word")
    else:
        best = [math.inf] * (len(words) + 1)
        next_end = [0] * len(words)
        best[-1] = 0
        for start in range(len(words) - 1, -1, -1):
            for end in range(start + 1, min(len(words), start + 14) + 1):
                cost, _ = _cue_cost(words, start, end)
                total = cost + 8 + best[end]
                if total < best[start]:
                    best[start], next_end[start] = total, end
        if not math.isfinite(best[0]):
            raise ValueError("Caption cannot fit in two lines; revise transcript or caption plan")
        ranges = []
        start = 0
        while start < len(words):
            end = next_end[start]
            ranges.append((start, end))
            start = end
    cues: list[CaptionCue] = []
    for index, (start, end) in enumerate(ranges):
        group = plan["groups"][index] if plan else {}
        display_tokens = group.get("displayTokens")
        if display_tokens:
            if not isinstance(display_tokens, list):
                raise ValueError("displayTokens must be a list")
            next_word = start
            tokens = []
            for display in display_tokens:
                first, last = display.get("startWord"), display.get("endWord")
                if not isinstance(first, int) or not isinstance(last, int) or first != next_word or last < first or last >= end:
                    raise ValueError("Display tokens must cover their caption group once, in order")
                spoken = _render_text([str(word["text"]) for word in words[first:last + 1]])
                if unicodedata.normalize("NFKC", str(display.get("spokenText", ""))).casefold() != unicodedata.normalize("NFKC", spoken).casefold():
                    raise ValueError(f"Display mapping spokenText does not match transcript words {first}-{last}")
                text = str(display.get("text", "")).strip()
                if not text:
                    raise ValueError("Display token text is required")
                tokens.append(CaptionToken(text, round(float(words[first]["start"]) * 1000),
                                           round(float(words[last]["end"]) * 1000)))
                next_word = last + 1
            if next_word != end:
                raise ValueError("Display tokens must cover their caption group")
        else:
            tokens = [CaptionToken(str(word["text"]), round(float(word["start"]) * 1000), round(float(word["end"]) * 1000))
                      for word in words[start:end]]
        tokens_text = [token.text for token in tokens]
        lines = _line_split(tokens_text)
        if not lines:
            raise ValueError(f"Caption group {index + 1} does not fit in two lines")
        next_start = round(float(words[end]["start"]) * 1000) if end < len(words) else tokens[-1].end_ms + 120
        cue_end = min(tokens[-1].end_ms + 120, next_start)
        cues.append(CaptionCue(_render_text(tokens_text), tokens[0].start_ms, cue_end, tokens, lines, start, end - 1))
    return cues
