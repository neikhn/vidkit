import unittest

from vidkit.captions import build_caption_cues
from vidkit.transcript import normalize_transcript, validate_transcript


class TranscriptTests(unittest.TestCase):
    def test_normalizes_segment_export_and_skips_whitespace(self):
        payload = {
            "language_code": "eng",
            "segments": [
                {
                    "words": [
                        {"text": "Every", "start_time": 0.12, "end_time": 0.38},
                        {"text": " ", "start_time": 0.38, "end_time": 0.42},
                        {"text": "kernel", "start_time": 0.42, "end_time": 0.74},
                    ]
                }
            ],
        }
        normalized = normalize_transcript(payload)
        self.assertEqual(normalized["language"], "en")
        self.assertEqual([word["text"] for word in normalized["words"]], ["Every", "kernel"])

    def test_detects_out_of_order_and_script_mismatch(self):
        normalized = {
            "words": [
                {"text": "wrong", "start": 1.0, "end": 1.2},
                {"text": "text", "start": 0.5, "end": 0.8},
            ]
        }
        findings = validate_transcript(normalized, "completely different intended sentence")
        codes = {finding.code for finding in findings}
        self.assertIn("out-of-order", codes)
        self.assertIn("script-mismatch", codes)

    def test_caption_groups_follow_sentence_boundary(self):
        cues = build_caption_cues(
            [
                {"text": "Hello", "start": 0, "end": 0.2},
                {"text": "world.", "start": 0.21, "end": 0.5},
                {"text": "Next", "start": 0.9, "end": 1.1},
            ]
        )
        self.assertEqual([cue.text for cue in cues], ["Hello world.", "Next"])


if __name__ == "__main__":
    unittest.main()
