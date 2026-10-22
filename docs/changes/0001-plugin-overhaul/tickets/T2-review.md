---
id: T2
title: Add the reviewer agent and the review skill over REVIEW.md
blocked_by: [T1]
files:
  [
    agents/reviewer.md,
    skills/review/SKILL.md,
    templates/REVIEW.md,
    README.md,
    PHILOSOPHY.md,
    GLOSSARY.md,
    skills/guide/SKILL.md,
    tests/test_components.py,
  ]
proves: "tests/test_components.py passes with the README listing review as shipped in 0.3.0 and the reviewer agent carrying a read-only tool allowlist"
status: in-progress
executed_by: single
branch: ticket/0001-T2
---

## Context

Spec: `review` runs "three `REVIEW.md` passes, findings in `review.md` and on the PR"; `reviewer` "executes one `REVIEW.md` pass". Philosophy "Verification is independent" and "Mistakes become memory": each pass runs in its own reviewer context, findings are Important or Nit (glossary), nits are capped at five, every Important finding is fixed or waived by the code owner before merge, and a flag raised in two reviews becomes a `CLAUDE.md` line through the `claude-md` discipline. The skill reads the repo's `REVIEW.md`, falling back to the template when absent, writes `review.md` in the change folder, and posts findings to the pull request when one exists so that `pr-sweep` can resolve them.

Seam: `tests/test_components.py`. Extend it so the reviewer agent, like the researcher, carries no editing tools.

## Acceptance

- The proving test passes.
- `agents/reviewer.md` has a tool allowlist without Edit, Write or Agent, and the test asserts it.
- `skills/review/SKILL.md` is user-invoked, runs one reviewer per pass in `REVIEW.md`, merges findings into `docs/changes/<change>/review.md`, and records waivers with the waiver's owner.
- `templates/REVIEW.md` states the finding format the reviewer returns.
- PHILOSOPHY "Verification is independent" links `review` and `reviewer`; the guide routes a finished change to `review`.

## Evidence

### Evidence 2026-10-22 17:27

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.296s

OK
```

Before `agents/reviewer.md` and `skills/review/SKILL.md` existed, with the README row at 0.3.0 and the read-only assertion extended to the reviewer, `tests.test_components` failed with `KeyError: 'reviewer'` and `AssertionError: 'review' not found in [...]`.
