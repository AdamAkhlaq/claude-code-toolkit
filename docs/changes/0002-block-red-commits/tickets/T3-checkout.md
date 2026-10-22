---
id: T3
title: red-guard runs the check in the checkout the commit lands in
blocked_by: [T2]
files:
  [hooks/scripts/_common.py, hooks/scripts/red_guard.py, tests/test_hooks.py]
proves: "in tests/test_hooks.py, with a linked worktree whose feedback command exits 1 and a main checkout whose feedback command exits 0, a `git commit` event with `cwd` set to the worktree exits 2, and so do `git -C <worktree> commit` and `cd <worktree> && git commit` from the main checkout"
status: in-progress
executed_by: single
branch: ticket/0002-T3
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

### Evidence 2026-10-22 19:38

Failing first: `test_checks_the_worktree_the_commit_lands_in` failed with `AssertionError: 0 != 2` on the event whose `cwd` is the worktree: the hook checked the main checkout, whose feedback command is green, instead of the worktree, whose feedback command is red.

Added `commit_checkout(event, command)` to `hooks/scripts/_common.py` and switched `red_guard.py` from `project_dir()` to it. The command is tokenised with `shlex` (falling back to whitespace on unbalanced quotes) so quoted directories survive; `~` is expanded. One refinement over the Context's "in order" list: a leading `cd <dir> &&` and a `git -C <dir>` on the commit compose, `cd` first, then each `-C` in turn, as the shell and git would apply them, instead of `-C` replacing `cd`. When `git rev-parse --show-toplevel` fails, including for a directory that does not exist, the directory itself is used. The existing hooks still use `project_dir()`; moving them is change 0003.

The test covers four forms against a linked worktree at `.claude/worktrees/w1` (excluded through `.git/info/exclude`, as `implement` does): event `cwd`, relative `git -C`, absolute `git -C`, and `cd <worktree> && git add -A && git commit`; plus the same commit with no `cwd`, which checks the green main checkout and exits 0. The T1 and T2 tests pass unchanged, their events carrying no `cwd`.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
----------------------------------------------------------------------
Ran 57 tests in 2.862s

OK
```
