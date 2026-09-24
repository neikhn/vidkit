import os
import tempfile
import unittest
from pathlib import Path

from vidkit.config import load_env_file, voice_id_for


class ConfigTests(unittest.TestCase):
    def test_loads_dotenv_without_overriding_process_environment(self):
        keys = ("ELEVENLABS_API_KEY", "VIDKIT_VOICE_VI")
        previous = {key: os.environ.get(key) for key in keys}
        try:
            os.environ["ELEVENLABS_API_KEY"] = "from-process"
            os.environ.pop("VIDKIT_VOICE_VI", None)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / ".env"
                path.write_text(
                    "ELEVENLABS_API_KEY=from-file\nVIDKIT_VOICE_VI='voice-vi'\n",
                    encoding="utf-8",
                )
                load_env_file(path)
            self.assertEqual(os.environ["ELEVENLABS_API_KEY"], "from-process")
            self.assertEqual(voice_id_for("vi"), "voice-vi")
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

if __name__ == "__main__":
    unittest.main()
