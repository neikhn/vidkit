---
name: vidkit-transcript
description: Prepare or validate ElevenLabs STT word-level transcripts for Vidkit final narration, including imported export JSON, script comparison and audio timing handoff.
---
# Transcript

## Input and output
Input: final narration MP3, expected spoken script if available, optional existing transcript.
Output: preserved raw transcript, normalized timed words and validation findings.
Read the [contract](../vidkit-pipeline/references/handoff-contract.md) and [transcript handling](references/transcript-handling.md).

## Workflow
1. Establish which final audio revision the transcript belongs to.
2. Reuse a valid matching transcript. Otherwise, when authorized tools exist, request ElevenLabs STT using scribe_v2 with word-level timestamps on narration without music.
3. Normalize API/export fields without overwriting raw evidence. Exclude whitespace and non-speech events from spoken-word highlighting.
4. Check temporal validity and compare recognized content with expected speech. Ignore harmless punctuation/case/number-format differences, but flag changed quantities, missing phrases and name errors.
5. Preserve uncertain corrections and findings; do not silently rewrite recognized text to make it match the script.
6. Hand off checked words and unresolved issues to storyboard.

## Completion and missing inputs
Without MP3, structural inspection is possible but audio synchronization remains unverified. Without the expected script, timing inspection is possible but fidelity to intended wording remains unverified. Missing API tooling means transcription is not executed.

Timestamps locate speech; they do not prove factual correctness, musical beats or vocal emphasis. Unresolved material mismatches block automatic publishing.
