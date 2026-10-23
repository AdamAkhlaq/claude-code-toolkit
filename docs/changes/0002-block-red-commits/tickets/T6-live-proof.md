---
id: T6
title: red-guard holds in a real Claude Code session
blocked_by: [T5]
files: [hooks/scripts/red_guard.py, hooks/hooks.json, tests/test_hooks.py]
proves: "with the plugin loaded from a clone in headless sessions against a temporary repo, a red source commit is blocked and the session reports the failing output (also under --permission-mode bypassPermissions), the same commit lands once green, a test-only red commit lands, `git add -A && git commit` on red is blocked, and a commit from a worktree under .claude/worktrees/ runs the feedback command there; the quoted transcripts are the evidence"
status: done
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

### Evidence 2026-10-22 19:45

Setup: the plugin cloned from `ticket/0002-T6` at `8bf024b` into the scratchpad, loaded with `~/.nvm/versions/node/v25.3.0/bin/claude --plugin-dir ../plugin -p` (Claude Code 2.1.304) from a throwaway repo beside it. The repo's `.claude/toolkit.json` is `{ "feedbackCommand": "python3 check.py", "testGlobs": ["tests/"] }`; `check.py` prints `check.py in <cwd>: <STATE>` and exits 1 when the ignored file `state` says `red`. Every prompt states the user approves the commit in this throwaway repo and asks for exactly one command, reported verbatim, with no alternatives. Below, `$E` stands for the scratchpad directory `/private/tmp/claude-501/-Users-adamakhlaq-code-claude-code-toolkit/96c2cbd6-347d-462f-9e1a-e69bd22e6dcc/scratchpad/e2e`. Outcomes are confirmed with `git log`, not only the session's words.

Run 1, red, `app.py` staged, default permission mode, `--allowedTools "Bash(git commit *)"`, `git commit -m run1`:

```
PreToolUse:Bash hook error: [python3 "$E/plugin/hooks/scripts/red_guard.py"]: Commit stopped: the feedback command is red.
Command: python3 check.py
Exit code: 1
Last 1 line of output:
check.py in $E/repo: RED
Fix the code and commit again. Never edit a test to reach green.

This hook comes from the toolkit@inline plugin.
```

`git log --oneline`: `bdf7cef init` only. `app.py` still staged.

Run 2, the same under `--permission-mode bypassPermissions`, `git commit -m run2`: the identical block message, and `git log` still `bdf7cef init` only.

Run 3, the same staged change with `state` green, `git commit -m run3`:

```
[master 4816dc0] run3
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Run 4, red again, only `tests/test_x.py` (a failing test) staged, `git commit -m run4`:

```
[master 067d6ff] run4
 1 file changed, 2 insertions(+)
 create mode 100644 tests/test_x.py
```

Run 5, red, `app.py` modified and unstaged, one command `git add -A && git commit -m run5` with `--allowedTools "Bash(git add *)" "Bash(git commit *)"`: the same block message as run 1; `git log` head still `067d6ff run4`, and `git status --short` shows ` M app.py`, nothing staged, so the whole command was stopped before its `git add` ran. This also shows the entry's `if: "Bash(git *)"` matches a compound command.

Run 6, `git worktree add .claude/worktrees/w1 -b w1` (excluded through `.git/info/exclude`), `state` red in the worktree and green in the main checkout, `app.py` modified in the worktree, `--permission-mode bypassPermissions`, two separate Bash calls `cd .claude/worktrees/w1` then `git commit -am run6`:

```
PreToolUse:Bash hook error: [python3 "$E/plugin/hooks/scripts/red_guard.py"]: Commit stopped: the feedback command is red.
Command: python3 check.py
Exit code: 1
Last 1 line of output:
check.py in $E/repo/.claude/worktrees/w1: RED
Fix the code and commit again. Never edit a test to reach green.

This hook comes from the toolkit@inline plugin.
```

The feedback command ran in the worktree. The worktree's `git log` head is still `067d6ff run4`; `python3 check.py` in the main checkout prints `GREEN` and exits 0, so a hook reading `CLAUDE_PROJECT_DIR` would have let this commit through.

Gap found: nothing in the unit tests pinned the hook entry itself. Removing `onFailure`, the `if` filter, or setting `timeout` at or below the script's 570-second limit would have reopened the gate without a red test. Added `test_hook_entry_fails_closed_and_outlasts_the_feedback_limit`: it passes, and with `timeout` temporarily set to 500 it failed with `AssertionError: 500 not greater than 570` (restored; `git diff hooks/hooks.json` empty). No fix to the script or the entry was needed. Nothing in the real repository was committed by the sessions.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
----------------------------------------------------------------------
Ran 61 tests in 3.941s

OK
```

### Verifier 2026-10-22 19:48

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. The live proof was reproduced in a fresh clone of `ticket/0002-T6` at `78862c8` and a fresh throwaway repo under the scratchpad's `verify-t6/` (Claude Code 2.1.304, `--plugin-dir <clone> -p`, `< /dev/null`, `check.py` printing `verify-check in <cwd>: <STATE>`). Run 1 (red, `app.py` staged, `--allowedTools "Bash(git commit *)"`): `Commit stopped: the feedback command is red.` with `Command: python3 check.py`, `Exit code: 1`, `verify-check in .../verify-t6/repo: RED`; `git log --oneline`: `f4aa750 init` only, `M  app.py` still staged. Run 2 (same, `--permission-mode bypassPermissions`): identical block, `git log` still `f4aa750 init`. Run 3 (green): `[master 695948b] v3`. Run 4 (red, only `tests/test_x.py` staged, `python3 check.py` exits 1): `[master bf0c6c9] v4`. Run 5 (red, `git add -A && git commit -m v5` in one call): the same block; `git log` head `bf0c6c9 v4`, `git status --short` ` M app.py`, nothing staged. Run 6 (`.claude/worktrees/w1` red, main checkout green and exiting 0, bypassPermissions, `cd .claude/worktrees/w1` then `git commit -am v6` as two calls): block reading `verify-check in .../verify-t6/repo/.claude/worktrees/w1: RED`; worktree `git log` head `bf0c6c9 v4`, ` M app.py`. The new unit test fails when the entry is weakened in the clone: `timeout` 500 gives `AssertionError: 500 not greater than 570`, removing `onFailure` gives `AssertionError: None != 'block'`.
3. proving test run: 0, `test_hook_entry_fails_closed_and_outlasts_the_feedback_limit` `Ran 1 test ... OK`
4. feedback command: 0, `Ran 61 tests in 3.912s` `OK`
5. acceptance: 3 of 3 checked. Transcripts and `git log` lines quoted for all six runs in the executor's evidence and reproduced above; the gap (the hook entry unpinned) has a unit test; `python3 -m unittest discover -s tests` exits 0.
6. scope: ok (`tests/test_hooks.py` and the ticket file only)
7. tests intact: ok (one test added, nothing removed or loosened)
