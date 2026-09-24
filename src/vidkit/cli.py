from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import load_env_file, voice_id_for
from .elevenlabs import ElevenLabsClient
from .media import audio_duration
from .models import ArtifactKind, ArtifactStatus, Mode
from .render import prepare_renderer_job, run_render, run_studio
from .script_bundle import validate_script_bundle
from .storage import Workspace
from .subtitles import render_srt, render_vtt
from .timeline import build_timeline
from .transcript import load_json, normalize_transcript, validate_transcript


def project_root() -> Path:
    return Path.cwd()


def read_artifact_json(root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    return json.loads((root / artifact["path"]).read_text(encoding="utf-8"))


def require_artifact(workspace: Workspace, job_id: str, language: str, kind: ArtifactKind) -> dict[str, Any]:
    artifact = workspace.latest_artifact(job_id, kind, language)
    if artifact is None:
        raise RuntimeError(f"Missing {kind.value} artifact for {job_id}/{language}")
    return artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vidkit")
    parser.add_argument("--root", type=Path, default=project_root())
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")
    create = sub.add_parser("create")
    create.add_argument("topic")
    create.add_argument("--languages", default="vi,en")
    create.add_argument("--mode", choices=[mode.value for mode in Mode], default=Mode.REVIEW.value)
    create.add_argument("--source-url")

    status = sub.add_parser("status")
    status.add_argument("job_id")

    add_script = sub.add_parser("add-script")
    add_script.add_argument("job_id")
    add_script.add_argument("language")
    add_script.add_argument("file", type=Path)

    tts = sub.add_parser("tts")
    tts.add_argument("job_id")
    tts.add_argument("language")
    tts.add_argument("--voice-id")

    transcribe = sub.add_parser("transcribe")
    transcribe.add_argument("job_id")
    transcribe.add_argument("language")

    import_transcript = sub.add_parser("import-transcript")
    import_transcript.add_argument("job_id")
    import_transcript.add_argument("language")
    import_transcript.add_argument("file", type=Path)
    import_transcript.add_argument("--audio", type=Path)

    timeline = sub.add_parser("timeline")
    timeline.add_argument("job_id")
    timeline.add_argument("language")

    for name in ("studio", "render"):
        command = sub.add_parser(name)
        command.add_argument("job_id")
        command.add_argument("language")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    load_env_file(root / ".env")
    workspace = Workspace(root)
    try:
        if args.command == "init":
            workspace.initialize()
            print(f"Initialized {workspace.state_root}")
        elif args.command == "create":
            job_id = workspace.create_job(
                args.topic,
                args.languages.split(","),
                Mode(args.mode),
                args.source_url,
            )
            print(job_id)
        elif args.command == "status":
            payload = {"job": workspace.get_job(args.job_id), "artifacts": workspace.list_artifacts(args.job_id)}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif args.command == "add-script":
            _add_script(workspace, args.job_id, args.language, args.file)
        elif args.command == "tts":
            _tts(workspace, args.job_id, args.language, args.voice_id)
        elif args.command == "transcribe":
            _transcribe(workspace, args.job_id, args.language)
        elif args.command == "import-transcript":
            _import_transcript(workspace, args.job_id, args.language, args.file, args.audio)
        elif args.command == "timeline":
            _timeline(workspace, args.job_id, args.language)
        elif args.command in {"studio", "render"}:
            return _remotion(workspace, args.job_id, args.language, args.command)
        return 0
    except (KeyError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"vidkit: {exc}", file=sys.stderr)
        return 2


def _add_script(workspace: Workspace, job_id: str, language: str, file: Path) -> None:
    payload = load_json(file)
    errors = validate_script_bundle(payload)
    if errors:
        raise ValueError("; ".join(errors))
    workspace.invalidate_downstream(job_id, language, ArtifactKind.SCRIPT)
    artifact = workspace.add_json_artifact(
        job_id,
        language,
        ArtifactKind.SCRIPT,
        payload,
        ArtifactStatus.CHECKED,
    )
    print(artifact["path"])


def _tts(workspace: Workspace, job_id: str, language: str, voice_id: str | None) -> None:
    voice_id = voice_id or voice_id_for(language)
    if not voice_id:
        variable = f"VIDKIT_VOICE_{language.upper().replace('-', '_')}"
        raise RuntimeError(f"Missing voice ID: set {variable} in .env or pass --voice-id")
    script_artifact = require_artifact(workspace, job_id, language, ArtifactKind.SCRIPT)
    script = read_artifact_json(workspace.project_root, script_artifact)
    output = workspace.job_dir(job_id, language) / "narration.pending.mp3"
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
    audio_path = workspace.project_root / audio_artifact["path"]
    payload = ElevenLabsClient().speech_to_text(audio_path, language_code=language)
    raw_path = workspace.job_dir(job_id, language) / "transcript.raw.pending.json"
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
            job_id,
            language,
            ArtifactKind.AUDIO,
            audio_file,
            ArtifactStatus.GENERATED,
            metadata={"provider": "import"},
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
    expected = None
    if script_artifact:
        expected = read_artifact_json(workspace.project_root, script_artifact).get("expected_spoken_text")
    duration = None
    if audio_artifact:
        duration = audio_duration(workspace.project_root / audio_artifact["path"])
    findings = validate_transcript(normalized, expected, duration)
    normalized["audio"] = {
        "revision": audio_artifact["revision"] if audio_artifact else None,
        "sha256": audio_artifact["sha256"] if audio_artifact else None,
        "duration_seconds": duration,
        "synchronization_verified": duration is not None,
    }
    normalized["findings"] = [finding.to_dict() for finding in findings]
    has_error = any(finding.severity == "error" for finding in findings)
    status = (
        ArtifactStatus.NEEDS_REVIEW
        if has_error or not audio_artifact or duration is None
        else ArtifactStatus.CHECKED
    )
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


def _timeline(workspace: Workspace, job_id: str, language: str) -> None:
    transcript_artifact = require_artifact(workspace, job_id, language, ArtifactKind.TRANSCRIPT)
    if transcript_artifact["metadata"].get("variant") != "normalized":
        artifacts = [
            artifact for artifact in workspace.list_artifacts(job_id)
            if artifact["language"] == language
            and artifact["kind"] == ArtifactKind.TRANSCRIPT.value
            and artifact["metadata"].get("variant") == "normalized"
            and artifact["status"] != ArtifactStatus.INVALIDATED.value
        ]
        if not artifacts:
            raise RuntimeError("Missing normalized transcript")
        transcript_artifact = artifacts[-1]
    transcript = read_artifact_json(workspace.project_root, transcript_artifact)
    script_artifact = require_artifact(workspace, job_id, language, ArtifactKind.SCRIPT)
    script = read_artifact_json(workspace.project_root, script_artifact)
    audio_artifact = require_artifact(workspace, job_id, language, ArtifactKind.AUDIO)
    timeline = build_timeline(
        transcript,
        script.get("title") or workspace.get_job(job_id)["topic"],
        language,
        audio_artifact["path"],
    )
    workspace.invalidate_downstream(job_id, language, ArtifactKind.TIMELINE)
    artifact = workspace.add_json_artifact(
        job_id,
        language,
        ArtifactKind.TIMELINE,
        timeline,
        ArtifactStatus.NEEDS_REVIEW,
        upstream={
            "script": script_artifact["revision"],
            "audio": audio_artifact["revision"],
            "transcript": transcript_artifact["revision"],
        },
    )
    subtitle_status = ArtifactStatus.NEEDS_REVIEW
    for kind, suffix, content in (
        (ArtifactKind.SUBTITLE_SRT, ".srt", render_srt(timeline["captions"])),
        (ArtifactKind.SUBTITLE_VTT, ".vtt", render_vtt(timeline["captions"])),
    ):
        pending = workspace.job_dir(job_id, language) / f"subtitle.pending{suffix}"
        pending.write_text(content, encoding="utf-8")
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
    timeline = read_artifact_json(workspace.project_root, timeline_artifact)
    audio_artifact = require_artifact(workspace, job_id, language, ArtifactKind.AUDIO)
    props = prepare_renderer_job(
        workspace.project_root,
        job_id,
        language,
        timeline,
        workspace.project_root / audio_artifact["path"],
    )
    if action == "studio":
        return run_studio(workspace.project_root, props)
    output = workspace.job_dir(job_id, language) / "final.mp4"
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


if __name__ == "__main__":
    raise SystemExit(main())
