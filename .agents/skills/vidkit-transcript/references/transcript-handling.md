# Transcript handling
Verified: 2026-09-24.
Official source: [ElevenLabs Create transcript](https://elevenlabs.io/docs/api-reference/speech-to-text/convert).
The API documents word timestamps and speaker/event metadata; do not assume a UI export has an identical response shape.

## Input adapters to specify
- API words: text, start, end and any returned type/speaker metadata.
- Supplied export shape: language_code, segments with text/start_time/end_time and nested words using text/start_time/end_time.
- Normalize to text/start/end in seconds; retain source indices and raw records. Normalize language aliases such as eng/en and vie/vi without losing original values.
- Preserve whitespace for reconstructing text, but omit whitespace-only entries from spoken animation events.
- Keep non-speech events separately; do not turn them into spoken captions automatically.

## Checks
Check finite numeric times, nonnegative starts, end greater than start for spoken words, ordering and containment within measured audio duration. Flag overlap or suspect boundaries for inspection rather than mechanically adjusting evidence. Missing timing is not permission to estimate timing from word count.

Compare expected speech after removing delivery instructions through the script's explicit spoken-text mapping. Do not use indiscriminate bracket deletion that could remove real content. Recognized tags spoken aloud are narration errors.

Normalize benign number spelling and punctuation for comparison. Flag changed names, quantities, negation, added claims, omissions or repeated passages. A corrected transcript must retain the raw recognition and correction reason. Uncertain discrepancies need audio review; STT is not infallible.

## Segments and captions
Export segments are grouping hints, not guaranteed sentences or scenes. Join “The hard outer” with a following “shell…” before deciding phrase boundaries. Use word timing to regroup captions without changing the audio clock.

Vietnamese space-separated units can be syllables within a multi-syllable word. Preserve natural phrases and diacritics; do not assume every space identifies an independent semantic word.

## Sample use
The user supplied a popcorn narration export with segments and whitespace tokens. Use its shape and boundary cases as fixtures when implementation starts; do not depend on the user's Downloads path at runtime or claim alignment was checked without its matching audio.
