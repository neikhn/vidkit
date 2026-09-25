"""Manual, no-API smoke run. Creates a new synthetic job; never touches existing jobs."""
from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path

from vidkit.cli import main
from vidkit.models import ArtifactKind as K, ArtifactStatus as S
from vidkit.storage import Workspace
from vidkit.workflow import add_brief, approve, make_qa


def run() -> str:
    root = Path(__file__).resolve().parents[1]
    workspace = Workspace(root)
    workspace.initialize()
    job = workspace.create_job("Vidkit v3 synthetic smoke", ["en"])
    workspace.add_json_artifact(job, None, K.SOURCE, {"claims": [
        {"id": "claim-1", "statement": "Synthetic fixture", "sourceUrl": "https://example.com",
         "publishedAt": None, "retrievedAt": "2026-09-25", "uncertainty": "Test only"}
    ]}, S.CHECKED)
    workspace.add_json_artifact(job, "en", K.SCRIPT, {"title": "Vidkit v3 smoke",
        "editorial_text": "A structured response shows choices and scores. Then the flow makes the result clear.",
        "expected_spoken_text": "A structured response shows choices and scores. Then the flow makes the result clear.",
        "tts_input": "A structured response shows choices and scores. Then the flow makes the result clear."}, S.CHECKED)
    cache = workspace.cache_root / "smoke-v3"
    cache.mkdir(parents=True, exist_ok=True)
    brief_file = cache / "brief.json"
    brief_file.write_text(json.dumps({
        "angle": "Demonstrate a synthetic API decision",
        "theme": "dark-grid",
        "hook": "Structured output",
        "visualStrategy": "Reveal fields, then diagram the flow",
        "screenshotUnavailable": True,
        "screenshotAlternative": {"type": "api-example", "sourceUrl": "https://example.com",
                                  "reason": "Synthetic fixture has no product console"},
        "frames": {
            "hook": {"headline": "Structured choices", "visualNote": "Product name and explanatory rings"},
            "evidence": {"headline": "Choices and scores", "visualNote": "Large verified JSON fields"},
            "takeaway": {"headline": "A clear decision", "visualNote": "One practical conclusion"},
        },
    }), encoding="utf-8")
    add_brief(workspace, job, "en", brief_file)
    approve(workspace, job, "en", "concept", "Smoke test")
    audio_file = cache / "narration.wav"
    rate = 24000
    with wave.open(str(audio_file), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"".join(struct.pack("<h", round(math.sin(i * 2 * math.pi * 220 / rate) * 500))
                                   for i in range(rate * 5)))
    audio = workspace.add_file_artifact(job, "en", K.AUDIO, audio_file, S.GENERATED)
    tokens = "A structured response shows choices and scores Then the flow makes the result clear".split()
    words = [{"text": token, "start": round(.2 + index * .29, 3),
              "end": round(.44 + index * .29, 3)} for index, token in enumerate(tokens)]
    words[6]["text"] = "scores."
    words[-1]["text"] = "clear."
    workspace.add_json_artifact(job, "en", K.TRANSCRIPT, {"words": words,
        "audio": {"revision": audio["revision"], "sha256": audio["sha256"], "duration_seconds": 5}},
        S.CHECKED, upstream={"audio": audio["revision"]}, metadata={"variant": "normalized"})
    storyboard = {"schemaVersion": 3, "language": "en", "theme": "dark-grid", "scenes": [
        {"id": "hook", "layout": "brand-hook", "title": "Structured choices", "body": "A synthetic demo",
         "claimIds": ["claim-1"], "startAnchor": {"wordIndex": 0}, "endAnchor": {"wordIndex": 2}},
        {"id": "response", "layout": "api-response", "title": "What the response contains",
         "body": "choice, score, confidence", "claimIds": ["claim-1"],
         "startAnchor": {"wordIndex": 3}, "endAnchor": {"wordIndex": 6}},
        {"id": "flow", "layout": "diagram-flow", "title": "How it flows",
         "body": "Input → Analysis → Decision", "claimIds": ["claim-1"],
         "startAnchor": {"wordIndex": 7}, "endAnchor": {"wordIndex": 10}},
        {"id": "takeaway", "layout": "takeaway", "title": "Clear output", "body": "Code can use the result",
         "claimIds": ["claim-1"], "startAnchor": {"wordIndex": 11}, "endAnchor": {"wordIndex": 13}},
    ]}
    storyboard_file = cache / "storyboard.json"
    storyboard_file.write_text(json.dumps(storyboard), encoding="utf-8")
    assert main(["--root", str(root), "add-storyboard", job, "en", str(storyboard_file)]) == 0
    assert main(["--root", str(root), "timeline", job, "en"]) == 0
    assert main(["--root", str(root), "preview", job, "en"]) == 0
    make_qa(workspace, job, "en")
    assert main(["--root", str(root), "render", job, "en"]) == 2
    approve(workspace, job, "en", "export", "Smoke test")
    assert main(["--root", str(root), "render", job, "en"]) == 0
    return job


if __name__ == "__main__":
    print(run())
