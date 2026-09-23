import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from vidkit.cli import main
from vidkit.models import ArtifactKind
from vidkit.storage import Workspace


class CliWorkflowTests(unittest.TestCase):
    def test_imported_transcript_builds_provisional_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", str(root), "create", "AI demo", "--languages", "vi"]), 0)
            job_id = output.getvalue().strip()

            script_path = root / "script.json"
            script_path.write_text(
                json.dumps(
                    {
                        "editorial_text": "Xin chào thế giới.",
                        "expected_spoken_text": "Xin chào thế giới.",
                        "tts_input": "[cheerfully] Xin chào thế giới.",
                        "title": "AI demo",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["--root", str(root), "add-script", job_id, "vi", str(script_path)]), 0)

            audio_path = root / "narration.mp3"
            audio_path.write_bytes(b"not-a-real-mp3")
            transcript_path = root / "transcript.json"
            transcript_path.write_text(
                json.dumps(
                    {
                        "language_code": "vie",
                        "text": "Xin chào thế giới.",
                        "words": [
                            {"text": "Xin", "start": 0.0, "end": 0.25, "type": "word"},
                            {"text": "chào", "start": 0.27, "end": 0.55, "type": "word"},
                            {"text": "thế", "start": 0.58, "end": 0.78, "type": "word"},
                            {"text": "giới.", "start": 0.80, "end": 1.1, "type": "word"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main(
                        [
                            "--root",
                            str(root),
                            "import-transcript",
                            job_id,
                            "vi",
                            str(transcript_path),
                            "--audio",
                            str(audio_path),
                        ]
                    ),
                    0,
                )
                self.assertEqual(main(["--root", str(root), "timeline", job_id, "vi"]), 0)

            workspace = Workspace(root)
            transcript = workspace.latest_artifact(job_id, ArtifactKind.TRANSCRIPT, "vi")
            timeline = workspace.latest_artifact(job_id, ArtifactKind.TIMELINE, "vi")
            srt = workspace.latest_artifact(job_id, ArtifactKind.SUBTITLE_SRT, "vi")
            vtt = workspace.latest_artifact(job_id, ArtifactKind.SUBTITLE_VTT, "vi")
            self.assertEqual(transcript["status"], "needs-review")
            self.assertEqual(timeline["status"], "needs-review")
            self.assertTrue((root / srt["path"]).is_file())
            self.assertTrue((root / vtt["path"]).is_file())
            timeline_payload = json.loads((root / timeline["path"]).read_text(encoding="utf-8"))
            self.assertEqual(timeline_payload["storyboardStatus"], "provisional")
            self.assertEqual(timeline_payload["captions"][0]["tokens"][0]["start_ms"], 0)


if __name__ == "__main__":
    unittest.main()
