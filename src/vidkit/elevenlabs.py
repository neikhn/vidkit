from __future__ import annotations

import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ElevenLabsError(RuntimeError):
    pass


class ElevenLabsClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.elevenlabs.io"):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ElevenLabsError("ELEVENLABS_API_KEY is not configured")
        self.base_url = base_url.rstrip("/")

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        output: Path,
        model_id: str = "eleven_v3",
        stability: float | None = None,
    ) -> None:
        voice_settings: dict[str, Any] = {}
        if stability is not None:
            voice_settings["stability"] = stability
        payload: dict[str, Any] = {"text": text, "model_id": model_id}
        if voice_settings:
            payload["voice_settings"] = voice_settings
        response = self._request(
            f"/v1/text-to-speech/{quote(voice_id, safe='')}?output_format=mp3_44100_128",
            json.dumps(payload).encode("utf-8"),
            "application/json",
            accept="audio/mpeg",
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response)

    def speech_to_text(
        self,
        audio: Path,
        model_id: str = "scribe_v2",
        language_code: str | None = None,
    ) -> dict[str, Any]:
        fields = {
            "model_id": model_id,
            "timestamps_granularity": "word",
            "diarize": "false",
        }
        if language_code:
            fields["language_code"] = language_code
        body, content_type = _multipart(audio, fields)
        response = self._request("/v1/speech-to-text", body, content_type, accept="application/json")
        try:
            payload = json.loads(response.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ElevenLabsError("ElevenLabs returned invalid STT JSON") from exc
        if not isinstance(payload, dict):
            raise ElevenLabsError("Unexpected STT response")
        return payload

    def _request(self, path: str, body: bytes, content_type: str, accept: str) -> bytes:
        request = Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={
                "xi-api-key": self.api_key or "",
                "Content-Type": content_type,
                "Accept": accept,
                "User-Agent": "vidkit/0.1",
            },
        )
        try:
            with urlopen(request, timeout=180) as response:
                return response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ElevenLabsError(f"ElevenLabs returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise ElevenLabsError(f"Could not reach ElevenLabs: {exc}") from exc


def _multipart(file_path: Path, fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"vidkit-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
