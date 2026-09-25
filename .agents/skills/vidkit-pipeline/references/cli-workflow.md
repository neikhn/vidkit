# Vidkit CLI workflow

Runtime contract v3. Workspace paths are relative to `workspace/`. New jobs use v3; existing jobs remain v2. Run `vidkit next <job-id> --language vi --json` for the next missing or blocked stage. `vidkit show` lists revisions and checksums.

## Production sequence

```powershell
vidkit create "Product" --languages vi --mode review --source-url https://example.com
vidkit add-source <id> source-pack.json
vidkit add-script <id> vi script.json
vidkit add-brief <id> vi brief.json
vidkit approve <id> vi concept --reviewer "Name"
vidkit tts <id> vi
vidkit transcribe <id> vi
vidkit add-asset <id> official.png --type artwork --description "Product artwork" --usage-basis "official media" --source-url https://example.com/media
vidkit add-caption-plan <id> vi captions.json
vidkit add-storyboard <id> vi storyboard.json
vidkit timeline <id> vi
vidkit preview <id> vi
vidkit qa <id> vi
vidkit approve <id> vi export --reviewer "Name"
vidkit render <id> vi
```

Caption plan is optional; Python creates a semantic fallback. `tts` and `transcribe` call ElevenLabs and can incur cost. `studio` is interactive; `import-render` records its MP4 as a preview in v3. `timeline --draft` is only a technical test.

## Source and brief

Source pack has non-empty `claims` with unique `id`, `statement`, `sourceUrl`, `publishedAt` (nullable), `retrievedAt`, and `uncertainty` (nullable). Visual descriptions must be checked against the actual asset.

Creative brief example:

```json
{
  "angle": "Show the product decision path",
  "theme": "dark-grid",
  "hook": "What does the tool return?",
  "visualStrategy": "One API response and one diagram, each tied to a claim",
  "screenshotUnavailable": true,
  "screenshotAlternative": {
    "type": "api-example",
    "sourceUrl": "https://example.com/docs",
    "reason": "The console requires login"
  },
  "frames": {
    "hook": {"headline": "A useful product hook", "visualNote": "Brand name with generic explanatory graphic"},
    "evidence": {"headline": "The API response", "visualNote": "Enlarge the verified response fields"},
    "takeaway": {"headline": "The practical limit", "visualNote": "One conclusion with supporting source"}
  }
}
```

`add-brief` renders three 1080×1920 sample PNGs before audio. A frame may use `imagePath` instead of `visualNote`. The concept approval is tied to the current script and brief checksums. Changing either requires new concept approval before paid narration in review mode.

## Caption plan

```json
{
  "groups": [
    {"startWord": 0, "endWord": 5},
    {"startWord": 6, "endWord": 11}
  ]
}
```

Groups partition all normalized transcript words, with no gap, repeat or reordering. For condensed numeric display, a group may include `displayTokens`: `{"text":"$0.042","startWord":6,"endWord":11,"spokenText":"zero point zero four two dollars"}`. Exact transcript wording is validated.

## Storyboard

Use `schemaVersion: 3`, `language`, `theme`, and non-empty `scenes`. Each scene requires `id`, `layout`, `title`, `startAnchor.wordIndex`, and `endAnchor.wordIndex`. Word ranges partition the full transcript. Layouts: `brand-hook`, `screenshot-focus`, `api-response`, `diagram-flow`, `metric-breakdown`, `takeaway`. Optional fields: `component`, `componentVersion`, `purpose`, `body`, `claimIds`, `assetId`, `assetRequired`, `crop`, `callout`, and `motion.cues`.

```json
{
  "schemaVersion": 3,
  "language": "vi",
  "theme": "dark-grid",
  "scenes": [
    {
      "id": "hook",
      "layout": "brand-hook",
      "title": "Tên sản phẩm và lời hứa",
      "body": "Một vấn đề rõ ràng",
      "claimIds": ["claim-1"],
      "assetId": "official-artwork-12345678",
      "assetRequired": false,
      "startAnchor": {"wordIndex": 0},
      "endAnchor": {"wordIndex": 11},
      "motion": {"cues": [{"type": "zoom", "wordIndex": 5}]}
    }
  ]
}
```

The example shows one scene shape; a real storyboard must cover the last word. Crop is `{x,y,width,height}` normalized against the original image, with no region outside it. Python resolves all word anchors and motion cue timestamps. A referenced component/theme must exist in the library; candidate components are allowed in automatic jobs but not promoted by export.

## Library and QA

`vidkit library search/show/preview/add/approve` operates on manifests. After `library add`, run `library preview <candidate-id>` before using or approving it; a manifest or fixture edit requires another preview. A candidate component fixture must show its tested `baseComponent`; a candidate theme fixture must use the theme ID and exact style tokens. A novel React primitive requires implementation and tests. Approved entries and fixtures are Git-versioned under `renderer/library/`; candidates are under ignored `workspace/library/`.

`vidkit qa` writes a report with `automatic`, `mediaProbe`, `frameInspection`, `transitionReview`, `fullPlayback`, and `audioListening`. Each is `pass`, `fail`, or `not-run` with evidence. A review file passed to `vidkit qa <id> vi <file>` supplies the last four checks. An export approval is tied to the current timeline, preview and QA revisions. `render` in review mode requires that explicit approval. Automatic export still blocks on validation failure and never claims that unperformed viewing/listening occurred.
