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
            self.assertEqual(json.loads((Path(directory) / script["path"]).read_text()), {"text": "one"})
            self.assertEqual(audio["revision"], 1)


if __name__ == "__main__":
    unittest.main()
