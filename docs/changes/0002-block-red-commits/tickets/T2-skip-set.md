---
id: T2
title: Commits that change only workflow documents and tests skip the check
blocked_by: [T1]
files: [hooks/scripts/red_guard.py, tests/test_hooks.py]
proves: "in tests/test_hooks.py, with a feedback command that exits 1, a `git commit` whose pending changes are only a file under docs/, GLOSSARY.md and a file matching testGlobs exits 0 without running the feedback command, and adding one untracked source file makes it exit 2"
status: in-progress
executed_by: single
branch: ticket/0002-T2
---

## Context

Spec requirements 4 and 5. Plan approach step 2. Glossary: workflow document.

The pending changes are every path `git status --porcelain -z` reports in the checkout: staged, unstaged, and untracked files that are not ignored. Use `-z` so paths with spaces arrive intact, and take the destination of a rename. They are read this way, not from the index, because in `git add -A && git commit` the hook fires before `git add` runs.

The feedback command runs only when at least one pending path is neither a workflow document (under `docs/`, or `GLOSSARY.md` or `REVIEW.md` at the checkout root) nor a test file (matches `testGlobs` through `_common.first_match`, the same glob rules as `lock-tests`). No pending changes at all also skips: there is nothing to commit, and git will say so.

This is what lets `fix-bug` commit its failing regression test, and the verifier commit a reopen verdict on a red tree.

Seam: the hook script as a subprocess, `tests/test_hooks.py`.

## Acceptance

- The proving test passes.
- An unstaged modification to a tracked source file counts as a source change, as does a staged one.
- A path with a space in it is classified correctly.
- `python3 -m unittest discover -s tests` passes.

## Evidence

### Evidence 2026-10-22 19:36

Failing first: `test_only_workflow_documents_and_tests_skip_the_check` failed with `(2, '', 'Commit stopped: the feedback comm...') != (0, '', '')`, the docs-and-tests commit being blocked because the skip set did not exist. `test_paths_with_spaces_and_nested_workflow_names_are_classified` failed the same way on its first assertion.

Added `pending_paths` (`git status --porcelain -z --untracked-files=all`) and `needs_check` to `hooks/scripts/red_guard.py`. One departure from the Context, in favour of spec requirement 4 ("every path `git status --porcelain` reports"): both sides of a rename count, not only the destination, because moving a source file into `docs/` removes it from the product; pinned by `test_renaming_source_into_docs_still_runs_the_check`. If `git status` fails the check runs, so an unreadable state never opens the gate. Workflow documents are `docs/...` and `GLOSSARY.md`, `REVIEW.md` at the root only; `lib/GLOSSARY.md` is source. Also fixed the verifier's T1 note: one line of output now reads "Last 1 line of output".

Proving test: `tests.test_hooks.RedGuardTests.test_only_workflow_documents_and_tests_skip_the_check`. Acceptance tests beside it: `test_staged_and_unstaged_source_changes_both_count`, `test_paths_with_spaces_and_nested_workflow_names_are_classified`, `test_renaming_source_into_docs_still_runs_the_check`. The T1 tests still pass unchanged: their uncommitted `.claude/toolkit.json` is itself a pending source change.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
----------------------------------------------------------------------
Ran 56 tests in 2.366s

OK
```
