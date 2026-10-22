---
id: T6
title: red-guard holds in a real Claude Code session
blocked_by: [T5]
files: [hooks/scripts/red_guard.py, hooks/hooks.json, tests/test_hooks.py]
proves: "with the plugin loaded from a clone in headless sessions against a temporary repo, a red source commit is blocked and the session reports the failing output (also under --permission-mode bypassPermissions), the same commit lands once green, a test-only red commit lands, `git add -A && git commit` on red is blocked, and a commit from a worktree under .claude/worktrees/ runs the feedback command there; the quoted transcripts are the evidence"
status: in-progress
executed_by: single
branch: ticket/0002-T6
---

## Context

Spec requirement 13, and the live half of 10 (`if` and `onFailure` honoured from a plugin's `hooks.json`). Plan approach step 6. Same method as 0001-T9.

Clone this branch into the scratchpad and load the plugin with `~/.nvm/versions/node/v25.3.0/bin/claude --plugin-dir <clone> -p "<prompt>"`, run from a separate temporary git repo with a `.claude/toolkit.json` whose `feedbackCommand` is `python3 check.py`, `testGlobs` `["tests/"]`, and a `check.py` that exits 0 or 1 depending on a file the run flips. Prompts tell Claude to run exactly one command and report verbatim without alternatives, and state that the user approves the commit in this throwaway repo (the maintainer's global `CLAUDE.md` otherwise makes Claude decline). Allow only the Bash commands each run needs, or use `--permission-mode bypassPermissions` for that run. Confirm each outcome with `git log` in the temporary repo, not only the session's words.

The five runs: red source commit blocked; the same under bypassPermissions; green lands; only `tests/test_x.py` staged on red lands; `git add -A && git commit` on red blocked. Then a worktree run: `git worktree add .claude/worktrees/w1`, make only the worktree red, have the session `cd` into it in one call and commit in the next, and show the block came from the worktree's feedback command.

Anything the runs show that the unit tests did not cover gets a unit test in `tests/test_hooks.py`; a fix to the script or the entry, if one is needed, belongs here too. Nothing in the real repository is committed by the sessions.

Seam: a headless Claude Code session, the plan's one slow seam.

## Acceptance

- Every run's transcript and `git log` line is quoted in Evidence.
- Any gap found has a unit test, or Evidence says none was found.
- `python3 -m unittest discover -s tests` passes.

## Evidence
