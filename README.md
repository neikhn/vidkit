# Vidkit

Vidkit produces short product explainers from researched sources. An agent handles editorial work; Python tracks revisions and validates handoffs; ElevenLabs supplies narration and word-level transcription; Remotion renders a 1080×1920 video.

## Setup

Requires Python 3.11+, Node.js, and npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
cd renderer
npm install
cd ..
vidkit doctor
```

Set `ELEVENLABS_API_KEY` and `VIDKIT_VOICE_VI` / `VIDKIT_VOICE_EN` in a local `.env`. Paid ElevenLabs calls occur only when you run `tts` or `transcribe`.

## Produce a video

Create a job. New jobs use workflow v3 and default to `review`; existing jobs keep their original workflow.

```powershell
vidkit create "Product name" --languages vi --source-url https://example.com
vidkit next <job-id> --language vi --json
```

Ask Codex or Antigravity to use `vidkit-pipeline` with the job ID. The agent researches claims, writes the script and creative brief, proposes a theme, and creates three concept frames before narration. If a product screenshot is unavailable, it may use sourced official artwork, an API example, or an explanatory diagram. The brief and QA must identify the substitute accurately.

```powershell
vidkit add-source <job-id> source-pack.json
vidkit add-script <job-id> vi script-vi.json
vidkit add-brief <job-id> vi brief-vi.json
vidkit approve <job-id> vi concept --reviewer "Your name"
vidkit tts <job-id> vi
vidkit transcribe <job-id> vi
vidkit add-asset <job-id> image.png --type artwork --description "Official product artwork" --usage-basis "official media" --source-url https://example.com/media
vidkit add-storyboard <job-id> vi storyboard-vi.json
vidkit timeline <job-id> vi
vidkit preview <job-id> vi
vidkit qa <job-id> vi
```

Inspect the MP4 in the video's `previews/` directory. The QA report distinguishes automated validation, media probing, frame inspection, transition review, full playback, and audio listening. Unperformed checks are marked `not-run`. To record inspection, supply a QA JSON file to `vidkit qa <job-id> vi qa-review.json` with `checks.frameInspection`, `checks.transitionReview`, `checks.fullPlayback`, and `checks.audioListening`; each has `status` (`pass`, `fail`, or `not-run`) and an `evidence` list. A passing check needs evidence.

```powershell
vidkit approve <job-id> vi export --reviewer "Your name"
vidkit render <job-id> vi
```

`render` writes the tracked MP4 to `exports/`. Approval is bound to the current script/brief or timeline/preview/QA checksum. A generic “continue” does not approve either gate. In `automatic` mode the video gates do not wait, but validation failures still block export, and new library candidates stay candidates. A successful encode alone does not mean full playback and audio have been reviewed.

## Captions and visuals

Captions use the final STT word timing. Automatic grouping considers pauses, punctuation, phrase endings and measured Noto Sans width. An optional `add-caption-plan` JSON selects explicit contiguous `startWord` / `endWord` groups. A group may include `displayTokens` with `text`, `startWord`, `endWord`, and exact `spokenText` to display a number or unit without losing its spoken-word mapping. The same cues feed burned-in captions and SRT/VTT.

The built-in themes are `dark-grid`, `dark-contours`, and `light-editorial`. Scene layouts are `brand-hook`, `screenshot-focus`, `api-response`, `diagram-flow`, `metric-breakdown`, and `takeaway`. Storyboard word anchors determine scene and motion timing; crop coordinates refer to the original image.

```powershell
vidkit library search "api" --kind component
vidkit library show api-response
vidkit library preview api-response
vidkit library search "bits" --kind bit
vidkit library preview bit-chat-conversation
vidkit library add candidate.json
vidkit library preview candidate-id
vidkit library approve candidate-id --reviewer "Your name"
```

Approved built-ins live in `renderer/library/`. Candidate manifests and assets live in the ignored `workspace/library/`. Candidate components are declarative variants of a tested base component; a new React primitive requires a code change and tests. Video approval and promotion to the shared library are separate choices.
The candidate fixture must exercise its base component. A theme fixture must include the candidate theme ID and its exact `themeData` tokens. Render `library preview` again after editing a candidate manifest or fixture.
`library approve` copies a checked component or theme manifest and fixture into `renderer/library/approved/`; no manual drag is needed. The command prints both destination paths. Shared image assets remain in `workspace/library/assets/` because their source and usage rights can be specific to a job. Commit the approved files if they should be shared through Git.

The library includes 23 requested [Remotion Bits](https://remotion-bits.dev/docs/getting-started/) examples in `renderer/library/bits.json`. `library preview <bit-id>` renders the original packaged example to `workspace/library/previews/`; `library show` gives its source path in the pinned package. They are marked `example` because their sample text, data, layout and aspect ratio need adaptation before production use. They cannot be selected directly as Vidkit storyboard components. The already integrated `AnimatedText`, `AnimatedCounter` and `GradientTransition` effects remain usable in Vidkit scenes. Provenance is recorded in [renderer/library/THIRD_PARTY.md](renderer/library/THIRD_PARTY.md).

## Find and resume work

```powershell
vidkit list
vidkit show <job-id>
vidkit open <job-id>
vidkit next <job-id> --language vi --json
```

Job files are under ignored `workspace/videos/<date>_<title>_<id>/`. Editing visuals or captions reuses matching narration and transcript. Replacing audio invalidates transcript-based timing. `vidkit studio` opens an interactive preview; a direct Studio export can be registered with `vidkit import-render`, which records it as a preview in v3 and does not grant approval.

Agent JSON contracts and examples: [.agents/skills/vidkit-pipeline/references/cli-workflow.md](.agents/skills/vidkit-pipeline/references/cli-workflow.md). Antigravity guidance: [docs/antigravity.md](docs/antigravity.md).
