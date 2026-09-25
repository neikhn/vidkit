---
name: vidkit-storyboard
description: Turn Vidkit scripts and word-level transcripts into meaning-driven scenes, caption groups, motion cues, and theme-locked timelines.
---
# Vidkit storyboard

Read [visual style](references/visual-style.md), [subtitle treatment](references/subtitles.md), and the [CLI workflow](../vidkit-pipeline/references/cli-workflow.md). Input: approved creative brief in review mode, final audio identity, normalized transcript, source claims, and asset inventory. Output: storyboard JSON and optional caption plan imported through the CLI.

Search `vidkit library search`, inspect `library show`, and render `library preview` before selecting a component. Choose one visual claim per scene. Use brand-hook, screenshot-focus, api-response, diagram-flow, metric-breakdown and takeaway as appropriate; avoid repeating one layout three times. A new candidate must have a fixture and tested base component. Render the candidate preview after the last manifest/fixture edit; a stale preview blocks use and approval. Preserve component ID/version/checksum and theme lock in the compiled timeline.

Scenes must partition transcript word indexes exactly. Copy anchor text; Python derives milliseconds. Motion cues use word indexes in their scene, never invented timestamps. Use source claim IDs, accurate asset IDs and crop coordinates from the original image. If no product screenshot exists, continue with a sourced substitute and call it by its true type.

Propose caption groups by meaning. Use contiguous word-index ranges; optional display tokens must cover every spoken word and carry exact spokenText. Let Python validate the plan and Noto Sans width. Keep captions to two lines, avoid orphan words and split boundaries at short connectors or between numbers and units. Subtitles and animated captions share timing; music beat analysis is outside this workflow.

Run `vidkit add-storyboard`, optional `vidkit add-caption-plan`, and `vidkit timeline`. If timing, assets, claims or library components fail validation, revise the inputs and compile again. Visual and caption edits retain unchanged audio/transcript; new audio invalidates both.

Remotion Bits: `vidkit library search bits --kind effect` lists the three integrated effects; `vidkit library search bits --kind bit` lists 23 upstream examples. Use `library preview <bit-id>` to render a gallery sample and `library show <bit-id>` to find its source in the pinned package. A `bit` entry is an example with sample data, not a storyboard component; adapt and test a parameterized wrapper before using it in a video. See renderer/library/THIRD_PARTY.md for provenance.
