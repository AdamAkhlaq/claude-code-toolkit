---
id: T9
title: Exercise the deploy gate end to end
blocked_by: [T8]
files: [README.md, tests/test_hooks.py]
proves: "with the plugin loaded in a headless session in this repo, `git tag` is blocked by deploy-gate and the block names the authorisation route, and the same command passes with RELEASE_AUTHORIZED=1; the quoted transcripts are the evidence"
status: in-progress
executed_by: single
branch: ticket/0001-T9
---

## Context

Plan phase 3 step 2: "`deploy-gate` behaviour exercised end to end". The unit tests feed the hook JSON directly; this ticket proves the hook fires inside a real Claude Code session with the plugin loaded (`claude --plugin-dir . -p ...`) against this repo's own `.claude/toolkit.json`, whose `gatedCommands` include `^git tag `. Run both directions and quote the transcripts in the Evidence section. Use a tag name that does not exist and delete it afterwards if the authorised run creates it. Add a unit test for whatever the end-to-end run reveals that the unit tests did not cover; if nothing, add the test that pins the block message's wording about `RELEASE_AUTHORIZED`, which the README documents.

Seam: a headless session for the proof; `tests/test_hooks.py` for what it pins.

## Acceptance

- The proving transcripts are quoted in Evidence, one blocked, one authorised.
- The README's hook table and the deploy gate wording agree on the two authorisation routes.
- The test suite passes.

## Evidence

### Evidence 2026-10-22 17:51

End to end, in a clone of this repo at commit `6a65381` (the T8 state, same `.claude/toolkit.json` with `"gatedCommands": ["^git tag ", "^gh release "]`), with the plugin loaded from the clone and only `Bash(git tag *)` allowed, prompt: "Run exactly this shell command and report its result verbatim, do not try any alternative: git tag v9.9.9-gate-check".

Blocked direction, no authorisation, `claude --plugin-dir . --allowedTools "Bash(git tag *)" -p ...`:

```
PreToolUse:Bash hook error: [python3 ".../hooks/scripts/deploy_gate.py"]: Blocked: 'git tag v9.9.9-gate-check' matches gated command pattern '^git tag ' in .claude/toolkit.json. This is a one-way door and needs release authorisation from a human. After approving, they export RELEASE_AUTHORIZED=1 for the session or create .claude/.release-authorized. Prepare everything up to this step and stop.

This hook comes from the toolkit@inline plugin.
```

The session reported: "The command was blocked, so no tag was created." `git tag | grep gate-check` printed nothing.

Authorised direction, `RELEASE_AUTHORIZED=1 claude --plugin-dir . --allowedTools "Bash(git tag *)" -p ...`:

```
The command ran and printed nothing, which means it worked: git created the tag `v9.9.9-gate-check` on the current commit `6a65381` without any error. No hook stopped it.
```

`git tag | grep gate-check` printed `v9.9.9-gate-check`; the tag was then deleted from the clone. Nothing was tagged in the real repository.

The end-to-end run revealed nothing the unit tests missed, so the new unit test `test_block_names_both_authorisation_routes` pins the block message's wording about both routes and checks the README names the same two. It passed on first run: the behaviour already existed, which the ticket's context allows for this ticket. The README gained a paragraph under Hooks describing the two routes.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
...............................................
----------------------------------------------------------------------
Ran 47 tests in 1.384s

OK
```
