---
id: T4
title: Release 0.3.0
blocked_by: [T3]
files:
  [
    .claude-plugin/plugin.json,
    CHANGELOG.md,
    README.md,
    docs/changes/0001-plugin-overhaul/spec.md,
  ]
proves: "the plugin manifest says 0.3.0, CHANGELOG has a 0.3.0 section with today's date, and the whole test suite and plugin validation pass"
status: todo
---

## Context

Repo `CLAUDE.md`: every release bumps `version` in `.claude-plugin/plugin.json`, moves the `[Unreleased]` entries under the new version in `CHANGELOG.md`, and tags after merge. The tag is a one-way door and is not part of this ticket: the user tags after the pull request merges. Update the README status paragraph and add a dated spec amendment for anything phase 2 settled that the spec did not say.

Seam: `python3 -m unittest discover -s tests` and `claude plugin validate .`.

## Acceptance

- The proving test passes.
- README's status paragraph and skill table show 0.3.0 for the three new skills and the reviewer agent.
- No `planned 0.3.0` remains anywhere in the README.

## Evidence
