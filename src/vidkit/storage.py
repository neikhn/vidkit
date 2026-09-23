from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

from .models import ArtifactKind, ArtifactStatus, Mode


STAGE_ORDER = [kind.value for kind in ArtifactKind]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Workspace:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.state_root = self.project_root / ".vidkit"
        self.db_path = self.state_root / "vidkit.sqlite3"
        self.artifacts_root = self.state_root / "artifacts"

    def initialize(self) -> None:
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY,
                  topic TEXT NOT NULL,
                  source_url TEXT,
                  mode TEXT NOT NULL,
                  languages_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_id TEXT NOT NULL REFERENCES jobs(id),
                  language TEXT,
                  kind TEXT NOT NULL,
                  revision INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  path TEXT NOT NULL,
                  sha256 TEXT NOT NULL,
                  upstream_json TEXT NOT NULL,
                  metadata_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  UNIQUE(job_id, language, kind, revision)
                );
                CREATE INDEX IF NOT EXISTS idx_artifact_latest
                  ON artifacts(job_id, language, kind, revision DESC);
                """
            )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.state_root.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def create_job(
        self,
        topic: str,
        languages: Iterable[str],
        mode: Mode = Mode.REVIEW,
        source_url: str | None = None,
    ) -> str:
        self.initialize()
        job_id = uuid.uuid4().hex[:12]
        now = utc_now()
        normalized_languages = list(dict.fromkeys(lang.strip() for lang in languages if lang.strip()))
        if not normalized_languages:
            raise ValueError("At least one language is required")
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    topic,
                    source_url,
                    mode.value,
                    json.dumps(normalized_languages, ensure_ascii=False),
                    "prepared",
                    now,
                    now,
                ),
            )
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown job: {job_id}")
        result = dict(row)
        result["languages"] = json.loads(result.pop("languages_json"))
        return result

    def job_dir(self, job_id: str, language: str | None = None) -> Path:
        target = self.artifacts_root / job_id
        if language:
            target /= language
        target.mkdir(parents=True, exist_ok=True)
        return target

    def latest_artifact(
        self,
        job_id: str,
        kind: ArtifactKind | str,
        language: str | None,
        include_invalidated: bool = False,
    ) -> dict[str, Any] | None:
        kind_value = kind.value if isinstance(kind, ArtifactKind) else kind
        invalidated_filter = "" if include_invalidated else "AND status != 'invalidated'"
        query = f"""
            SELECT * FROM artifacts
            WHERE job_id = ? AND kind = ? AND language IS ? {invalidated_filter}
            ORDER BY revision DESC LIMIT 1
        """
        with self.connect() as conn:
            row = conn.execute(query, (job_id, kind_value, language)).fetchone()
        return self._decode_artifact(row) if row else None

    def list_artifacts(self, job_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM artifacts WHERE job_id = ? ORDER BY language, kind, revision",
                (job_id,),
            ).fetchall()
        return [self._decode_artifact(row) for row in rows]

    def add_json_artifact(
        self,
        job_id: str,
        language: str | None,
        kind: ArtifactKind,
        payload: dict[str, Any],
        status: ArtifactStatus,
        upstream: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.get_job(job_id)
        revision = self._next_revision(job_id, language, kind)
        output = self.job_dir(job_id, language) / f"{kind.value}.r{revision}.json"
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return self._record_artifact(
            job_id, language, kind, revision, status, output, upstream, metadata
        )

    def add_file_artifact(
        self,
        job_id: str,
        language: str | None,
        kind: ArtifactKind,
        source: Path,
        status: ArtifactStatus,
        upstream: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.get_job(job_id)
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        revision = self._next_revision(job_id, language, kind)
        output = self.job_dir(job_id, language) / f"{kind.value}.r{revision}{source.suffix.lower()}"
        if source != output.resolve():
            shutil.copy2(source, output)
        return self._record_artifact(
            job_id, language, kind, revision, status, output, upstream, metadata
        )

    def invalidate_downstream(self, job_id: str, language: str, changed_kind: ArtifactKind) -> None:
        index = STAGE_ORDER.index(changed_kind.value)
        downstream = STAGE_ORDER[index + 1 :]
        if not downstream:
            return
        placeholders = ",".join("?" for _ in downstream)
        with self.connect() as conn:
            conn.execute(
                f"""
                UPDATE artifacts SET status = 'invalidated'
                WHERE job_id = ? AND language IS ? AND kind IN ({placeholders})
                  AND status != 'published'
                """,
                (job_id, language, *downstream),
            )
            conn.execute("UPDATE jobs SET updated_at = ? WHERE id = ?", (utc_now(), job_id))

    def _next_revision(self, job_id: str, language: str | None, kind: ArtifactKind) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(revision), 0) + 1 AS revision FROM artifacts "
                "WHERE job_id = ? AND language IS ? AND kind = ?",
                (job_id, language, kind.value),
            ).fetchone()
        return int(row["revision"])

    def _record_artifact(
        self,
        job_id: str,
        language: str | None,
        kind: ArtifactKind,
        revision: int,
        status: ArtifactStatus,
        path: Path,
        upstream: dict[str, int] | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        now = utc_now()
        rel_path = path.resolve().relative_to(self.project_root).as_posix()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts
                (job_id, language, kind, revision, status, path, sha256,
                 upstream_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    language,
                    kind.value,
                    revision,
                    status.value,
                    rel_path,
                    sha256_file(path),
                    json.dumps(upstream or {}, ensure_ascii=False),
                    json.dumps(metadata or {}, ensure_ascii=False),
                    now,
                ),
            )
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, job_id),
            )
            row = conn.execute("SELECT * FROM artifacts WHERE id = last_insert_rowid()").fetchone()
        return self._decode_artifact(row)

    @staticmethod
    def _decode_artifact(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["upstream"] = json.loads(result.pop("upstream_json"))
        result["metadata"] = json.loads(result.pop("metadata_json"))
        return result
