# Handoff scenarios
Use these as manual behavioral walkthroughs when editing skills. Do not call paid APIs, upload media or generate a video merely to validate the instructions.

| Input / change | Expected routing and outcome | Incorrect outcome |
|---|---|---|
| Only a URL | Research retrieves evidence; script can proceed from supported claims; absent API tooling is reported | Treating a URL as verified evidence or claiming MP3 creation |
| Clean script, requesting Eleven v3 preparation | Voice prepares tagged input and spoken/display mappings; preserves meaning; missing voice ID blocks generation only | Rewriting claims, using SSML breaks, inventing a voice ID |
| MP3 and sample segments/words JSON | Transcript imports and preserves raw data; validates against that MP3 if accessible; skips redundant STT if valid | Charging for another transcription solely because a file uses export field names |
| Only the sample JSON | Inspect structure and prepare a provisional storyboard; audio correspondence remains unverified | Declaring synchronization verified without the audio |
| Audio changed after storyboard | Invalidate transcript, timed storyboard, captions, render and approval | Reusing old timestamps against new audio |
| Visual-only edit | Reuse audio/transcript; update timeline/render and approval | Regenerating TTS without a spoken-content change |
| Automatic with transcript mismatch | Mark needs-review, retain evidence and do not publish | Silently changing captions to conceal missing narration |
| Existing upload with uncertain response | Reconcile upload status using available tooling; otherwise block retry | Uploading a duplicate |
| Export segment ends with “The hard outer” | Reconstruct phrase across segments before scene/caption decisions | Splitting the idea just because an export segment ended |
| STT contains whitespace tokens | Preserve raw text, exclude whitespace from highlight events | Animating whitespace as spoken words |

Passing a walkthrough shows instruction coverage, not proven runtime behavior. Record separately any checks that require future technical implementation.
