---
id: T5
title: Add the diagnose skill
blocked_by: [T4]
files:
  [skills/diagnose/SKILL.md, README.md, PHILOSOPHY.md, skills/guide/SKILL.md]
proves: "tests/test_components.py passes with the README skill table listing diagnose as shipped in 0.4.0"
status: todo
---

## Context

Spec component table, row `diagnose`: "Read-only diagnosis of a finding, written as a new `intent.md`". Philosophy "The loop closes": every finding from running software re-enters the workflow as an intent so it passes the same gates as any other change. The skill takes a finding (an alert, a log excerpt, a metric, a user complaint, a failing check in production), investigates without changing anything, using the `toolkit:researcher` agent for code and history, and ends by allocating a change and writing `intent.md` with the finding as origin, the diagnosis as problem, and the open questions tagged. It never fixes. If the finding is a reproducible bug with a known route, it says so and hands to `/toolkit:fix-bug` instead.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/diagnose/SKILL.md` is user-invoked, takes the finding as its argument, and writes only under `docs/changes/`.
- PHILOSOPHY "The loop closes" links the skill. The guide routes a production finding to it.

## Evidence
