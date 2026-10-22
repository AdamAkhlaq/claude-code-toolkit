---
id: T4
title: A feedback command that cannot finish is red, and faults never block other commands
blocked_by: [T3]
files: [hooks/scripts/red_guard.py, tests/test_hooks.py]
proves: "in tests/test_hooks.py, red_guard.run_feedback(command, cwd, limit=1) on a shell command that starts a child sleeping 30 seconds returns within 5 seconds reporting it timed out, and the child process is gone"
status: done
executed_by: single
branch: ticket/0002-T4
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

### Evidence 2026-10-22 19:41

Failing first: before any code, the proving test errored with `TypeError: run_feedback() takes 2 positional arguments but 3 were given`, the limit not existing. Because a signature error says nothing about the behaviour, the test was also run against a naive version, `subprocess.run(..., timeout=limit)` with the timeout caught, swapped in temporarily and then restored: it failed with `AssertionError: child 82095 outlived the feedback command's limit`, which is the hazard the ticket names. `test_a_fault_blocks_a_commit_readably_and_never_blocks_other_commands` failed with `AssertionError: 1 != 2`, a traceback and exit 1 on `feedbackCommand: 123`.

`run_feedback(command, cwd, limit)` now starts the shell with `start_new_session=True` and, past the limit, `os.killpg(..., SIGKILL)` on the group, collects what output there is, and returns `None` for the code. `guard` blocks a `None` with `timeout_reason`, which names `LIMIT_SECONDS` (570) and says a feedback command that cannot finish is treated as red. `main` is split into the commit test, where any exception exits 0, and `guard`, where any exception blocks with `red-guard could not check the commit (<type>: <message>)`. The hook entry's `timeout: 600` and `onFailure: "block"` were added in T1.

Proving test: `tests.test_hooks.RedGuardTests.test_feedback_past_the_limit_is_stopped_with_its_children`, through the imported module (returns in about a second, the backgrounded `sleep 30` is gone, and `timeout_reason` names "570 seconds"). Acceptance test: `test_a_fault_blocks_a_commit_readably_and_never_blocks_other_commands`. The suite went from 57 tests in 2.9 seconds to 59 in 3.9, the extra second being the limit test itself.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
----------------------------------------------------------------------
Ran 59 tests in 3.931s

OK
```

### Verifier 2026-10-22 19:42

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok, `test_feedback_past_the_limit_is_stopped_with_its_children` is new on this branch, imports `red_guard` directly (the plan's seam) and probes the backgrounded child with `os.kill(pid, 0)`; on a scratch copy with `start_new_session` removed and `killpg` replaced by `process.kill()` it fails with `AssertionError: 6.027073208002548 not less than 5`, and the fault test fails against the integration branch's `red_guard.py` with `AssertionError: 1 != 2`
3. proving test run: 0, `Ran 2 tests in 1.142s OK` (proving test and fault test)
4. feedback command: 0, `Ran 59 tests in 3.921s OK`
5. acceptance: 4 of 4 checked, none failed (proving test passes; `timeout_reason` asserted to contain "570 seconds" through the imported module; `feedbackCommand: 123` on a commit exits 2 with `Commit stopped: red-guard could not check the commit (TypeError: 'int' object is not iterable)...` and garbage stdin exits 0 with no output, run by hand and by the test; suite 3.9s against 2.7s for the base hook tests alone, the extra second being the 1-second limit test)
6. scope: ok
7. tests intact: ok, the test diff only adds two tests and an import
