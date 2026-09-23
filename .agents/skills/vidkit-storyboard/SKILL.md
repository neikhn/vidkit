---
name: vidkit-storyboard
description: Turn Vidkit scripts and word-level transcripts into meaning-driven timed scenes, caption groups and animation cues. Use for narrative timing and subtitle design, not music beat detection.
---
# Storyboard

## Input and output
Input: script, source pack, checked transcript, final audio identity and asset inventory.
Output: timeline using the [contract](../vidkit-pipeline/references/handoff-contract.md).
Read [visual style](references/visual-style.md) for scene design and [subtitles](references/subtitles.md) for caption grouping.

## Workflow
1. Reconstruct complete narrative ideas across export segment boundaries.
2. Choose a scene for each useful explanatory beat; map it to actual word/phrase anchors and audio time.
3. Use keywords for reveals, counters or emphasis; change scenes at meaningful transitions rather than each word.
4. Select source footage and diagrams that actually support the claims. Label conceptual diagrams and avoid invented numerical histories.
5. Group readable captions from the same words; share timing with scene cues.
6. Make separate localized timelines. Research/assets can be shared, but narration duration and layout cannot be assumed identical.

## Completion and missing inputs
Complete when every timed scene/caption has valid anchors and necessary assets or explicitly unresolved dependencies. With only script, deliver an untimed storyboard; do not invent measured seconds. Missing assets or unchecked synchronization prevent a production-ready handoff.

Music beat analysis and vocal stress detection are separate capabilities outside v1. Word timing alone does not measure either.
