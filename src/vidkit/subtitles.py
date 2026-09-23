from __future__ import annotations

from typing import Any


def render_srt(cues: list[dict[str, Any]]) -> str:
    blocks = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n{_timestamp(cue['startMs'], ',')} --> {_timestamp(cue['endMs'], ',')}\n{cue['text']}"
        )
    return "\n\n".join(blocks) + "\n"


def render_vtt(cues: list[dict[str, Any]]) -> str:
    blocks = ["WEBVTT"]
    for cue in cues:
        blocks.append(
            f"{_timestamp(cue['startMs'], '.')} --> {_timestamp(cue['endMs'], '.')}\n{cue['text']}"
        )
    return "\n\n".join(blocks) + "\n"


def _timestamp(milliseconds: int, separator: str) -> str:
    total = max(0, int(milliseconds))
    hours, remainder = divmod(total, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"
