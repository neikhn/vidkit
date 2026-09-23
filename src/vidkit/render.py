from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class RenderDependencyError(RuntimeError):
    pass


def find_npx() -> str:
    executable = shutil.which("npx.cmd") or shutil.which("npx")
    if not executable:
        raise RenderDependencyError("npx is unavailable; install Node.js with npm before running Remotion")
    return executable


def prepare_renderer_job(
    project_root: Path,
    job_id: str,
    language: str,
    timeline: dict[str, Any],
    audio_path: Path,
) -> Path:
    public_dir = project_root / "renderer" / "public" / "jobs" / job_id / language
    public_dir.mkdir(parents=True, exist_ok=True)
    audio_target = public_dir / f"narration{audio_path.suffix.lower()}"
    shutil.copy2(audio_path, audio_target)
    props = dict(timeline)
    props["audioSrc"] = f"jobs/{job_id}/{language}/{audio_target.name}"
    props_path = public_dir / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    return props_path


def run_studio(project_root: Path, props_path: Path) -> int:
    npx = find_npx()
    renderer = project_root / "renderer"
    return subprocess.run(
        [npx, "remotion", "studio", "src/index.ts", "--props", str(props_path)],
        cwd=renderer,
        check=False,
    ).returncode

def run_render(project_root: Path, props_path: Path, output: Path) -> int:
    npx = find_npx()
    renderer = project_root / "renderer"
    output.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            npx,
            "remotion",
            "render",
            "src/index.ts",
            "VidkitShort",
            str(output),
            "--props",
            str(props_path),
            "--codec",
            "h264",
            "--audio-codec",
            "aac",
        ],
        cwd=renderer,
        check=False,
    ).returncode
