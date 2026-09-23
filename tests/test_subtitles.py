import unittest

from vidkit.subtitles import render_srt, render_vtt


class SubtitleTests(unittest.TestCase):
    def test_renders_srt_and_vtt_from_shared_cues(self):
        cues = [{"text": "Xin chào", "startMs": 1250, "endMs": 3625, "tokens": []}]
        self.assertIn("00:00:01,250 --> 00:00:03,625", render_srt(cues))
        self.assertIn("00:00:01.250 --> 00:00:03.625", render_vtt(cues))
        self.assertTrue(render_vtt(cues).startswith("WEBVTT\n\n"))


if __name__ == "__main__":
    unittest.main()
