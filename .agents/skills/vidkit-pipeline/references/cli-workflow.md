# Vidkit CLI workflow

Runtime contract version: 2. Workspace paths are relative to `workspace/`. Inspect state with `vidkit show <job-id>` and choose the next action with `vidkit next <job-id> --language vi --json`.

## Agent handoffs

1. Create a job with `vidkit create "Title" --languages vi,en --source-url <url>`.
2. Import research with `vidkit add-source <job-id> source-pack.json`.
3. Import localized scripts, then generate the configured narration and transcript.
4. Generate final narration and word-level transcript.
5. Add local images with `vidkit add-asset`. Record `assetId` values.
6. Write one storyboard per language using normalized transcript word indexes.
7. Run `vidkit timeline`, `vidkit studio`, revise, then `vidkit render` when the review version is ready.

Use `vidkit timeline --draft` only for a technical pipeline test. Its evenly divided scenes are not editorial output.

## Source pack

The top-level object requires a non-empty `claims` list. Each claim requires `id`, `statement`, `sourceUrl`, `publishedAt`, `retrievedAt` and `uncertainty`; use `null` for an unavailable publication date or uncertainty only when the absence itself is explicit. IDs must be unique. Store visual candidates separately from selected local assets.

```json
{
  "claims": [
    {
      "id": "claim-1",
      "statement": "The product supports feature X.",
      "sourceUrl": "https://example.com/docs",
      "publishedAt": null,
      "retrievedAt": "2026-09-24",
      "uncertainty": "Official documentation; availability may vary by plan."
    }
  ],
  "visualCandidates": []
}
```

## Asset command

```powershell
vidkit add-asset <job-id> screenshot.png `
  --description "Dashboard showing the editor" `
  --usage-basis "official product media" `
  --source-url "https://example.com/product"
```

The command validates PNG/JPEG/WebP dimensions, copies the file into the job, calculates a checksum and returns the `assetId`.

## Storyboard schema

```json
{
  "schemaVersion": 1,
  "language": "vi",
  "scenes": [
    {
      "id": "hook",
      "purpose": "Establish the promise",
      "layout": "hook",
      "title": "Một cách dựng video nhanh hơn",
      "body": "",
      "startAnchor": {"wordIndex": 0, "text": "Bạn"},
      "endAnchor": {"wordIndex": 11, "text": "không?"}
    },
    {
      "id": "demo",
      "purpose": "Show the actual interface",
      "layout": "screenshot",
      "title": "Chọn mẫu và nhập nội dung",
      "body": "",
      "assetId": "dashboard-1234abcd",
      "assetRequired": true,
      "crop": {"x": 0.05, "y": 0.1, "width": 0.8, "height": 0.7},
      "callout": {"text": "Bắt đầu tại đây", "x": 0.12, "y": 0.78},
      "startAnchor": {"wordIndex": 12, "text": "Đầu"},
      "endAnchor": {"wordIndex": 30, "text": "video."}
    }
  ]
}
```

Allowed layouts are `hook`, `screenshot`, `steps` and `takeaway`. Scene word ranges must partition the complete transcript: first index `0`, no overlap/gaps, and the final index equals the last word. Crop coordinates are normalized from 0 to 1. Python validates anchor text and derives all timing.

## Review boundaries

Studio may show placeholders for missing required images. `vidkit render` blocks those timelines. In automatic mode, export also blocks until timeline status is checked or approved. A successful encode remains `needs-review` until the actual MP4 is inspected.
