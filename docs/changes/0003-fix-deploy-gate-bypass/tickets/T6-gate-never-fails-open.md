---
id: T6
title: The gate never fails open on a long or nested call
blocked_by: [T5]
files:
  [
    hooks/scripts/deploy_gate.py,
    hooks/hooks.json,
    tests/test_hooks.py,
    README.md,
    CHANGELOG.md,
    docs/changes/0003-fix-deploy-gate-bypass/intent.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_gate_never_fails_open_on_a_long_or_nested_call: with gatedCommands ["^git tag ", "^git push .*--force"], deploy_gate.py exits 2 on `env git push origin` followed by 70 refs and `--force`, exits 2 within 5 seconds on 40 `eval` words before `git tag v1`, exits 2 with a message saying the call is too long to read on a call of 200000 words, and exits 0 silently within 5 seconds on `env git add` followed by 5000 paths; and the `deploy_gate.py` entry in hooks/hooks.json has a timeout and `"onFailure": "block"`'
status: in-progress
executed_by: single
branch: ticket/0003-T6
---

## Context

From the second review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-24 of a90e0c2"): Importants at `deploy_gate.py:49` (`WINDOW`) and `deploy_gate.py:54` (`eval` cost), the Decisions taken at that review, and the two `intent.md` wording Nits. Execution mode is `single`.

The decisions: the `WINDOW` goes, every line is matched whole, and the cost is bounded by a total budget, past which the call is blocked as unreadable; `eval` is re-read in linear time; `deploy-gate` gets an explicit timeout in `hooks/hooks.json` with `"onFailure": "block"`, as `red-guard` has, and the hook blocks on its own budget well before that timeout, so it never fails open.

Building a whole line from every program word is quadratic in the words of a simple command (5000 paths after `git add`: 361 MB). A linear way to keep every line whole: join each simple command once, with each program word's basename in place, record the offset where each program word starts, and for a pattern that starts with `^`, strip the `^` and use the compiled pattern's `match(line, offset)` at each offset, which anchors there; a pattern without a leading `^` is searched over the whole line and the raw command, as now. The budget is then a count of work, not time, so it is deterministic and testable: count the words read across all simple commands and every recursion into `eval`, `-c` scripts and substitutions, and block once it passes a limit well above any real call (200000 words is past it; 5000 paths after `git add` is not). For `eval`, re-read the words after the first `eval` in a simple command once and let that recursion handle any further `eval`, instead of recursing from every `eval` word.

The README's `deploy-gate` paragraph says a call too long to read is blocked. `intent.md`'s outcome says a quoted mention is not gated and an unquoted one is, on purpose, and its "this intent and its one ticket" becomes "its tickets".

Seam: the hook script as a subprocess, plus a test that reads `hooks/hooks.json`, as `RedGuardTests` pins `red-guard`'s entry. Write the proving test first and commit it failing before any code change.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged.
- The README's `deploy-gate` paragraph and `intent.md` say what the ticket's Context says.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry says it blocks a call too long to read and never fails open on a timeout.

## Evidence
