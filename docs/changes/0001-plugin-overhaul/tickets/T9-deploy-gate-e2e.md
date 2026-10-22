---
id: T9
title: Exercise the deploy gate end to end
blocked_by: [T8]
files: [README.md, tests/test_hooks.py]
proves: "with the plugin loaded in a headless session in this repo, `git tag` is blocked by deploy-gate and the block names the authorisation route, and the same command passes with RELEASE_AUTHORIZED=1; the quoted transcripts are the evidence"
status: todo
---

## Context

Plan phase 3 step 2: "`deploy-gate` behaviour exercised end to end". The unit tests feed the hook JSON directly; this ticket proves the hook fires inside a real Claude Code session with the plugin loaded (`claude --plugin-dir . -p ...`) against this repo's own `.claude/toolkit.json`, whose `gatedCommands` include `^git tag `. Run both directions and quote the transcripts in the Evidence section. Use a tag name that does not exist and delete it afterwards if the authorised run creates it. Add a unit test for whatever the end-to-end run reveals that the unit tests did not cover; if nothing, add the test that pins the block message's wording about `RELEASE_AUTHORIZED`, which the README documents.

Seam: a headless session for the proof; `tests/test_hooks.py` for what it pins.

## Acceptance

- The proving transcripts are quoted in Evidence, one blocked, one authorised.
- The README's hook table and the deploy gate wording agree on the two authorisation routes.
- The test suite passes.

## Evidence
