---
name: vidkit-pipeline
description: Coordinate Vidkit research, script, creative brief, concept approval, ElevenLabs narration, timed storyboard, preview QA, and export. Use for multi-stage requests and resuming jobs.
---
# Vidkit pipeline

Read [handoff contract](references/handoff-contract.md) and [CLI workflow](references/cli-workflow.md). Use `vidkit doctor`, `vidkit show <job-id>`, and `vidkit next <job-id> --language <language> --json` before acting. Existing v2 jobs keep their workflow; new jobs use v3. Do not edit SQLite or assume a missing stage is complete.

For each language, follow: research → script → creative brief with theme, hook, visual strategy, sourced assets and three frame previews → concept approval in review mode → final Eleven v3 narration → ElevenLabs STT word-level transcript → assets and caption plan → storyboard and motion → preview MP4 → QA report → export approval in review mode → render. Use `vidkit next` after every handoff.

In review mode, “continue” means continue non-gated preparation only. Require explicit `vidkit approve ... concept` and `vidkit approve ... export` for the current revisions. In automatic mode, skip waits for video approval but never ignore validation failures; candidate library entries remain candidates. Do not promote a library candidate while approving a video unless the user separately chooses to do so.

Search and preview the library before proposing new components. If a product screenshot is inaccessible, continue with sourced official artwork, an API example, chart or explanatory diagram. Label the evidence type and limitations accurately in brief and QA. Do not invent UI screenshots or logos.

Research and editorial work are agent tasks imported through the CLI. TTS and STT are paid API steps; do not send requests speculatively or repeat an uncertain result. No embedded LLM API, scheduler, automatic publishing, music beat detector, or budget guard exists.

Route to [research](../vidkit-research/SKILL.md), [script](../vidkit-script/SKILL.md), [voice](../vidkit-voice/SKILL.md), [transcript](../vidkit-transcript/SKILL.md), [storyboard](../vidkit-storyboard/SKILL.md), [render](../vidkit-render/SKILL.md), and [publish](../vidkit-publish/SKILL.md) only as needed. Report actual artifact paths, revisions and unperformed QA checks.
