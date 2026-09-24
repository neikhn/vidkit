---
name: vidkit-script
description: Write and localize Vidkit AI Shorts scripts in Vietnamese and English from an evidence pack, preserving factual meaning and mapping narrative beats to visual ideas.
---
# Script

## Input and output
Input: source pack, requested languages and optional existing script.
Output: script bundle under the [handoff contract](../vidkit-pipeline/references/handoff-contract.md).

## Workflow
1. Choose one concrete promise or question. Structure the story around hook, identity, evidence, mechanism, limitation and takeaway where appropriate.
2. Attach claim references to factual statements and stable IDs to narrative beats.
3. Write Vietnamese and English as natural localized narration, preserving numbers, uncertainty and meaning. Do not translate idioms literally.
4. Target 45–75 seconds by default, but label length as estimated until actual narration is available.
5. Supply a visual idea per beat without inventing demonstrations or benchmark results.
6. Keep clean editorial narration separate from display text; hand pronunciation and expression preparation to [voice](../vidkit-voice/SKILL.md).
7. Save each language with `vidkit add-script <job-id> <language> <script.json>`; keep visuals out of `tts_input`.

## Completion and missing inputs
Complete when scripts are coherent, supported and ready for voice preparation. Each episode must add a specific explanation or useful judgment; reusable graphics are not a substitute for original content.

If claims lack evidence, return them to research. If a supplied script is only being prepared for TTS, preserve its content and flag factual concerns separately instead of silently rewriting it. Existing approved wording takes precedence over a preferred storytelling formula.
