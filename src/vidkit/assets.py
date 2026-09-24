from __future__ import annotations

import json
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .models import ArtifactKind
from .storage import Workspace, sha256_file, slugify


SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def load_asset_manifest(workspace: Workspace, job_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    artifact = workspace.latest_artifact(job_id, ArtifactKind.ASSET_MANIFEST, None)
    if artifact is None:
        return {"schemaVersion": 1, "assets": []}, None
    payload = json.loads(workspace.resolve_path(artifact).read_text(encoding="utf-8"))
    return payload, artifact


def prepare_asset_entry(
    workspace: Workspace,
    job_id: str,
    source: Path,
    description: str,
    usage_basis: str,
    source_url: str | None,
) -> tuple[dict[str, Any], Path]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError("Asset must be a PNG, JPEG or WebP image")
    width, height = image_dimensions(source)
    checksum = sha256_file(source)
    asset_id = f"{slugify(description or source.stem, 30)}-{checksum[:8]}"
    target = workspace.asset_dir(job_id) / f"{asset_id}{suffix}"
    return (
        {
            "id": asset_id,
            "path": target.relative_to(workspace.workspace_root).as_posix(),
            "sourceUrl": source_url,
            "retrievedAt": datetime.now(UTC).isoformat(),
            "usageBasis": usage_basis.strip(),
            "description": unicodedata.normalize("NFC", description.strip()),
            "width": width,
            "height": height,
            "sha256": checksum,
            "qualityWarnings": _resolution_warnings(width, height),
        },
        target,
    )


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            detected = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError(f"Unsupported or corrupt image: {path}") from exc
    if detected not in {"PNG", "JPEG", "WEBP"} or width <= 0 or height <= 0:
        raise ValueError(f"Unsupported or corrupt image: {path}")
    return width, height


def _resolution_warnings(width: int, height: int) -> list[str]:
    warnings: list[str] = []
    if max(width, height) < 720 or min(width, height) < 360:
        warnings.append("low-resolution: use at least 720px on the long edge and 360px on the short edge")
    return warnings
