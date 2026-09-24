from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .assets import load_asset_manifest, prepare_asset_entry
from .config import load_env_file, voice_id_for
from .elevenlabs import ElevenLabsClient
from .media import audio_duration
from .models import ArtifactKind, ArtifactStatus, Mode
from .render import prepare_renderer_job, run_render, run_studio
from .script_bundle import validate_script_bundle
from .storage import Workspace, sha256_file, slugify
from .subtitles import render_srt, render_vtt
from .timeline import build_draft_timeline, compile_storyboard, validate_storyboard_shape
from .transcript import load_json, normalize_transcript, validate_transcript


def project_root() -> Path:
    return Path.cwd()


def read_artifact_json(workspace: Workspace, artifact: dict[str, Any]) -> dict[str, Any]:
    return json.loads(workspace.resolve_path(artifact).read_text(encoding="utf-8"))


def require_artifact(
    workspace: Workspace, job_id: str, language: str | None, kind: ArtifactKind
) -> dict[str, Any]:
    artifact = workspace.latest_artifact(job_id, kind, language)
    if artifact is None:
        suffix = f"/{language}" if language else ""
        raise RuntimeError(f"Missing {kind.value} artifact for {job_id}{suffix}")
    return artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vidkit")
    parser.add_argument("--root", type=Path, default=project_root())
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")
    sub.add_parser("migrate")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")

    create = sub.add_parser("create")
    create.add_argument("topic")
    create.add_argument("--languages", default="vi,en")
    create.add_argument("--mode", choices=[mode.value for mode in Mode], default=Mode.REVIEW.value)
    create.add_argument("--source-url")

    listing = sub.add_parser("list")
    listing.add_argument("--status")
    listing.add_argument("--json", action="store_true")

    for name in ("show", "status", "open"):
        command = sub.add_parser(name)
        command.add_argument("job_id")

    rename = sub.add_parser("rename")
    rename.add_argument("job_id")
    rename.add_argument("title")

    next_command = sub.add_parser("next")
    next_command.add_argument("job_id")
    next_command.add_argument("--language")
    next_command.add_argument("--json", action="store_true")

    add_source = sub.add_parser("add-source")
    add_source.add_argument("job_id")
    add_source.add_argument("file", type=Path)

    add_script = sub.add_parser("add-script")
    add_script.add_argument("job_id")
    add_script.add_argument("language")
    add_script.add_argument("file", type=Path)

    add_asset = sub.add_parser("add-asset")
    add_asset.add_argument("job_id")
    add_asset.add_argument("file", type=Path)
    add_asset.add_argument("--description", required=True)
    add_asset.add_argument("--usage-basis", required=True)
    add_asset.add_argument("--source-url")

    add_storyboard = sub.add_parser("add-storyboard")
    add_storyboard.add_argument("job_id")
    add_storyboard.add_argument("language")
    add_storyboard.add_argument("file", type=Path)

    tts = sub.add_parser("tts")
    tts.add_argument("job_id")
    tts.add_argument("language")
    tts.add_argument("--voice-id")
    tts.add_argument("--confirm-paid", action="store_true")

    transcribe = sub.add_parser("transcribe")
    transcribe.add_argument("job_id")
    transcribe.add_argument("language")
    transcribe.add_argument("--confirm-paid", action="store_true")

    import_transcript = sub.add_parser("import-transcript")
    import_transcript.add_argument("job_id")
    import_transcript.add_argument("language")
    import_transcript.add_argument("file", type=Path)
    import_transcript.add_argument("--audio", type=Path)

    timeline = sub.add_parser("timeline")
    timeline.add_argument("job_id")
    timeline.add_argument("language")
    timeline.add_argument("--draft", action="store_true")

    for name in ("studio", "render"):
        command = sub.add_parser(name)
        command.add_argument("job_id")
        command.add_argument("language")

    import_render = sub.add_parser("import-render")
    import_render.add_argument("job_id")
    import_render.add_argument("language")
    import_render.add_argument("file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    load_env_file(root / ".env")
    workspace = Workspace(root)
    workspace.initialize()
    try:
        if args.command == "init":
            print(f"Initialized {workspace.workspace_root}")
        elif args.command == "migrate":
            print(json.dumps(workspace.migrate_legacy(), ensure_ascii=False, indent=2))
        elif args.command == "doctor":
            _doctor(workspace, args.json)
        elif args.command == "create":
            print(
                workspace.create_job(
                    args.topic, args.languages.split(","), Mode(args.mode), args.source_url
                )
            )
        elif args.command == "list":
            _list_jobs(workspace, args.status, args.json)
        elif args.command in {"show", "status"}:
            _show(workspace, args.job_id)
        elif args.command == "open":
            _open_job(workspace, args.job_id)
        elif args.command == "rename":
            print(json.dumps(workspace.rename_job(args.job_id, args.title), ensure_ascii=False, indent=2))
        elif args.command == "next":
            _next(workspace, args.job_id, args.language, args.json)
        elif args.command == "add-source":
            _add_source(workspace, args.job_id, args.file)
        elif args.command == "add-script":
            _add_script(workspace, args.job_id, args.language, args.file)
        elif args.command == "add-asset":
            _add_asset(
                workspace,
                args.job_id,
                args.file,
                args.description,
                args.usage_basis,
                args.source_url,
            )
        elif args.command == "add-storyboard":
            _add_storyboard(workspace, args.job_id, args.language, args.file)
        elif args.command == "tts":
            _require_paid_authorization(args.confirm_paid)
            _tts(workspace, args.job_id, args.language, args.voice_id)
        elif args.command == "transcribe":
            _require_paid_authorization(args.confirm_paid)
            _transcribe(workspace, args.job_id, args.language)
        elif args.command == "import-transcript":
            _import_transcript(workspace, args.job_id, args.language, args.file, args.audio)
        elif args.command == "timeline":
            _timeline(workspace, args.job_id, args.language, args.draft)
        elif args.command in {"studio", "render"}:
            return _remotion(workspace, args.job_id, args.language, args.command)
        elif args.command == "import-render":
            _import_render(workspace, args.job_id, args.language, args.file)
        return 0
    except (KeyError, ValueError, RuntimeError, FileNotFoundError, OSError) as exc:
        print(f"vidkit: {exc}", file=sys.stderr)
        return 2


def _doctor(workspace: Workspace, as_json: bool) -> None:
    local_remotion = (
        workspace.project_root
        / "renderer"
        / "node_modules"
        / "@remotion"
        / "cli"
        / "remotion-cli.js"
    )
    checks = {
        "workspace": workspace.workspace_root.is_dir(),
        "python": sys.version.split()[0],
        "node": shutil.which("node") is not None,
        "npm": shutil.which("npm.cmd") is not None or shutil.which("npm") is not None,
        "npx": shutil.which("npx.cmd") is not None or shutil.which("npx") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "rendererDependencies": (workspace.project_root / "renderer" / "node_modules").is_dir(),
        "remotionCli": local_remotion.is_file(),
        "elevenLabsApiKey": bool(os.environ.get("ELEVENLABS_API_KEY")),
        "voiceVi": bool(voice_id_for("vi")),
        "voiceEn": bool(voice_id_for("en")),
        "paidBudgetConfigured": _configured_paid_budget() is not None,
    }
    if as_json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
        return
    for key, value in checks.items():
        print(f"{key:22} {value}")


def _list_jobs(workspace: Workspace, status: str | None, as_json: bool) -> None:
    jobs = [job for job in workspace.list_jobs() if status is None or job["status"] == status]
    for job in jobs:
        states = {language: _next_state(workspace, job, language) for language in job["languages"]}
        selected_language = next(
            (language for language, state in states.items() if state["step"] != "review"),
            job["languages"][0],
        )
        job["nextByLanguage"] = states
        job["next"] = states[selected_language]
    if as_json:
        print(json.dumps(jobs, ensure_ascii=False, indent=2))
        return
    print(f"{'ID':12}  {'STATUS':14}  {'LANG':8}  {'NEXT':18}  TITLE / ISSUES")
    for job in jobs:
        next_state = job["next"]
        issues = "; ".join(next_state["issues"])
        suffix = f" / {issues}" if issues else ""
        next_label = f"{next_state['language']}:{next_state['step']}"
        print(
            f"{job['id']:12}  {job['status'][:14]:14}  {','.join(job['languages']):8}  "
            f"{next_label[:18]:18}  {job['topic']}{suffix}"
        )


def _show(workspace: Workspace, job_id: str) -> None:
    payload = {"job": workspace.get_job(job_id), "artifacts": workspace.list_artifacts(job_id)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _open_job(workspace: Workspace, job_id: str) -> None:
    path = workspace.job_root(job_id)
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
    print(path)


def _next(workspace: Workspace, job_id: str, language: str | None, as_json: bool) -> None:
    job = workspace.get_job(job_id)
    selected = language or job["languages"][0]
    result = _next_state(workspace, job, selected)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['step']}: {result['command']}")
        if result["issues"]:
            print("Issues: " + "; ".join(result["issues"]))


def _next_state(workspace: Workspace, job: dict[str, Any], language: str) -> dict[str, Any]:
    job_id = job["id"]
    issues: list[str] = []
    source = workspace.latest_artifact(job_id, ArtifactKind.SOURCE, None)
    if not source:
        return {"jobId": job_id, "language": language, "step": "research", "command": f"vidkit add-source {job_id} <source-pack.json>", "issues": issues}
    if source["status"] != ArtifactStatus.CHECKED.value:
        return {"jobId": job_id, "language": language, "step": "research-review", "command": f"vidkit show {job_id}", "issues": [f"source status is {source['status']}"]}
    if not workspace.latest_artifact(job_id, ArtifactKind.SCRIPT, language):
        return {"jobId": job_id, "language": language, "step": "script", "command": f"vidkit add-script {job_id} {language} <script.json>", "issues": issues}
    if not workspace.latest_artifact(job_id, ArtifactKind.AUDIO, language):
        return {"jobId": job_id, "language": language, "step": "voice", "command": f"vidkit tts {job_id} {language}", "issues": _paid_step_issues()}
    transcript = _normalized_transcript_artifact(workspace, job_id, language)
    if not transcript:
        return {"jobId": job_id, "language": language, "step": "transcript", "command": f"vidkit transcribe {job_id} {language}", "issues": _paid_step_issues()}
    if transcript["status"] != ArtifactStatus.CHECKED.value:
        issues.append(f"transcript status is {transcript['status']}")
    if not workspace.latest_artifact(job_id, ArtifactKind.STORYBOARD, language):
        return {"jobId": job_id, "language": language, "step": "storyboard", "command": f"vidkit add-storyboard {job_id} {language} <storyboard.json>", "issues": issues}
    timeline = workspace.latest_artifact(job_id, ArtifactKind.TIMELINE, language)
    if not timeline:
        return {"jobId": job_id, "language": language, "step": "timeline", "command": f"vidkit timeline {job_id} {language}", "issues": issues}
    timeline_payload = read_artifact_json(workspace, timeline)
    if timeline_payload.get("missingAssets"):
        issues.append("missing assets: " + ", ".join(timeline_payload["missingAssets"]))
        return {"jobId": job_id, "language": language, "step": "assets", "command": f"vidkit add-asset {job_id} <image> --description <text> --usage-basis <basis>", "issues": issues}
    if timeline_payload.get("assetWarnings"):
        issues.extend(timeline_payload["assetWarnings"])
        return {"jobId": job_id, "language": language, "step": "assets-review", "command": f"vidkit show {job_id}", "issues": issues}
    if not workspace.latest_artifact(job_id, ArtifactKind.RENDER, language):
        return {"jobId": job_id, "language": language, "step": "preview", "command": f"vidkit studio {job_id} {language}", "issues": issues}
    return {"jobId": job_id, "language": language, "step": "review", "command": f"vidkit show {job_id}", "issues": issues}


def _configured_paid_budget() -> float | None:
    raw = os.environ.get("VIDKIT_PAID_BUDGET_USD", "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _paid_step_issues() -> list[str]:
    if _configured_paid_budget() is not None:
        return []
    return ["paid-step blocked: configure VIDKIT_PAID_BUDGET_USD or pass --confirm-paid"]


def _require_paid_authorization(confirmed: bool) -> None:
    if confirmed or _configured_paid_budget() is not None:
        return
    raise RuntimeError(
        "Paid step blocked: set a positive VIDKIT_PAID_BUDGET_USD in .env "
        "or rerun with --confirm-paid"
    )


def _add_source(workspace: Workspace, job_id: str, file: Path) -> None:
    payload = load_json(file)
    errors = _validate_source_pack(payload)
    if errors:
        raise ValueError("; ".join(errors))
    for language in workspace.get_job(job_id)["languages"]:
        workspace.invalidate_downstream(job_id, language, ArtifactKind.SOURCE)
    artifact = workspace.add_json_artifact(job_id, None, ArtifactKind.SOURCE, payload, ArtifactStatus.CHECKED)
    print(artifact["path"])


def _validate_source_pack(payload: dict[str, Any]) -> list[str]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return ["Source pack must contain a non-empty claims list"]
    errors: list[str] = []
    required = ("id", "statement", "sourceUrl", "retrievedAt", "publishedAt", "uncertainty")
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claim {index + 1} must be an object")
            continue
        missing = [
            key
            for key in required
            if key not in claim
            or (
                key not in {"publishedAt", "uncertainty"}
                and (claim[key] is None or claim[key] == "")
            )
            or (key in {"publishedAt", "uncertainty"} and claim[key] == "")
        ]
        if missing:
            errors.append(f"claim {index + 1} is missing: {', '.join(missing)}")
        claim_id = str(claim.get("id", ""))
        if claim_id in seen:
            errors.append(f"duplicate claim id: {claim_id}")
        seen.add(claim_id)
    return errors


def _add_script(workspace: Workspace, job_id: str, language: str, file: Path) -> None:
    payload = load_json(file)
    errors = validate_script_bundle(payload)
    if errors:
        raise ValueError("; ".join(errors))
    workspace.invalidate_downstream(job_id, language, ArtifactKind.SCRIPT)
    artifact = workspace.add_json_artifact(job_id, language, ArtifactKind.SCRIPT, payload, ArtifactStatus.CHECKED)
    print(artifact["path"])


def _add_asset(
    workspace: Workspace,
    job_id: str,
    file: Path,
    description: str,
    usage_basis: str,
    source_url: str | None,
) -> None:
    if not usage_basis.strip():
        raise ValueError("usage basis cannot be empty")
    manifest, previous = load_asset_manifest(workspace, job_id)
    entry, target = prepare_asset_entry(
        workspace, job_id, file, description, usage_basis, source_url
    )
    existing = next((item for item in manifest["assets"] if item["sha256"] == entry["sha256"]), None)
    if existing:
        print(existing["id"])
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file.resolve(), target)
    manifest["assets"].append(entry)
    artifact = workspace.add_json_artifact(
        job_id,
        None,
        ArtifactKind.ASSET_MANIFEST,
        manifest,
        ArtifactStatus.CHECKED,
        upstream={"asset-manifest": previous["revision"]} if previous else {},
    )
    workspace.invalidate_visuals(job_id)
    print(
        json.dumps(
            {
                "assetId": entry["id"],
                "manifest": artifact["path"],
                "qualityWarnings": entry["qualityWarnings"],
            },
            ensure_ascii=False,
        )
    )


def _add_storyboard(workspace: Workspace, job_id: str, language: str, file: Path) -> None:
    payload = load_json(file)
    if payload.get("language") and payload["language"] != language:
        raise ValueError(f"Storyboard language {payload['language']} does not match {language}")
    errors = validate_storyboard_shape(payload)
    if errors:
        raise ValueError("; ".join(errors))
    workspace.invalidate_downstream(job_id, language, ArtifactKind.STORYBOARD)
    artifact = workspace.add_json_artifact(job_id, language, ArtifactKind.STORYBOARD, payload, ArtifactStatus.CHECKED)
    print(artifact["path"])


def _tts(workspace: Workspace, job_id: str, language: str, voice_id: str | None) -> None:
    voice_id = voice_id or voice_id_for(language)
    if not voice_id:
        variable = f"VIDKIT_VOICE_{language.upper().replace('-', '_')}"
        raise RuntimeError(f"Missing voice ID: set {variable} in .env or pass --voice-id")
    script_artifact = require_artifact(workspace, job_id, language, ArtifactKind.SCRIPT)
    script = read_artifact_json(workspace, script_artifact)
    output = workspace.pending_path(job_id, language, "narration.pending.mp3")
    ElevenLabsClient().text_to_speech(script["tts_input"], voice_id, output)
    workspace.invalidate_downstream(job_id, language, ArtifactKind.AUDIO)
    artifact = workspace.add_file_artifact(
        job_id,
        language,
        ArtifactKind.AUDIO,
        output,
        ArtifactStatus.GENERATED,
        upstream={"script": script_artifact["revision"]},
        metadata={"provider": "elevenlabs", "model": "eleven_v3", "voice_id": voice_id},
    )
    output.unlink(missing_ok=True)
    print(artifact["path"])


def _transcribe(workspace: Workspace, job_id: str, language: str) -> None:
    audio_artifact = require_artifact(workspace, job_id, language, ArtifactKind.AUDIO)
    payload = ElevenLabsClient().speech_to_text(workspace.resolve_path(audio_artifact), language_code=language)
    raw_path = workspace.pending_path(job_id, language, "transcript.raw.pending.json")
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    workspace.invalidate_downstream(job_id, language, ArtifactKind.TRANSCRIPT)
    _store_transcript(workspace, job_id, language, raw_path, audio_artifact)
    raw_path.unlink(missing_ok=True)


def _import_transcript(
    workspace: Workspace,
    job_id: str,
    language: str,
    transcript_file: Path,
    audio_file: Path | None,
) -> None:
    audio_artifact = workspace.latest_artifact(job_id, ArtifactKind.AUDIO, language)
    if audio_file:
        if not audio_file.is_file():
            raise FileNotFoundError(audio_file)
        workspace.invalidate_downstream(job_id, language, ArtifactKind.AUDIO)
        audio_artifact = workspace.add_file_artifact(
            job_id, language, ArtifactKind.AUDIO, audio_file, ArtifactStatus.GENERATED, metadata={"provider": "import"}
        )
    workspace.invalidate_downstream(job_id, language, ArtifactKind.TRANSCRIPT)
    _store_transcript(workspace, job_id, language, transcript_file, audio_artifact)


def _store_transcript(
    workspace: Workspace,
    job_id: str,
    language: str,
    transcript_file: Path,
    audio_artifact: dict[str, Any] | None,
) -> None:
    raw_payload = load_json(transcript_file)
    normalized = normalize_transcript(raw_payload)
    script_artifact = workspace.latest_artifact(job_id, ArtifactKind.SCRIPT, language)
    expected = read_artifact_json(workspace, script_artifact).get("expected_spoken_text") if script_artifact else None
    duration = audio_duration(workspace.resolve_path(audio_artifact)) if audio_artifact else None
    findings = validate_transcript(normalized, expected, duration)
    normalized["audio"] = {
        "revision": audio_artifact["revision"] if audio_artifact else None,
        "sha256": audio_artifact["sha256"] if audio_artifact else None,
        "duration_seconds": duration,
        "synchronization_verified": duration is not None,
    }
    normalized["findings"] = [finding.to_dict() for finding in findings]
    has_error = any(finding.severity == "error" for finding in findings)
    status = ArtifactStatus.NEEDS_REVIEW if has_error or not audio_artifact or duration is None else ArtifactStatus.CHECKED
    raw_artifact = workspace.add_file_artifact(
        job_id,
        language,
        ArtifactKind.TRANSCRIPT,
        transcript_file,
        ArtifactStatus.GENERATED,
        upstream={"audio": audio_artifact["revision"]} if audio_artifact else {},
        metadata={"variant": "raw"},
    )
    artifact = workspace.add_json_artifact(
        job_id,
        language,
        ArtifactKind.TRANSCRIPT,
        normalized,
        status,
        upstream={"audio": audio_artifact["revision"]} if audio_artifact else {},
        metadata={"variant": "normalized", "raw_revision": raw_artifact["revision"]},
    )
    print(artifact["path"])


def _normalized_transcript_artifact(
    workspace: Workspace, job_id: str, language: str
) -> dict[str, Any] | None:
    artifacts = [
        artifact
        for artifact in workspace.list_artifacts(job_id)
        if artifact["language"] == language
        and artifact["kind"] == ArtifactKind.TRANSCRIPT.value
        and artifact["metadata"].get("variant") == "normalized"
        and artifact["status"] != ArtifactStatus.INVALIDATED.value
    ]
    return artifacts[-1] if artifacts else None


def _timeline(workspace: Workspace, job_id: str, language: str, draft: bool) -> None:
    transcript_artifact = _normalized_transcript_artifact(workspace, job_id, language)
    if not transcript_artifact:
        raise RuntimeError("Missing normalized transcript")
    transcript = read_artifact_json(workspace, transcript_artifact)
    script_artifact = require_artifact(workspace, job_id, language, ArtifactKind.SCRIPT)
    script = read_artifact_json(workspace, script_artifact)
    audio_artifact = require_artifact(workspace, job_id, language, ArtifactKind.AUDIO)
    storyboard_artifact = None
    manifest_artifact = workspace.latest_artifact(job_id, ArtifactKind.ASSET_MANIFEST, None)
    if draft:
        timeline = build_draft_timeline(
            transcript, script.get("title") or workspace.get_job(job_id)["topic"], language, audio_artifact["path"]
        )
        missing_assets: list[str] = []
    else:
        storyboard_artifact = require_artifact(workspace, job_id, language, ArtifactKind.STORYBOARD)
        storyboard = read_artifact_json(workspace, storyboard_artifact)
        manifest, _ = load_asset_manifest(workspace, job_id)
        timeline, missing_assets = compile_storyboard(
            transcript,
            storyboard,
            manifest,
            script.get("title") or workspace.get_job(job_id)["topic"],
            language,
            audio_artifact["path"],
        )
    job = workspace.get_job(job_id)
    validation_issues: list[str] = []
    if transcript_artifact["status"] != ArtifactStatus.CHECKED.value:
        validation_issues.append(f"transcript status is {transcript_artifact['status']}")
    validation_issues.extend(timeline.get("assetWarnings", []))
    source_artifact = workspace.latest_artifact(job_id, ArtifactKind.SOURCE, None)
    if job["mode"] == Mode.AUTOMATIC.value and (
        not source_artifact or source_artifact["status"] != ArtifactStatus.CHECKED.value
    ):
        validation_issues.append("checked source pack is required in automatic mode")
    timeline["validationIssues"] = validation_issues
    workspace.invalidate_downstream(job_id, language, ArtifactKind.TIMELINE)
    upstream = {
        "script": script_artifact["revision"],
        "audio": audio_artifact["revision"],
        "transcript": transcript_artifact["revision"],
    }
    if storyboard_artifact:
        upstream["storyboard"] = storyboard_artifact["revision"]
    if manifest_artifact:
        upstream["asset-manifest"] = manifest_artifact["revision"]
    if missing_assets:
        timeline_status = ArtifactStatus.BLOCKED
    elif job["mode"] == Mode.AUTOMATIC.value:
        timeline_status = ArtifactStatus.BLOCKED if validation_issues else ArtifactStatus.CHECKED
    else:
        timeline_status = ArtifactStatus.NEEDS_REVIEW
    artifact = workspace.add_json_artifact(
        job_id,
        language,
        ArtifactKind.TIMELINE,
        timeline,
        timeline_status,
        upstream=upstream,
    )
    for kind, suffix, content in (
        (ArtifactKind.SUBTITLE_SRT, ".srt", render_srt(timeline["captions"])),
        (ArtifactKind.SUBTITLE_VTT, ".vtt", render_vtt(timeline["captions"])),
    ):
        pending = workspace.pending_path(job_id, language, f"subtitle.pending{suffix}")
        pending.write_text(content, encoding="utf-8")
        subtitle_status = (
            ArtifactStatus.BLOCKED
            if timeline_status == ArtifactStatus.BLOCKED
            else ArtifactStatus.CHECKED
            if job["mode"] == Mode.AUTOMATIC.value
            else ArtifactStatus.NEEDS_REVIEW
        )
        workspace.add_file_artifact(
            job_id,
            language,
            kind,
            pending,
            subtitle_status,
            upstream={"timeline": artifact["revision"], "transcript": transcript_artifact["revision"]},
        )
        pending.unlink(missing_ok=True)
    print(artifact["path"])


def _remotion(workspace: Workspace, job_id: str, language: str, action: str) -> int:
    timeline_artifact = require_artifact(workspace, job_id, language, ArtifactKind.TIMELINE)
    timeline = read_artifact_json(workspace, timeline_artifact)
    audio_artifact = require_artifact(workspace, job_id, language, ArtifactKind.AUDIO)
    props = prepare_renderer_job(
        workspace, job_id, language, timeline, workspace.resolve_path(audio_artifact)
    )
    job = workspace.get_job(job_id)
    if action == "studio":
        output = workspace.job_root(job_id) / "exports" / f"{slugify(job['topic'])}.{language}.studio.mp4"
        return run_studio(workspace.project_root, props, output)
    if timeline.get("missingAssets"):
        raise RuntimeError("Cannot export: required assets are missing")
    if timeline_artifact["status"] == ArtifactStatus.BLOCKED.value:
        raise RuntimeError("Cannot export: timeline has blocking validation issues")
    if job["mode"] == Mode.AUTOMATIC.value and timeline_artifact["status"] not in {
        ArtifactStatus.CHECKED.value,
        ArtifactStatus.APPROVED.value,
    }:
        raise RuntimeError("Automatic export is blocked until timeline checks pass")
    output = workspace.pending_path(job_id, language, "final.pending.mp4")
    code = run_render(workspace.project_root, props, output)
    if code == 0:
        artifact = workspace.add_file_artifact(
            job_id,
            language,
            ArtifactKind.RENDER,
            output,
            ArtifactStatus.NEEDS_REVIEW,
            upstream={"timeline": timeline_artifact["revision"]},
            metadata={"renderer": "remotion", "format": "1080x1920@30"},
        )
        output.unlink(missing_ok=True)
        print(artifact["path"])
    return code


def _import_render(workspace: Workspace, job_id: str, language: str, file: Path) -> None:
    timeline = require_artifact(workspace, job_id, language, ArtifactKind.TIMELINE)
    artifact = workspace.add_file_artifact(
        job_id,
        language,
        ArtifactKind.RENDER,
        file,
        ArtifactStatus.NEEDS_REVIEW,
        upstream={"timeline": timeline["revision"]},
        metadata={"renderer": "remotion-studio", "imported": True, "source_sha256": sha256_file(file)},
    )
    print(artifact["path"])


if __name__ == "__main__":
    raise SystemExit(main())
