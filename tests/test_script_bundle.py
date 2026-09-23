import unittest

from vidkit.script_bundle import validate_script_bundle


class ScriptBundleTests(unittest.TestCase):
    def test_accepts_eleven_v3_tags_when_spoken_text_matches(self):
        payload = {
            "editorial_text": "Đây là công cụ mới.",
            "expected_spoken_text": "Đây là công cụ mới.",
            "tts_input": "[curious] Đây là công cụ mới.",
        }
        self.assertEqual(validate_script_bundle(payload), [])

    def test_rejects_text_drift_and_unbalanced_tag(self):
        payload = {
            "editorial_text": "Giá là năm đô.",
            "expected_spoken_text": "Giá là năm đô.",
            "tts_input": "[surprised Giá là mười đô.",
        }
        errors = validate_script_bundle(payload)
        self.assertTrue(any("unbalanced" in error for error in errors))
        self.assertTrue(any("does not match" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
