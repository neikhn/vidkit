from __future__ import annotations

from typing import Any

from .captions import build_caption_cues


SCENE_TYPES = ["headline", "tool-identity", "process", "comparison", "takeaway"]


def build_timeline(
    transcript: dict[str, Any],
    title: str,
    language: str,
    audio_src: str,
) -> dict[str, Any]:
    words = transcript.get("words", [])
    if not words:
        raise ValueError("Cannot build a timeline without timed words")
    cues = build_caption_cues(words)
    duration_ms = max(round(float(words[-1]["end"]) * 1000) + 350, 1000)
    scenes: list[dict[str, Any]] = []
    scene_count = min(len(SCENE_TYPES), max(1, len(cues)))
    cues_per_scene = max(1, (len(cues) + scene_count - 1) // scene_count)
    for index in range(scene_count):
        owned = cues[index * cues_per_scene : (index + 1) * cues_per_scene]
        if not owned:
            continue
        scenes.append(
            {
                "id": f"scene-{index + 1}",
                "type": SCENE_TYPES[index],
                "title": title if index == 0 else owned[0].text,
                "body": " ".join(cue.text for cue in owned),
                "startMs": owned[0].start_ms,
                "endMs": owned[-1].end_ms,
                "status": "provisional",
            }
        )
    return {
        "schemaVersion": 1,
        "language": language,
        "title": title,
        "audioSrc": audio_src,
        "durationSeconds": duration_ms / 1000,
        "captions": [cue.to_dict() for cue in cues],
        "scenes": scenes,
        "storyboardStatus": "provisional",
        "notes": ["Scene selection is a deterministic draft; editorial storyboard review is still required."],
    }
