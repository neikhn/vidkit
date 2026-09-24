from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from mutagen import File as MutagenFile, MutagenError


def audio_duration(path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
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
            pass
    try:
        media = MutagenFile(path)
        duration = float(media.info.length) if media is not None and media.info else 0.0
        return duration if duration > 0 else None
    except (MutagenError, OSError, ValueError, AttributeError):
        return None
