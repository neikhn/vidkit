import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from vidkit.storage import Workspace


class MigrationTests(unittest.TestCase):
    def test_legacy_migration_preserves_identity_revision_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / ".vidkit"
            artifact_dir = legacy / "artifacts" / "job123" / "vi"
            artifact_dir.mkdir(parents=True)
            artifact_path = artifact_dir / "script.r1.json"
            artifact_path.write_text(json.dumps({"title": "Demo"}), encoding="utf-8")
            checksum = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            database = sqlite3.connect(legacy / "vidkit.sqlite3")
            database.executescript(
                """
                CREATE TABLE jobs (
                  id TEXT PRIMARY KEY, topic TEXT, source_url TEXT, mode TEXT,
                  languages_json TEXT, status TEXT, created_at TEXT, updated_at TEXT
                );
                CREATE TABLE artifacts (
                  id INTEGER PRIMARY KEY, job_id TEXT, language TEXT, kind TEXT,
                  revision INTEGER, status TEXT, path TEXT, sha256 TEXT,
                  upstream_json TEXT, metadata_json TEXT, created_at TEXT
                );
                """
            )
            database.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("job123", "Demo", None, "review", '["vi"]', "checked", "2026-09-24T00:00:00+00:00", "2026-09-24T00:00:00+00:00"),
            )
            database.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (1, "job123", "vi", "script", 1, "checked", ".vidkit/artifacts/job123/vi/script.r1.json", checksum, "{}", "{}", "2026-09-24T00:00:00+00:00"),
            )
            database.commit()
            database.close()

            workspace = Workspace(root)
            first = workspace.migrate_legacy()
            second = workspace.migrate_legacy()
            self.assertEqual(first, {"jobs": 1, "artifacts": 1, "skipped_jobs": 0})
            self.assertEqual(second, {"jobs": 0, "artifacts": 0, "skipped_jobs": 1})
            job = workspace.get_job("job123")
            self.assertEqual(job["folder_name"], "2026-09-24_demo_job123")
            artifact = workspace.list_artifacts("job123")[0]
            self.assertEqual(artifact["revision"], 1)
            self.assertEqual(hashlib.sha256(workspace.resolve_path(artifact).read_bytes()).hexdigest(), checksum)

            with workspace.connect() as conn:
                conn.execute("DELETE FROM artifacts WHERE job_id = ?", ("job123",))
            resumed = workspace.migrate_legacy()
            self.assertEqual(resumed["jobs"], 0)
            self.assertEqual(resumed["artifacts"], 1)


if __name__ == "__main__":
    unittest.main()
