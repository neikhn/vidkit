from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def resolve_node() -> Path | None:
    candidates: list[str | Path] = []
    configured = os.environ.get("VIDKIT_NODE_PATH")
    if configured:
        candidates.append(configured)
    found = shutil.which("node.exe") or shutil.which("node")
    if found:
        candidates.append(found)
    fnm = os.environ.get("FNM_MULTISHELL_PATH")
    if fnm:
        candidates.append(Path(fnm) / "node.exe")
    appdata = os.environ.get("APPDATA")
    program_files = os.environ.get("ProgramFiles")
    if appdata:
        candidates.append(Path(appdata) / "npm" / "node.exe")
    if program_files:
        candidates.append(Path(program_files) / "nodejs" / "node.exe")
    for candidate in candidates:
        path = Path(candidate).expanduser()
        if not path.is_file():
            continue
        try:
            result = subprocess.run([str(path), "--version"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and result.stdout.strip().startswith("v"):
            return path.resolve()
    return None
