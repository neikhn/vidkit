# Shared handoff contract
Contract version: 3. Reviewed: 2026-09-25.

The Python CLI stores immutable artifact revisions and checksums in SQLite, with readable files under ignored `workspace/videos/`. Existing workflow v2 jobs remain readable; new jobs use v3. Agents use the CLI, never direct SQLite writes. Publishing remains a prepared handoff; no uploader or scheduler is implemented.

Every handoff identifies job ID, language, revision, checksum, upstream revisions, actual path, producing provider/model or component/theme version, completed checks, and unresolved issues. Prepared, generated, checked, needs-review, blocked, approved, published and invalidated are distinct states. Never claim an unperformed API call, visual inspection, listening pass or upload.

## Artifacts

| Artifact | Key content |
|---|---|
| Source | Claim IDs, statements, URLs, dates, uncertainty and visual candidates |
| Script | Editorial text, expected spoken text, Eleven v3 TTS input and claim mapping |
| Creative brief | Angle, theme, hook, visual strategy, sourced screenshot substitute when needed, and three sample frame PNGs |
| Concept approval | Reviewer, time, exact script and brief revisions/checksums |
| Audio | Final MP3 or imported audio, voice/model/settings and checksum |
| Transcript | Raw provider response and normalized word timing tied to audio checksum, plus validation findings |
| Assets | Local checksum, actual MIME/extension, evidence type, dimensions, source, date, usage basis and description |
| Caption plan | Optional contiguous word-index groups and verified display-token mapping |
| Storyboard | Semantic scene purpose, component ID/version, theme, claim IDs, asset ID, source-image crop, word anchors and motion cues |
| Timeline | Derived scene/caption timings, component/theme locks, claim-to-scene mapping and validation findings |
| Preview | Actual MP4 for the current timeline |
| QA | Automatic checks, media probe, frame inspection, transition review, full playback and audio listening, each pass/fail/not-run with evidence |
| Export approval | Reviewer, time, exact timeline, preview and QA revisions/checksums |
| Render | Actual export path, input revisions, component/theme locks, claim-to-scene mapping and QA reference |

Eleven v3 narration → final audio → ElevenLabs STT word-level is the default. Word timing drives scenes, captions and subtitle highlighting; it does not measure music beats. SRT/VTT share cue groups and timing but have no animated styling.

## Revisions and gates

Changing a script invalidates concept approval and spoken downstream work. Changing brief/theme requires new concept approval but preserves audio if spoken text is unchanged. Changing audio invalidates transcript and timed outputs. Changing visual, caption plan, component or storyboard invalidates timeline, preview, QA and export approval while preserving unchanged audio/transcript. Only exact current approval records unlock their gates. “Continue” is never approval.

Review mode stops at concept and export approvals. Automatic mode skips those waits but still blocks on failed source, transcript, asset, timeline, media or render validation. Library candidate promotion is independent from video approval; automatic mode never promotes candidates.

A missing product screenshot is not automatically blocking. Use a sourced official artwork, API example, chart or clear diagram where appropriate, label its true evidence type and note the limitation in brief and QA. Never present a replacement as an actual console screenshot.

Do not repeat an uncertain paid TTS/STT request. If a check cannot run, record `not-run`; audio-level analysis does not count as listening, and frame sampling does not count as full playback.
