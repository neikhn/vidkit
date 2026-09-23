from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def audio_duration(path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        completed = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        return float(payload["format"]["duration"])
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
