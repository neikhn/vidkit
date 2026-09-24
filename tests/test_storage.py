import json
import tempfile
import unittest
from pathlib import Path

from vidkit.models import ArtifactKind, ArtifactStatus
from vidkit.storage import Workspace


class StorageTests(unittest.TestCase):
    def test_revisions_and_downstream_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory))
            job = workspace.create_job("demo", ["vi"])
            script = workspace.add_json_artifact(
                job, "vi", ArtifactKind.SCRIPT, {"text": "one"}, ArtifactStatus.CHECKED
            )
            audio_source = Path(directory) / "audio.mp3"
            audio_source.write_bytes(b"fake")
            audio = workspace.add_file_artifact(
                job,
                "vi",
                ArtifactKind.AUDIO,
                audio_source,
                ArtifactStatus.GENERATED,
                upstream={"script": script["revision"]},
            )
            workspace.invalidate_downstream(job, "vi", ArtifactKind.SCRIPT)
            current = workspace.latest_artifact(job, ArtifactKind.AUDIO, "vi")
            self.assertIsNone(current)
            invalidated = workspace.latest_artifact(job, ArtifactKind.AUDIO, "vi", True)
            self.assertEqual(invalidated["status"], "invalidated")
            self.assertEqual(json.loads(workspace.resolve_path(script).read_text()), {"text": "one"})
            self.assertEqual(audio["revision"], 1)

    def test_folder_name_stays_stable_when_title_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory))
            job_id = workspace.create_job("Công cụ AI", ["vi"])
            before = workspace.get_job(job_id)
            workspace.rename_job(job_id, "Tên mới")
            after = workspace.get_job(job_id)
            self.assertEqual(before["folder_name"], after["folder_name"])
            self.assertIn("cong-cu-ai", before["folder_name"])
            manifest = json.loads((workspace.job_root(job_id) / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["title"], "Tên mới")

    def test_visual_change_keeps_audio_and_invalidates_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory))
            job = workspace.create_job("demo", ["vi"])
            audio_source = Path(directory) / "audio.mp3"
            audio_source.write_bytes(b"fake")
            workspace.add_file_artifact(
                job, "vi", ArtifactKind.AUDIO, audio_source, ArtifactStatus.GENERATED
            )
            workspace.add_json_artifact(
                job,
                "vi",
                ArtifactKind.TIMELINE,
                {"scenes": []},
                ArtifactStatus.NEEDS_REVIEW,
            )

            workspace.invalidate_visuals(job)

            self.assertIsNotNone(workspace.latest_artifact(job, ArtifactKind.AUDIO, "vi"))
            self.assertIsNone(workspace.latest_artifact(job, ArtifactKind.TIMELINE, "vi"))

    def test_audio_change_invalidates_timing_but_keeps_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory))
            job = workspace.create_job("demo", ["vi"])
            workspace.add_json_artifact(
                job,
                None,
                ArtifactKind.ASSET_MANIFEST,
                {"schemaVersion": 1, "assets": []},
                ArtifactStatus.CHECKED,
            )
            workspace.add_json_artifact(
                job, "vi", ArtifactKind.TRANSCRIPT, {"words": []}, ArtifactStatus.CHECKED
            )
            workspace.add_json_artifact(
                job, "vi", ArtifactKind.STORYBOARD, {"scenes": []}, ArtifactStatus.CHECKED
            )
            workspace.add_json_artifact(
                job, "vi", ArtifactKind.TIMELINE, {"scenes": []}, ArtifactStatus.NEEDS_REVIEW
            )

            workspace.invalidate_downstream(job, "vi", ArtifactKind.AUDIO)

            self.assertIsNotNone(
                workspace.latest_artifact(job, ArtifactKind.ASSET_MANIFEST, None)
            )
            self.assertIsNone(workspace.latest_artifact(job, ArtifactKind.TRANSCRIPT, "vi"))
            self.assertIsNone(workspace.latest_artifact(job, ArtifactKind.STORYBOARD, "vi"))
            self.assertIsNone(workspace.latest_artifact(job, ArtifactKind.TIMELINE, "vi"))

    def test_duplicate_titles_have_distinct_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory))
            first = workspace.create_job("Cùng tiêu đề", ["vi"])
            second = workspace.create_job("Cùng tiêu đề", ["vi"])
            self.assertNotEqual(
                workspace.get_job(first)["folder_name"], workspace.get_job(second)["folder_name"]
            )


if __name__ == "__main__":
    unittest.main()
