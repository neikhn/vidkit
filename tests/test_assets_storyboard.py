import tempfile
import unittest
from pathlib import Path

from PIL import Image

from vidkit.assets import image_dimensions, prepare_asset_entry
from vidkit.storage import Workspace
from vidkit.timeline import compile_storyboard, validate_storyboard_shape


class AssetStoryboardTests(unittest.TestCase):
    def test_reads_png_dimensions_and_compiles_anchored_scenes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = Workspace(root)
            job_id = workspace.create_job("Demo", ["vi"])
            image = root / "screen.png"
            Image.new("RGB", (1200, 800), "white").save(image)
            self.assertEqual(image_dimensions(image), (1200, 800))
            entry, _ = prepare_asset_entry(
                workspace, job_id, image, "Màn hình sản phẩm", "official-media", "https://example.com"
            )
            words = [
                {"text": "Xin", "start": 0.1, "end": 0.3},
                {"text": "chào", "start": 0.32, "end": 0.6},
                {"text": "bạn", "start": 0.7, "end": 0.9},
                {"text": "nhé", "start": 0.92, "end": 1.2},
            ]
            storyboard = {
                "schemaVersion": 1,
                "scenes": [
                    {
                        "id": "hook",
                        "layout": "hook",
                        "title": "Xin chào",
                        "startAnchor": {"wordIndex": 0, "text": "Xin"},
                        "endAnchor": {"wordIndex": 1, "text": "chào"},
                    },
                    {
                        "id": "demo",
                        "layout": "screenshot",
                        "title": "Demo",
                        "assetId": entry["id"],
                        "startAnchor": {"wordIndex": 2, "text": "bạn"},
                        "endAnchor": {"wordIndex": 3, "text": "nhé"},
                    },
                ],
            }
            timeline, missing = compile_storyboard(
                {"words": words, "audio": {"duration_seconds": 1.4}},
                storyboard,
                {"schemaVersion": 1, "assets": [entry]},
                "Demo",
                "vi",
                "audio.mp3",
            )
            self.assertEqual(missing, [])
            self.assertEqual(timeline["storyboardStatus"], "checked")
            self.assertEqual(timeline["scenes"][0]["startMs"], 0)
            self.assertEqual(timeline["scenes"][-1]["endMs"], 1400)

    def test_rejects_corrupt_images(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "broken.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\nnot-an-image")
            with self.assertRaises(ValueError):
                image_dimensions(image)

    def test_accepts_portrait_images_and_warns_for_low_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = Workspace(root)
            job_id = workspace.create_job("Demo", ["vi"])
            portrait = root / "portrait.jpg"
            Image.new("RGB", (600, 1200), "white").save(portrait)
            entry, _ = prepare_asset_entry(
                workspace, job_id, portrait, "Portrait", "user-provided", None
            )
            self.assertEqual((entry["width"], entry["height"]), (600, 1200))
            self.assertEqual(entry["qualityWarnings"], [])

            small = root / "small.webp"
            Image.new("RGB", (200, 300), "white").save(small)
            entry, _ = prepare_asset_entry(
                workspace, job_id, small, "Small", "user-provided", None
            )
            self.assertTrue(entry["qualityWarnings"])

    def test_storyboard_import_validation_rejects_missing_anchors(self):
        errors = validate_storyboard_shape(
            {
                "schemaVersion": 1,
                "scenes": [{"id": "hook", "layout": "hook", "title": "Demo"}],
            }
        )
        self.assertIn("scene 1 startAnchor.wordIndex is required", errors)

    def test_missing_required_asset_blocks_timeline(self):
        words = [{"text": "Demo", "start": 0.0, "end": 0.5}]
        storyboard = {
            "schemaVersion": 1,
            "scenes": [
                {
                    "layout": "screenshot",
                    "title": "Demo",
                    "assetId": "missing",
                    "startAnchor": {"wordIndex": 0},
                    "endAnchor": {"wordIndex": 0},
                }
            ],
        }
        timeline, missing = compile_storyboard(
            {"words": words}, storyboard, {"assets": []}, "Demo", "vi", "audio.mp3"
        )
        self.assertEqual(missing, ["missing"])
        self.assertEqual(timeline["storyboardStatus"], "blocked")


if __name__ == "__main__":
    unittest.main()
