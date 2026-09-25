from __future__ import annotations

import json
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .models import ArtifactKind
from .storage import Workspace, sha256_file, slugify


IMAGE_FORMATS = {"PNG": (".png", "image/png"), "JPEG": (".jpg", "image/jpeg"), "WEBP": (".webp", "image/webp")}


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
    evidence_type: str = "artwork",
) -> tuple[dict[str, Any], Path]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    width, height, suffix, mime = detect_image(source)
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
            "evidenceType": evidence_type,
            "mime": mime,
            "originalFilename": source.name,
            "width": width,
            "height": height,
            "sha256": checksum,
            "qualityWarnings": _resolution_warnings(width, height),
        },
        target,
    )


def image_dimensions(path: Path) -> tuple[int, int]:
    width, height, _, _ = detect_image(path)
    return width, height


def detect_image(path: Path) -> tuple[int, int, str, str]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            detected = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError(f"Unsupported or corrupt image: {path}") from exc
    if detected not in IMAGE_FORMATS or width <= 0 or height <= 0:
        raise ValueError(f"Unsupported or corrupt image: {path}")
    suffix, mime = IMAGE_FORMATS[detected]
    return width, height, suffix, mime


def _resolution_warnings(width: int, height: int) -> list[str]:
    warnings: list[str] = []
    if max(width, height) < 720 or min(width, height) < 360:
        warnings.append("low-resolution: use at least 720px on the long edge and 360px on the short edge")
    return warnings
