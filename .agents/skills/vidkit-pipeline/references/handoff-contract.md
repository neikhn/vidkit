# Shared handoff contract
Contract version: 2. Reviewed: 2026-09-24.

The Python runtime implements revisioned source, script, audio, transcript, asset manifest, storyboard, timeline and render records. Publication remains a prepared handoff until an authorized uploader is implemented. Sibling modules use this source rather than duplicating contracts.

## Common envelope
Every stage handoff identifies the job/topic, language, artifact revision, upstream revisions, producing skill/template version where known, actual output location, check results and unresolved issues. Record actual provider/model/settings when a service is used. Never invent missing identifiers, measurements or checksums.

Distinguish prepared, generated, checked, needs-review, blocked, approved and published. A prepared prompt is not generated audio; a render specification is not an MP4; an upload is not proof of public availability.

## Artifacts
| Artifact | Required content |
|---|---|
| Source pack | Claim IDs, supporting excerpts/URLs, publication and retrieval dates, uncertainty, asset origin and usage basis |
| Script bundle | Language, stable beat IDs, clean editorial narration, expected spoken text, optional TTS input, display text mappings, claim references |
| Audio record | Final narration file, actual duration, revision/checksum when available, model, voice ID, settings and generation provenance |
| Transcript | Unmodified provider/export response plus normalized words with text/start/end in seconds, audio identity, language, segment boundaries and validation findings |
| Asset manifest | Local immutable image identity, source, retrieval date, usage basis, dimensions, checksum and description |
| Storyboard | Semantic scene purpose, layout, display text, asset ID/crop and checked transcript word anchors; no invented timestamps |
| Timeline | Scene/beat IDs, word or phrase anchors, absolute timing, scene type, assets, display text, captions, evidence references and optional separate music/SFX |
| Render record | Input revisions, template version, preview/export paths, format and observed visual/audio checks |
| Publication record | Exact render and metadata revisions, destination, mode, approval if required, upload ID, processing/visibility status, schedule and result |

Scene and caption timing derive from the final audio's transcript. Preserve mappings between editorial text, pronunciation-expanded spoken text and display text. Retain raw data when corrections are made.

## Invalidation and reuse
- Changed evidence invalidates affected claims/scripts and dependent outputs.
- Changed spoken content, pronunciation, voice or TTS settings invalidates audio and downstream artifacts.
- Replacing, trimming, joining or retiming audio invalidates transcript and timed downstream artifacts; transcribe the final audio again for this workflow.
- Caption-only or visual edits invalidate affected timeline/render/publication approval, not unchanged audio or transcription.
- Metadata-only edits invalidate approval of the publication package, not the render.
- Keep earlier revisions for comparison. Reuse only artifacts whose upstream inputs remain unchanged.
- If one language changes, invalidate that language only, unless shared facts/assets also changed.

## Modes and failure handling
Review mode requires explicit approval of the exact publication package. Automatic mode uses the user's configured publishing authorization and destination; it does not waive checks. Unresolved source, transcript, asset or render issues go to review. Mode selection is not permission to install tools, create accounts or broaden destinations.

Before paid work, establish the configured usage/retry budget. Default content repair allows one automatic audio regeneration within that budget; persistent problems go to review. Do not blindly repeat an uncertain paid request. For an uncertain upload, reconcile existing upload state before another upload.

Technical checks and content checks are distinct. An LLM saying “looks good” cannot substitute for measuring timestamps or inspecting a rendered file. When automation code is absent, mark checks not run rather than claiming automated validation.

## Maintenance
Store skills with the project; record revisions using repository revision when available or an explicit document version. Test changed guidance against representative artifacts before automatic use. Keep provider-specific details in the relevant reference with official URLs and verification dates. Recheck them when compatibility changes or a documented behavior fails.
