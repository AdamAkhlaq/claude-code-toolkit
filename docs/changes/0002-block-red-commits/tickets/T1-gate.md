---
id: T1
title: red-guard blocks a commit while the feedback command is red
blocked_by: []
files:
  [hooks/scripts/red_guard.py, hooks/hooks.json, README.md, tests/test_hooks.py]
proves: "in tests/test_hooks.py, a `git commit` event in a repo with a pending source change and a feedback command that exits 1 makes red_guard.py exit 2 with a message naming the command, its exit code and its output, and the same event with a feedback command that exits 0 makes it exit 0 with no output"
status: todo
---

## Context

Spec requirements 1, 3, 6, 7, 8 and 14, and the hook entry part of 10. Plan approach step 1.

Create `hooks/scripts/red_guard.py` following the shape of `secret_guard.py`: module docstring, imports from `_common` (`read_event`, `tool_input`, `is_git_commit`, `load_config`, `project_dir`, `git`, `block`), `main() -> int`, `sys.exit(main())`. In this ticket the checkout is `project_dir()`; T3 replaces that. Every commit with at least one pending change runs the check; T2 adds the skip set.

- Not a `git commit` (per `is_git_commit`): exit 0, no output, the feedback command never runs.
- No `.claude/toolkit.json`, or `feedbackCommand` missing or empty: exit 0, no output.
- Otherwise run `feedbackCommand` with `shell=True` from the checkout root, stdout and stderr combined.
- Exit 0: exit 0 with no output. Non-zero: `block()` with a message that says the commit was stopped because the feedback command is red, names the command and exit code, quotes at most the last 40 lines of output, and says to fix the code and commit again, never to edit a test to reach green.

Register it in `hooks/hooks.json` in the `Bash` PreToolUse group directly after `secret_guard.py`, with `"if": "Bash(git *)"`, `"timeout": 600`, `"onFailure": "block"`. Add a `red-guard` row to the README hooks table (fires before `git commit`, config keys `feedbackCommand`, `testGlobs`), because `test_every_hook_script_is_registered_and_documented` requires both.

Seam: the hook script as a subprocess, `run_hook` and `HookCase` in `tests/test_hooks.py`. A feedback command such as `python3 -c "print('boom'); raise SystemExit(1)"` keeps the test fast and portable.

## Acceptance

- The proving test passes.
- A non-commit command and a repo without `.claude/toolkit.json` each exit 0 with no output and do not run the feedback command (a feedback command that writes a marker file shows it did not run).
- The block quotes no more than the last 40 lines of a longer output.
- `hooks/hooks.json` carries the entry with `if`, `timeout` and `onFailure` as above, and the README table has the row.
- `python3 -m unittest discover -s tests` passes.

## Evidence
