---
name: vidkit-publish
description: Prepare Vidkit YouTube metadata, enforce review or authorized automatic publication, reconcile upload state and interpret Shorts performance. Use after rendering or for publication-package preparation.
---
# Publish

## Input and output
Input: exact render revision, source pack, localized metadata, check results, destination and publishing mode.
Output: prepared publication package or verified publication record under the [contract](../vidkit-pipeline/references/handoff-contract.md).

## Workflow
1. Write faithful localized titles/descriptions and include supporting source links. Avoid strengthening claims for a hook.
2. Verify content, asset, transcript and render checks. Apply current platform disclosure/metadata requirements where relevant.
3. Review mode: require approval for the exact package. Automatic mode: require configured destination and user authorization; unresolved findings go to review.
4. Check uploader availability and account/project eligibility. When supported and authorized, upload privately, verify processing, then publish/schedule as requested.
5. Save upload ID and actual visibility. Reconcile uncertain responses before retrying; never assume a missing response means no upload exists.
6. Record performance at comparable ages, separated by language/topic/duration. Prefer engaged views, retention and subscriber outcomes over raw public views alone; use Studio where an API metric is unavailable.

## Completion and missing capabilities
Without an authorized uploader, complete metadata preparation only. Skills are not publishing authorization or a scheduler. Never mark a draft package as uploaded or published.

Check current [video API requirements](https://developers.google.com/youtube/v3/docs/videos) and [Shorts analytics](https://support.google.com/youtube/answer/12942217) before implementing or executing platform-specific behavior. Links reviewed 2026-09-24; account eligibility still requires verification. Original analysis is required regardless of reusable templates; no automated check guarantees monetization.
