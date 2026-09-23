# Eleven v3 preparation
Verified: 2026-09-24.
Official source: [Prompting Eleven v3](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#prompting-eleven-v3).
This is a focused working reference, not a copy of the vendor manual. Recheck current documentation when API compatibility or voice behavior changes.

## Documented behavior
Eleven v3 uses voice choice, punctuation, text structure and audio tags to influence delivery. Tags depend on the selected voice and are not exact timing commands. SSML break tags are unsupported. Natural balances delivery; Creative increases expressiveness and hallucination risk; Robust is less responsive to direction. Emphasis may be influenced by capitalization. Preserve spoken content when adding expression.

## Vidkit defaults
- Model: eleven_v3. Delivery: clear with selected emphasis; start with Natural.
- Use a configured voice suitable for each language. Test pronunciation and tone on a short representative sample during voice setup.
- Prefer ordinary sentence rhythm. Add tags only when they improve a particular line; do not tag every sentence.
- Keep emotion believable for an explainer. Do not add laughter, sighs, singing or environmental sound effects by default.
- Expand spoken numbers/abbreviations before expression enhancement. Preserve a mapping to clean display text and expected spoken text.
- Keep camera directions, source links and scene notes outside the TTS input.
- Tags are directions, not subtitle text or guaranteed pauses.
- The selected workflow transcribes the final narration using STT regardless of whether the TTS provider could also supply alignment.

## Preparation example
Editorial: “This tool costs twenty dollars per month. But there is a limit.”
TTS input: “[curious] This tool costs twenty dollars per month. But… there is a limit.”
Display treatment: “$20/month” anchored to the spoken price phrase.

This illustrates optional delivery direction, not a required tag pattern. Do not add a claim or change certainty while making a line expressive.
