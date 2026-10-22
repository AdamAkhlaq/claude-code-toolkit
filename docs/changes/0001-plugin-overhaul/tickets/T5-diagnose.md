---
id: T5
title: Add the diagnose skill
blocked_by: [T4]
files:
  [skills/diagnose/SKILL.md, README.md, PHILOSOPHY.md, skills/guide/SKILL.md]
proves: "tests/test_components.py passes with the README skill table listing diagnose as shipped in 0.4.0"
status: done
executed_by: single
branch: ticket/0001-T5
---

## Context

Spec component table, row `diagnose`: "Read-only diagnosis of a finding, written as a new `intent.md`". Philosophy "The loop closes": every finding from running software re-enters the workflow as an intent so it passes the same gates as any other change. The skill takes a finding (an alert, a log excerpt, a metric, a user complaint, a failing check in production), investigates without changing anything, using the `toolkit:researcher` agent for code and history, and ends by allocating a change and writing `intent.md` with the finding as origin, the diagnosis as problem, and the open questions tagged. It never fixes. If the finding is a reproducible bug with a known route, it says so and hands to `/toolkit:fix-bug` instead.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/diagnose/SKILL.md` is user-invoked, takes the finding as its argument, and writes only under `docs/changes/`.
- PHILOSOPHY "The loop closes" links the skill. The guide routes a production finding to it.

## Evidence

### Evidence 2026-10-22 17:43

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.310s

OK
```

Before `skills/diagnose/SKILL.md` existed, with the README row at 0.4.0, `tests.test_components` failed with `AssertionError: 'diagnose' not found in [...]`.

### Verifier 2026-10-22 18:05

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `tests/test_components.py` existed before the branch and is unchanged on it; `test_invocation_matches_readme` and `test_shipped_components_are_linked_not_just_named` fail in a copy of HEAD with `skills/diagnose` removed (`AssertionError: 'diagnose' not found in [...]`, `FAILED (failures=2)`), so the test guards both the README row and the PHILOSOPHY link.
3. proving test run: 0, `Ran 10 tests in 0.013s OK` (`python3 -m unittest tests.test_components`)
4. feedback command: 0, `Ran 46 tests in 1.507s OK` (`python3 -m unittest discover -s tests`)
5. acceptance: 3 of 3 checked, none failed. Proving test passes (check 3). `skills/diagnose/SKILL.md` carries `disable-model-invocation: true`, takes the finding through `$ARGUMENTS` with an `argument-hint`, and states in step 1 and in Rules that its only writes are under `docs/changes/`. PHILOSOPHY "The loop closes" links `./skills/diagnose/SKILL.md`; the guide table gained a row routing a finding from running software to `/toolkit:diagnose`. `claude plugin validate .` passes.
6. scope: ok. Branch touches PHILOSOPHY.md, README.md, skills/diagnose/SKILL.md, skills/guide/SKILL.md and the ticket file, all in `files` or exempt.
7. tests intact: ok, `git diff change/0001-phase-3...HEAD -- tests/` is empty.
