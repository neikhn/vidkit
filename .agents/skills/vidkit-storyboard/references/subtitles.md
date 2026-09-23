# Subtitle treatment
Project convention, reviewed 2026-09-24.

## Shared timing
Keep detailed word timing as the source for both burned-in animated captions and separate SRT/VTT. SRT/VTT cue exports do not preserve the full styling or per-word animation design.

## Grouping and presentation
- Show a short natural phrase, normally at most two lines.
- Split by meaning, pauses and measured text width, not a rigid character count or export segment boundary.
- Retain Vietnamese diacritics and multi-syllable phrases.
- Highlight current spoken words or a deliberately grouped phrase. Do not highlight whitespace.
- Hold layout stable within a caption group; avoid reflow on every word.
- Provide strong contrast and enough separation from diagrams and platform overlays.
- Represent on-screen numeric abbreviations through explicit mappings to the whole spoken phrase.

## Validation
Inspect long tool names, English acronyms inside Vietnamese speech, punctuation, fast passages and phrase boundaries. Ensure captions refer to the actual audio revision and do not extend beyond it. Check cue ordering and exported text.

Do not include voice-direction tags. Keep subtitle text faithful to speech; scene headlines may summarize separately. A subtitle spelling correction must not conceal a different spoken number or missing sentence.
