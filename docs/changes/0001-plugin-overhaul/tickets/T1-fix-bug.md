---
id: T1
title: Add the fix-bug skill with the test lock flow
blocked_by: []
files:
  [
    skills/fix-bug/SKILL.md,
    README.md,
    PHILOSOPHY.md,
    GLOSSARY.md,
    skills/guide/SKILL.md,
  ]
proves: "tests/test_components.py passes with the README skill table listing fix-bug as shipped in 0.3.0"
status: in-progress
executed_by: single
branch: ticket/0001-T1
---

## Context

Spec component table, row `fix-bug`: "Reproduction as reported, minimised failing test, locked fix". Philosophy "Reproduce before fixing" and "Seams before tests, tests before code": reproduce the bug the way the user hit it, narrow to the fastest test at the nearest seam that fails for the same reason, commit that test, create `.claude/.tests-locked` so the `lock-tests` hook blocks test edits, fix, verify, unlock. A bug fix is a change: the skill allocates a change folder with an `intent.md` whose origin is the report and a one-ticket graph whose `proves` is the regression test, so the fix passes through the same hooks and leaves the same artifacts as any other work. Spec and plan are not required for a bug fix.

Seam: `tests/test_components.py`, which checks the README table against the skills on disk, the invocation flag, and the PHILOSOPHY links. The ticket is done when the table row says `0.3.0` and the test suite is green.

## Acceptance

- The proving test passes.
- `skills/fix-bug/SKILL.md` is user-invoked and takes the bug report as its argument.
- The skill uses the `toolkit:verify` and `toolkit:grilling` disciplines and the `lock-tests` marker, and never edits a test after the lock.
- PHILOSOPHY "Reproduce before fixing" links the skill. The guide routes bugs to it. `GLOSSARY.md` defines test lock and regression test.

## Evidence
