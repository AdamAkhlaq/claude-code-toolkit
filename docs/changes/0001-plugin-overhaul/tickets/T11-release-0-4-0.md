---
id: T11
title: Release 0.4.0
blocked_by: [T10]
files:
  [
    .claude-plugin/plugin.json,
    CHANGELOG.md,
    README.md,
    docs/changes/0001-plugin-overhaul/spec.md,
    docs/changes/0001-plugin-overhaul/intent.md,
  ]
proves: "the plugin manifest says 0.4.0, CHANGELOG has a 0.4.0 section with today's date, no `planned` remains in the README, and the whole test suite and plugin validation pass"
status: in-progress
executed_by: single
branch: ticket/0001-T11
---

## Context

Repo `CLAUDE.md` release rules. This is the last phase of change 0001: after the release, the intent's status becomes `shipped` with a dated amendment, and the PHILOSOPHY "Enforced by" column must have no bare names left. The tag is the user's, after merge.

Seam: `python3 -m unittest discover -s tests` and `claude plugin validate .`.

## Acceptance

- The proving check passes.
- `intent.md` status is `shipped` with an amendment naming the four releases.
- Every component in PHILOSOPHY's "Enforced by" column is a link.

## Evidence
