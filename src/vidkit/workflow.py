from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import ArtifactKind as K, ArtifactStatus as S
from .storage import Workspace, sha256_file
from .brief_frames import render_brief_frames


def payload(workspace: Workspace, artifact: dict[str, Any]) -> dict[str, Any]:
    return json.loads(workspace.resolve_path(artifact).read_text(encoding="utf-8"))


def current_approval(workspace: Workspace, job_id: str, language: str, stage: str) -> bool:
    target_kinds = (K.SCRIPT, K.BRIEF) if stage == "concept" else (K.TIMELINE, K.PREVIEW, K.QA_REPORT)
    current = {kind.value: workspace.latest_artifact(job_id, kind, language) for kind in target_kinds}
    if any(value is None for value in current.values()):
        return False
    for artifact in reversed(workspace.list_artifacts(job_id)):
        if artifact["kind"] != K.APPROVAL.value or artifact["language"] != language or artifact["status"] == S.INVALIDATED.value:
            continue
        record = payload(workspace, artifact)
        if record.get("stage") == stage:
            return record.get("targets") == {kind: {"revision": item["revision"], "sha256": item["sha256"]}
                                               for kind, item in current.items()}
    return False


def add_brief(workspace: Workspace, job_id: str, language: str, source: Path) -> dict[str, Any]:
    data = json.loads(source.read_text(encoding="utf-8"))
    script = workspace.latest_artifact(job_id, K.SCRIPT, language)
    if not script:
        raise ValueError("Add a script before the creative brief")
    required = {"angle", "theme", "hook", "visualStrategy", "frames"}
    if required - data.keys():
        raise ValueError(f"Brief missing: {', '.join(sorted(required - data.keys()))}")
    from .library import entries
    if not any(item["kind"] == "theme" and item["id"] == data["theme"] for item in entries(workspace)):
        raise ValueError(f"Unknown theme: {data['theme']}")
    frames = data["frames"]
    if not isinstance(frames, dict) or not {"hook", "evidence", "takeaway"} <= frames.keys():
        raise ValueError("Brief needs hook, evidence, and takeaway frame descriptions")
    for name in ("hook", "evidence", "takeaway"):
        frame = frames[name]
        if not isinstance(frame, dict) or not isinstance(frame.get("headline"), str) or not frame["headline"].strip():
            raise ValueError(f"Brief {name} frame needs a headline")
        if not frame.get("imagePath") and not str(frame.get("visualNote", "")).strip():
            raise ValueError(f"Brief {name} frame needs imagePath or visualNote")
    if data.get("screenshotUnavailable"):
        alternative = data.get("screenshotAlternative")
        if not isinstance(alternative, dict) or alternative.get("type") not in {
            "official-artwork", "api-example", "chart", "diagram", "recreated-illustration"
        } or not alternative.get("sourceUrl"):
            raise ValueError("Document alternative type and sourceUrl when a screenshot is unavailable")
    previous = workspace.latest_artifact(job_id, K.BRIEF, language, include_invalidated=True)
    revision = previous["revision"] + 1 if previous else 1
    data["framePreviews"] = render_brief_frames(workspace, job_id, language, frames, data["theme"], revision)
    workspace.invalidate_downstream(job_id, language, K.BRIEF)
    return workspace.add_json_artifact(job_id, language, K.BRIEF, data, S.CHECKED,
                                       upstream={"script": script["revision"]})


def add_caption_plan(workspace: Workspace, job_id: str, language: str, source: Path) -> dict[str, Any]:
    from .captions import build_caption_cues
    data = json.loads(source.read_text(encoding="utf-8"))
    transcript = workspace.latest_artifact(job_id, K.TRANSCRIPT, language)
    if not transcript or transcript["metadata"].get("variant") != "normalized":
        raise ValueError("Normalized transcript required before caption plan")
    build_caption_cues(payload(workspace, transcript)["words"], plan=data)
    workspace.invalidate_downstream(job_id, language, K.CAPTION_PLAN)
    return workspace.add_json_artifact(job_id, language, K.CAPTION_PLAN, data, S.CHECKED,
                                       upstream={"transcript": transcript["revision"]})


def approve(workspace: Workspace, job_id: str, language: str, stage: str, reviewer: str) -> dict[str, Any]:
    if stage not in {"concept", "export"} or not reviewer.strip():
        raise ValueError("Approval requires concept/export stage and reviewer")
    kinds = (K.SCRIPT, K.BRIEF) if stage == "concept" else (K.TIMELINE, K.PREVIEW, K.QA_REPORT)
    targets = {}
    for kind in kinds:
        item = workspace.latest_artifact(job_id, kind, language)
        if not item:
            raise ValueError(f"Missing {kind.value} for {stage} approval")
        targets[kind.value] = {"revision": item["revision"], "sha256": item["sha256"]}
    if stage == "export":
        report = payload(workspace, workspace.latest_artifact(job_id, K.QA_REPORT, language))
        if any(check["status"] == "fail" for check in report["checks"].values()):
            raise ValueError("QA failed; cannot approve export")
    record = {"stage": stage, "reviewer": reviewer.strip(), "approvedAt": datetime.now(UTC).isoformat(),
              "targets": targets}
    return workspace.add_json_artifact(job_id, language, K.APPROVAL, record, S.APPROVED,
                                       metadata={"stage": stage})


QA_SECTIONS = ("automatic", "mediaProbe", "frameInspection", "transitionReview", "fullPlayback", "audioListening")


def make_qa(workspace: Workspace, job_id: str, language: str, supplied: dict[str, Any] | None = None) -> dict[str, Any]:
    timeline = workspace.latest_artifact(job_id, K.TIMELINE, language)
    preview = workspace.latest_artifact(job_id, K.PREVIEW, language)
    if not timeline or not preview:
        raise ValueError("Timeline and preview MP4 required before QA")
    data = payload(workspace, timeline)
    issues = list(data.get("validationIssues", []))
    issues.extend(f"Missing asset: {item}" for item in data.get("missingAssets", []))
    if not workspace.resolve_path(preview).is_file():
        issues.append("Preview file missing")
    checks = {"automatic": {"status": "fail" if issues else "pass", "evidence": issues or
                            [f"Preview {preview['path']} exists", "Timeline validation passed"]}}
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            probe = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-of", "json",
                                    str(workspace.resolve_path(preview))], capture_output=True, text=True,
                                   timeout=20, check=True)
            streams = json.loads(probe.stdout)["streams"]
            video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
            audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
            passed = video is not None and video.get("width") == 1080 and video.get("height") == 1920 and audio is not None
            checks["mediaProbe"] = {"status": "pass" if passed else "fail",
                                    "evidence": [f"video={video.get('codec_name') if video else 'missing'} "
                                                 f"{video.get('width') if video else 0}x{video.get('height') if video else 0}; "
                                                 f"audio={audio.get('codec_name') if audio else 'missing'}"]}
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, KeyError):
            checks["mediaProbe"] = {"status": "fail", "evidence": ["ffprobe could not inspect preview MP4"]}
    else:
        checks["mediaProbe"] = {"status": "not-run", "evidence": ["ffprobe unavailable"]}
    for name in QA_SECTIONS[2:]:
        check = (supplied or {}).get("checks", {}).get(name, {"status": "not-run", "evidence": []})
        if check.get("status") not in {"pass", "fail", "not-run"} or not isinstance(check.get("evidence"), list):
            raise ValueError(f"Invalid QA check: {name}")
        if check["status"] == "pass" and not check["evidence"]:
            raise ValueError(f"QA pass requires evidence: {name}")
        checks[name] = check
    brief = workspace.latest_artifact(job_id, K.BRIEF, language)
    limitations = []
    if brief and payload(workspace, brief).get("screenshotUnavailable"):
        limitations.append("Product screenshot unavailable; sourced alternative used")
    layouts = [scene.get("layout") for scene in data.get("scenes", [])]
    if any(layouts[index] == layouts[index + 1] == layouts[index + 2] for index in range(len(layouts) - 2)):
        limitations.append("Three consecutive scenes repeat the same layout")
    if any(scene.get("layout") in {"screenshot", "screenshot-focus"} and
           scene.get("crop", {}).get("width", 1) > .8 and
           scene.get("asset", {}).get("width", 0) > scene.get("asset", {}).get("height", 0) * 1.4
           for scene in data.get("scenes", []) if scene.get("asset")):
        limitations.append("Wide visual may be too small on a portrait screen; inspect a phone-sized frame")
    report = {"schemaVersion": 3, "checks": checks, "limitations": limitations,
              "preview": {"revision": preview["revision"], "sha256": preview["sha256"]},
              "timeline": {"revision": timeline["revision"], "sha256": timeline["sha256"]}}
    return workspace.add_json_artifact(job_id, language, K.QA_REPORT, report,
                                       S.BLOCKED if issues else S.NEEDS_REVIEW,
                                       upstream={"preview": preview["revision"], "timeline": timeline["revision"]})


def next_state(workspace: Workspace, job: dict[str, Any], language: str) -> dict[str, Any]:
    job_id = job["id"]
    steps = [
        (K.SOURCE, None, "research", f"vidkit add-source {job_id} <source-pack.json>"),
        (K.SCRIPT, language, "script", f"vidkit add-script {job_id} {language} <script.json>"),
        (K.BRIEF, language, "creative-brief", f"vidkit add-brief {job_id} {language} <brief.json>"),
    ]
    for kind, lang, step, command in steps:
        if not workspace.latest_artifact(job_id, kind, lang):
            return {"jobId": job_id, "language": language, "step": step, "command": command, "issues": []}
    source = workspace.latest_artifact(job_id, K.SOURCE, None)
    if source and source["status"] != S.CHECKED.value:
        return {"jobId": job_id, "language": language, "step": "source-review",
                "command": f"vidkit show {job_id}", "issues": [f"Source status: {source['status']}"]}
    if job["mode"] == "review" and not current_approval(workspace, job_id, language, "concept"):
        return {"jobId": job_id, "language": language, "step": "await-concept-approval",
                "command": f"vidkit approve {job_id} {language} concept --reviewer <name>", "issues": []}
    for kind, step, command in (
        (K.AUDIO, "voice", f"vidkit tts {job_id} {language}"),
        (K.STORYBOARD, "storyboard", f"vidkit add-storyboard {job_id} {language} <storyboard.json>"),
        (K.TIMELINE, "timeline", f"vidkit timeline {job_id} {language}"),
        (K.PREVIEW, "preview", f"vidkit preview {job_id} {language}"),
        (K.QA_REPORT, "qa", f"vidkit qa {job_id} {language}"),
    ):
        if kind == K.STORYBOARD:
            transcript = workspace.latest_artifact(job_id, K.TRANSCRIPT, language)
            if not transcript or transcript["metadata"].get("variant") != "normalized":
                return {"jobId": job_id, "language": language, "step": "transcript",
                        "command": f"vidkit transcribe {job_id} {language}", "issues": []}
            if transcript["status"] != S.CHECKED.value:
                return {"jobId": job_id, "language": language, "step": "transcript-review",
                        "command": f"vidkit show {job_id}",
                        "issues": [f"Normalized transcript status: {transcript['status']}"]}
        if not workspace.latest_artifact(job_id, kind, language):
            return {"jobId": job_id, "language": language, "step": step, "command": command, "issues": []}
        if kind == K.TIMELINE:
            timeline = workspace.latest_artifact(job_id, kind, language)
            timeline_data = payload(workspace, timeline)
            renderer_hash = sha256_file(workspace.project_root / "renderer" / "src" / "VidkitShort.tsx")
            package_hash = sha256_file(workspace.project_root / "renderer" / "package-lock.json")
            from .library import locks_match
            if (timeline_data.get("rendererCodeSha256") != renderer_hash or
                    timeline_data.get("rendererPackageLockSha256") != package_hash or
                    not locks_match(workspace, timeline_data)):
                return {"jobId": job_id, "language": language, "step": "timeline-stale",
                        "command": f"vidkit timeline {job_id} {language}",
                        "issues": ["Renderer or a locked library entry changed since timeline compilation"]}
            if timeline["status"] == S.BLOCKED.value:
                return {"jobId": job_id, "language": language, "step": "timeline-blocked",
                        "command": f"vidkit show {job_id}", "issues": timeline_data.get("validationIssues", []) +
                        timeline_data.get("missingAssets", [])}
        if kind == K.QA_REPORT:
            report = payload(workspace, workspace.latest_artifact(job_id, kind, language))
            failed = [name for name, item in report["checks"].items() if item["status"] == "fail"]
            if failed:
                return {"jobId": job_id, "language": language, "step": "qa-failed",
                        "command": f"vidkit qa {job_id} {language}", "issues": failed}
    if job["mode"] == "review" and not current_approval(workspace, job_id, language, "export"):
        return {"jobId": job_id, "language": language, "step": "await-export-approval",
                "command": f"vidkit approve {job_id} {language} export --reviewer <name>", "issues": []}
    if not workspace.latest_artifact(job_id, K.RENDER, language):
        return {"jobId": job_id, "language": language, "step": "export",
                "command": f"vidkit render {job_id} {language}", "issues": []}
    return {"jobId": job_id, "language": language, "step": "complete",
            "command": f"vidkit show {job_id}", "issues": []}
