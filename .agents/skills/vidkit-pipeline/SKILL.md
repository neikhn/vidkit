---
name: vidkit-pipeline
description: Coordinate Vidkit AI Shorts production across research, bilingual scripting, ElevenLabs narration and transcription, storyboard, rendering, and review or automatic publishing. Use for multi-stage requests and resuming jobs.
---
# Vidkit pipeline

## Inputs and routing
Read [handoff contract](references/handoff-contract.md) before coordinating stages. Accept a topic, source URL, or existing artifacts. Inspect available artifacts and their revisions; enter at the earliest missing or invalid stage, without recreating valid work.

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
5. Report actual stage status, artifact locations and the next concrete dependency.

Daily discovery plus on-demand input is the intended operating model, not an installed schedule. Skills do not start background work.

## Completion and missing capabilities
Finish only the stages requested and supported by available tools. These files contain instructions, not an API client, renderer, job database or scheduler. When execution is unavailable, deliver a labeled specification or prepared artifact and state what remains unexecuted. Never invent successful API calls, checks or publication.

For maintenance reviews, use [handoff scenarios](references/handoff-scenarios.md).
