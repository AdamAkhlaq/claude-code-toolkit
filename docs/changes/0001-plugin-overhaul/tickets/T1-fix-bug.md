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
    tests/test_components.py,
  ]
proves: "tests/test_components.py passes with the README skill table listing fix-bug as shipped in 0.3.0"
status: done
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

### Evidence 2026-10-22 17:25

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.298s

OK
```

Before `skills/fix-bug/SKILL.md` existed, with the README row already at 0.3.0, `tests.test_components` failed with `AssertionError: 'fix-bug' not found in [...]: README lists fix-bug as shipped but skills/fix-bug/SKILL.md is missing`.

### Verifier 2026-10-22 17:26

Verdict: pass

Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok (`tests/test_components.py` checks the README skill table against `skills/*/SKILL.md`; on a scratch copy of HEAD without `skills/fix-bug` it fails with `README lists fix-bug as shipped but skills/fix-bug/SKILL.md is missing`, exit 1)
3. proving test run: 0, `Ran 10 tests in 0.009s` / `OK` (`python3 -m unittest tests.test_components`)
4. feedback command: 0, `Ran 46 tests in 1.297s` / `OK` (`python3 -m unittest discover -s tests`)
5. acceptance: 4 of 4 checked, none failed (proving test passes; `skills/fix-bug/SKILL.md` has `disable-model-invocation: true`, `argument-hint` and reads `$ARGUMENTS` as the report; steps 3, 7, 9 and the Rules use `toolkit:grilling`, `toolkit:verify`, create and remove `.claude/.tests-locked` and forbid test edits under the lock; PHILOSOPHY "Reproduce before fixing" links `./skills/fix-bug/SKILL.md`, the guide table routes bugs to `/toolkit:fix-bug`, `GLOSSARY.md` defines Reproduction, Regression test and Test lock)
6. scope: ok (branch touches only listed files plus the ticket)
7. tests intact: ok (only change to `tests/test_components.py` is `assertIn(name, sorted(skills()))` for a readable failure message; no assertion removed, skipped or loosened)
