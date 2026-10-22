---
id: T3
title: red-guard runs the check in the checkout the commit lands in
blocked_by: [T2]
files:
  [hooks/scripts/_common.py, hooks/scripts/red_guard.py, tests/test_hooks.py]
proves: "in tests/test_hooks.py, with a linked worktree whose feedback command exits 1 and a main checkout whose feedback command exits 0, a `git commit` event with `cwd` set to the worktree exits 2, and so do `git -C <worktree> commit` and `cd <worktree> && git commit` from the main checkout"
status: todo
---

## Context

Spec requirement 2. Plan approach step 3, the riskiest step.

Add `commit_checkout(event, command) -> Path` to `hooks/scripts/_common.py`. The directory is, in order: the argument of `-C` in the `git ... commit` invocation; the directory of a leading `cd <dir> &&` (the first command in the string); the event's `cwd` field; `CLAUDE_PROJECT_DIR`; the process cwd. A relative directory resolves against the event's `cwd`. Then `git rev-parse --show-toplevel` in that directory gives the checkout; when git fails, use the directory itself. Parse only those two leading forms; anything else falls back to `cwd`, which the probe of 2026-10-22 showed is the shell's real directory after an earlier `cd`.

`red_guard.py` then reads `.claude/toolkit.json`, the pending changes, and runs the feedback command, all in that checkout. The existing hooks stay on `project_dir()`: moving them is change 0003.

A linked worktree in a test: `git worktree add <path> -b <branch>` from the temporary repo, with a different `.claude/toolkit.json` written into each checkout so the test can tell which one ran.

Seam: the hook script as a subprocess, `tests/test_hooks.py`. `run_hook` sets `CLAUDE_PROJECT_DIR` to the main checkout, which is what makes the test meaningful.

## Acceptance

- The proving test passes.
- An event with no `cwd` falls back to `CLAUDE_PROJECT_DIR`, so the T1 and T2 tests still pass unchanged.
- `python3 -m unittest discover -s tests` passes.

## Evidence
