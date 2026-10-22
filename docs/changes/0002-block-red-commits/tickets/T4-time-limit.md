---
id: T4
title: A feedback command that cannot finish is red, and faults never block other commands
blocked_by: [T3]
files: [hooks/scripts/red_guard.py, tests/test_hooks.py]
proves: "in tests/test_hooks.py, red_guard.run_feedback(command, cwd, limit=1) on a shell command that starts a child sleeping 30 seconds returns within 5 seconds reporting it timed out, and the child process is gone"
status: todo
---

## Context

Spec requirements 9, 10 and 11. Plan approach step 4.

`run_feedback(command, cwd, limit)` runs the command with `start_new_session=True` and, when `limit` seconds pass, kills the whole process group (`os.killpg`) and reports a timeout, so a hung `npm test` leaves no `node` child behind. Production calls it with `limit=570`, a module constant, under the hook's 600-second timeout so the block message is the hook's own. A timeout blocks the commit with a message that names the limit in seconds and says a feedback command that cannot finish is treated as red.

`main` catches any unexpected exception. If the command is not a `git commit`, or the event cannot be read, exit 0: a fault in the hook must never block an unrelated Bash call, because the entry has `onFailure: "block"`. If it is a commit, block with a one-line description of the error, which is what `onFailure` would do but readable.

Seam: the module imported directly in `tests/test_hooks.py` (add `SCRIPTS` to `sys.path`), for the time limit; the hook script as a subprocess for the fault cases. To check the child is gone, have the command write its child's pid to a file and probe it with `os.kill(pid, 0)` after the call returns.

## Acceptance

- The proving test passes.
- The function that builds the timeout block message names the limit; tested through the imported module.
- A `git commit` event in a repo whose `feedbackCommand` is not a string (for example `123`) exits 2 with a readable message, and a non-commit event with unreadable stdin exits 0.
- `python3 -m unittest discover -s tests` passes in about the same time as before.

## Evidence
