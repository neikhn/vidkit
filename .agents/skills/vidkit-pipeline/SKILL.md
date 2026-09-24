---
name: vidkit-pipeline
description: Coordinate Vidkit AI Shorts production across research, bilingual scripting, ElevenLabs narration and transcription, storyboard, rendering, and review or automatic publishing. Use for multi-stage requests and resuming jobs.
---
# Vidkit pipeline

## Inputs and routing
Read [handoff contract](references/handoff-contract.md) before coordinating stages. Accept a topic, source URL, or existing artifacts. Inspect available artifacts and their revisions; enter at the earliest missing or invalid stage, without recreating valid work.
For executable commands and JSON shapes, read [CLI workflow](references/cli-workflow.md).

Route only the needed modules:
- [research](../vidkit-research/SKILL.md): sources and evidence.
- [script](../vidkit-script/SKILL.md): localized narration.
- [voice](../vidkit-voice/SKILL.md): Eleven v3 preparation and audio.
- [transcript](../vidkit-transcript/SKILL.md): final audio to word-level text.
- [storyboard](../vidkit-storyboard/SKILL.md): timed scenes and captions.
- [render](../vidkit-render/SKILL.md): specification, preview and export.
- [publish](../vidkit-publish/SKILL.md): metadata, publishing and performance.

## Workflow
1. Establish requested languages, entry point, artifacts and mode. Defaults: Vietnamese and English, review mode, 45–75 seconds per version.
2. Maintain independent localized revisions; research and authorized visual assets may be shared.
3. Follow script → Eleven v3 TTS → final MP3 → ElevenLabs STT word-level → checks → storyboard → render → publishing.
4. Apply dependency invalidation from the contract after edits.
5. Use `vidkit next <job-id> --language <language> --json` after each handoff.
6. Report actual stage status, workspace artifact locations and the next concrete dependency.

Daily discovery plus on-demand input is the intended operating model, not an installed schedule. Skills do not start background work.

## Completion and missing capabilities
The repository includes the Python CLI, revision database, ElevenLabs client and Remotion renderer. Research, writing, asset selection and storyboard authoring are agent work imported through checked CLI interfaces; no embedded LLM service or scheduler exists. When a stage cannot execute, deliver a labeled artifact and state what remains. Never invent successful API calls, checks or publication.

For maintenance reviews, use [handoff scenarios](references/handoff-scenarios.md).
