# Vidkit

Vidkit is a local-first workflow for producing short-form product videos with Python, ElevenLabs, and Remotion.

```text
source -> script -> Eleven v3 narration -> word-level transcript
       -> local assets -> storyboard -> preview -> export
```

Python manages project state and validates inputs. Agents research, write, select visuals, and prepare storyboards. Remotion previews and renders the validated timeline.

## Setup

Requirements: Python 3.11+, Node.js LTS, and npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

cd renderer
npm install
cd ..

vidkit init
vidkit doctor
```

Create `.env` from `.env.example`:

```dotenv
ELEVENLABS_API_KEY=your-key
VIDKIT_VOICE_VI=your-vietnamese-voice-id
VIDKIT_VOICE_EN=your-english-voice-id
```

## Agent workflow

Codex can run the complete workflow from the skills stored in `.agents/skills/`.

Example prompt:

> Use vidkit-pipeline to create a Vietnamese product video from this URL. Use real product screenshots and stop at the Remotion preview for review.

The agent should inspect the environment and job state first:

```powershell
vidkit doctor
vidkit list
vidkit next <job-id> --language vi --json
```

## CLI workflow

Create a video project:

```powershell
vidkit create "Product name" --languages vi --source-url https://example.com/product
```

The command returns a job ID. Use that ID for the remaining steps:

```powershell
vidkit add-source <job-id> .\source-pack.json
vidkit add-script <job-id> vi .\script-vi.json
vidkit tts <job-id> vi
vidkit transcribe <job-id> vi

vidkit add-asset <job-id> .\screenshot.png `
  --description "Product dashboard" `
  --usage-basis "official product media" `
  --source-url https://example.com/product

vidkit add-storyboard <job-id> vi .\storyboard-vi.json
vidkit timeline <job-id> vi
vidkit studio <job-id> vi
vidkit render <job-id> vi
```

`vidkit studio` opens the review preview. `vidkit render` writes the tracked MP4 to the video's `exports/` directory. If a video is exported manually from Remotion Studio, register it with:

```powershell
vidkit import-render <job-id> vi <path-to-mp4>
```

## Project management

Production data is stored under `workspace/`, which is excluded from Git. Each video has a readable directory name containing its creation date, title slug, and stable ID.

```powershell
vidkit list
vidkit show <job-id>
vidkit open <job-id>
vidkit rename <job-id> "New title"
vidkit next <job-id> --language vi --json
```

Changing visuals or the storyboard reuses existing narration and transcription. Replacing the audio invalidates the transcript, timeline, subtitles, and renders. Missing required images remain visible as placeholders in Studio and block final export.

## References

- Agent CLI contract and storyboard schema: `.agents/skills/vidkit-pipeline/references/cli-workflow.md`
- Antigravity usage: `docs/antigravity.md`
