# Subtitle treatment
Project convention, reviewed 2026-09-25.

Use final ElevenLabs STT word timing for captions and SRT/VTT. Word timing measures speech alignment, not music beat detection.

In v3, burned-in captions have no box: centered 756px region within 1080px, Noto Sans 48px, white text, dark outline and light shadow. The active word uses the theme accent. Keep position and font stable; never hide overflow with line-clamp. Python measures bundled Noto Sans while compiling, and Remotion rechecks width with browser font metrics after font loading.

Prefer natural phrases and pauses. Avoid a one-word final cue such as “directly.”, a line ending in “at”, a single orphan on the second line, and breaks between a number and its unit. A deliberate emphatic exception is allowed only when explicitly recorded in the caption plan.

An optional caption plan lists contiguous `startWord` and `endWord` groups. For an abbreviation such as `$0.042`, use `displayTokens` with explicit `text`, `startWord`, `endWord`, and `spokenText` that matches the covered transcript words. Every word must be covered exactly once. The display mapping changes visible spelling, never source timing or spoken meaning.

Caption end is at most 120ms after the final spoken word, bounded by the next cue. Inspect fast English speech, Vietnamese diacritics, long product names, currency and units on a 360×640 preview. Mark inspection not-run if it was not performed.
