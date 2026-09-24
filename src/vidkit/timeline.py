from __future__ import annotations

import unicodedata
from typing import Any

from .captions import build_caption_cues


SCENE_TYPES = ["hook", "screenshot", "steps", "takeaway"]


def build_draft_timeline(
    transcript: dict[str, Any],
    title: str,
    language: str,
    audio_src: str,
) -> dict[str, Any]:
    words = transcript.get("words", [])
    if not words:
        raise ValueError("Cannot build a timeline without timed words")
    cues = build_caption_cues(words)
    duration_ms = _duration_ms(transcript, words)
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
                "layout": SCENE_TYPES[index],
                "purpose": "technical-draft",
                "title": _nfc(title if index == 0 else owned[0].text),
                "body": "",
                "startMs": 0 if index == 0 else owned[0].start_ms,
                "endMs": duration_ms if index == scene_count - 1 else owned[-1].end_ms,
                "status": "provisional",
                "asset": None,
            }
        )
    return _timeline_payload(
        language, title, audio_src, duration_ms, cues, scenes, "technical-draft", []
    )


def compile_storyboard(
    transcript: dict[str, Any],
    storyboard: dict[str, Any],
    asset_manifest: dict[str, Any],
    title: str,
    language: str,
    audio_src: str,
) -> tuple[dict[str, Any], list[str]]:
    words = transcript.get("words", [])
    if not words:
        raise ValueError("Cannot build a timeline without timed words")
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Storyboard must contain at least one scene")
    assets = {item.get("id"): item for item in asset_manifest.get("assets", [])}
    compiled: list[dict[str, Any]] = []
    missing_assets: list[str] = []
    previous_end = -1
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index + 1} must be an object")
        layout = str(scene.get("layout", ""))
        if layout not in SCENE_TYPES:
            raise ValueError(f"Scene {index + 1} has unsupported layout: {layout}")
        start_index = _anchor_index(scene.get("startAnchor"), words, "start", index)
        end_index = _anchor_index(scene.get("endAnchor"), words, "end", index)
        if start_index > end_index:
            raise ValueError(f"Scene {index + 1} starts after it ends")
        if index == 0 and start_index != 0:
            raise ValueError("Storyboard must start at word 0")
        if start_index != previous_end + 1:
            raise ValueError(f"Scene {index + 1} must begin at word {previous_end + 1}")
        previous_end = end_index
        asset_id = scene.get("assetId")
        required_asset = bool(scene.get("assetRequired", layout == "screenshot"))
        asset = assets.get(asset_id) if asset_id else None
        if required_asset and asset is None:
            missing_assets.append(str(asset_id or f"scene:{scene.get('id', index + 1)}"))
        compiled.append(
            {
                "id": str(scene.get("id") or f"scene-{index + 1}"),
                "layout": layout,
                "purpose": _nfc(str(scene.get("purpose") or "")),
                "title": _nfc(str(scene.get("title") or "")),
                "body": _nfc(str(scene.get("body") or "")),
                "startWord": start_index,
                "endWord": end_index,
                "startMs": 0 if index == 0 else round(float(words[start_index]["start"]) * 1000),
                "endMs": 0,
                "status": "blocked" if required_asset and asset is None else "checked",
                "asset": asset,
                "assetRequired": required_asset,
                "crop": _validate_crop(scene.get("crop"), index),
                "callout": scene.get("callout"),
            }
        )
    if previous_end != len(words) - 1:
        raise ValueError(f"Storyboard must end at word {len(words) - 1}")
    duration_ms = _duration_ms(transcript, words)
    for index, scene in enumerate(compiled):
        scene["endMs"] = compiled[index + 1]["startMs"] if index + 1 < len(compiled) else duration_ms
    cues = build_caption_cues(words)
    asset_warnings = list(
        dict.fromkeys(
            f"{scene['asset']['id']}: {warning}"
            for scene in compiled
            if scene.get("asset")
            for warning in scene["asset"].get("qualityWarnings", [])
        )
    )
    timeline = _timeline_payload(
        language,
        title,
        audio_src,
        duration_ms,
        cues,
        compiled,
        "blocked" if missing_assets else "checked",
        missing_assets,
    )
    timeline["assetWarnings"] = asset_warnings
    return timeline, missing_assets


def validate_storyboard_shape(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty list")
        return errors
    seen: set[str] = set()
    for index, scene in enumerate(scenes):
        label = f"scene {index + 1}"
        if not isinstance(scene, dict):
            errors.append(f"{label} must be an object")
            continue
        scene_id = str(scene.get("id") or "")
        if not scene_id:
            errors.append(f"{label} id is required")
        elif scene_id in seen:
            errors.append(f"duplicate scene id: {scene_id}")
        seen.add(scene_id)
        if scene.get("layout") not in SCENE_TYPES:
            errors.append(f"{label} layout must be one of: {', '.join(SCENE_TYPES)}")
        if not isinstance(scene.get("title"), str) or not scene["title"].strip():
            errors.append(f"{label} title is required")
        for anchor_name in ("startAnchor", "endAnchor"):
            anchor = scene.get(anchor_name)
            if not isinstance(anchor, dict) or not isinstance(anchor.get("wordIndex"), int):
                errors.append(f"{label} {anchor_name}.wordIndex is required")
        if scene.get("assetRequired") and not scene.get("assetId"):
            errors.append(f"{label} requires assetId")
        try:
            _validate_crop(scene.get("crop"), index)
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
    return errors


def _anchor_index(anchor: Any, words: list[dict[str, Any]], name: str, scene_index: int) -> int:
    if not isinstance(anchor, dict) or not isinstance(anchor.get("wordIndex"), int):
        raise ValueError(f"Scene {scene_index + 1} {name}Anchor.wordIndex is required")
    word_index = anchor["wordIndex"]
    if word_index < 0 or word_index >= len(words):
        raise ValueError(f"Scene {scene_index + 1} {name}Anchor is outside the transcript")
    expected = anchor.get("text")
    if expected and _canonical(str(expected)) != _canonical(str(words[word_index].get("text", ""))):
        raise ValueError(f"Scene {scene_index + 1} {name}Anchor text does not match word {word_index}")
    return word_index


def _validate_crop(crop: Any, scene_index: int) -> dict[str, float]:
    if crop is None:
        return {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}
    if not isinstance(crop, dict):
        raise ValueError(f"Scene {scene_index + 1} crop must be an object")
    result = {key: float(crop.get(key, default)) for key, default in (("x", 0), ("y", 0), ("width", 1), ("height", 1))}
    if any(value < 0 or value > 1 for value in result.values()):
        raise ValueError(f"Scene {scene_index + 1} crop values must be between 0 and 1")
    if result["width"] <= 0 or result["height"] <= 0 or result["x"] + result["width"] > 1 or result["y"] + result["height"] > 1:
        raise ValueError(f"Scene {scene_index + 1} crop rectangle is invalid")
    return result


def _timeline_payload(
    language: str,
    title: str,
    audio_src: str,
    duration_ms: int,
    cues: list[Any],
    scenes: list[dict[str, Any]],
    storyboard_status: str,
    missing_assets: list[str],
) -> dict[str, Any]:
    return {
        "schemaVersion": 2,
        "language": language,
        "title": _nfc(title),
        "audioSrc": audio_src,
        "durationSeconds": duration_ms / 1000,
        "captions": [cue.to_dict() for cue in cues],
        "scenes": scenes,
        "storyboardStatus": storyboard_status,
        "missingAssets": missing_assets,
        "assetWarnings": [],
        "safeArea": {"top": 88, "right": 150, "bottom": 260, "left": 64},
    }


def _duration_ms(transcript: dict[str, Any], words: list[dict[str, Any]]) -> int:
    audio_duration = transcript.get("audio", {}).get("duration_seconds")
    if isinstance(audio_duration, (int, float)) and audio_duration > 0:
        return max(round(float(audio_duration) * 1000), round(float(words[-1]["end"]) * 1000))
    return max(round(float(words[-1]["end"]) * 1000) + 350, 1000)


def _canonical(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)
