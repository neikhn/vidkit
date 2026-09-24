---
name: vidkit-render
description: Specify or execute available Remotion rendering for Vidkit timelines and validate portrait video, audio and captions. Use for preview/export requests; does not imply a renderer is installed.
---
# Render

## Input and output
Input: checked timeline, final narration, approved assets and available template/runtime.
Output: render specification or actual preview, MP4 and SRT/VTT, clearly distinguished.
Read the [handoff contract](../vidkit-pipeline/references/handoff-contract.md).

## Workflow
1. Verify upstream revisions and unresolved findings before claiming readiness.
2. Confirm renderer, templates, fonts and assets exist. If not, deliver an implementation-ready render brief and list dependencies; do not build software unless requested.
3. Specify Remotion with 1080×1920, 30 fps, H.264 video and AAC audio by default. Derive duration from actual narration/timeline.
4. Use checked templates populated with content. New template code requires review before automatic production use.
5. When execution is available and authorized, render a preview and inspect scene transitions, text fitting, Vietnamese glyphs, subtitle sync and mobile safe areas. Listen for clipping, missing speech and music masking.
6. Export only after checks pass; retain actual inputs, versions and findings.
7. Use `vidkit studio` for review. Use `vidkit render` for a tracked export, or `vidkit import-render` to register a Studio export against the current timeline revision.

## Completion and missing inputs
A technical export success is not visual/audio approval. Unperformed checks remain unperformed. If narration changes, return to transcript and rebuild dependent timing. If only visuals change, reuse matching audio/transcript.

The repository includes a Remotion composition with bundled Noto Sans, screenshot layouts and Python preview/render helpers. Run `vidkit doctor` before execution; visual and audio inspection remain explicit checks.
