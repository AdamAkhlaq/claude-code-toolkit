---
id: T2
title: Commits that change only workflow documents and tests skip the check
blocked_by: [T1]
files: [hooks/scripts/red_guard.py, tests/test_hooks.py]
proves: "in tests/test_hooks.py, with a feedback command that exits 1, a `git commit` whose pending changes are only a file under docs/, GLOSSARY.md and a file matching testGlobs exits 0 without running the feedback command, and adding one untracked source file makes it exit 2"
status: todo
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
