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
status: done
executed_by: single
branch: ticket/0001-T4
---

## Context

Repo `CLAUDE.md`: every release bumps `version` in `.claude-plugin/plugin.json`, moves the `[Unreleased]` entries under the new version in `CHANGELOG.md`, and tags after merge. The tag is a one-way door and is not part of this ticket: the user tags after the pull request merges. Update the README status paragraph and add a dated spec amendment for anything phase 2 settled that the spec did not say.

Seam: `python3 -m unittest discover -s tests` and `claude plugin validate .`.

## Acceptance

- The proving test passes.
- README's status paragraph and skill table show 0.3.0 for the three new skills and the reviewer agent.
- No `planned 0.3.0` remains anywhere in the README.

## Evidence

### Evidence 2026-10-22 17:37

Command: a release check (manifest says 0.3.0, CHANGELOG has a dated 0.3.0 section, no `planned 0.3.0` in the README, the test suite is OK, `claude plugin validate .` passes) followed by `python3 -m unittest discover -s tests`

Exit code: 0

```
release-check: ok
Ran 46 tests in 1.470s

OK
```

Before the bump the same check exited 1 on the manifest version.

### Verifier 2026-10-22 17:38

Verdict: pass

Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. The seam is a release check, not a unit test: reproduced it as a script that reads `.claude-plugin/plugin.json` (version 0.3.0), checks `CHANGELOG.md` for `## [0.3.0] - 2026-10-22` and greps the README for `planned 0.3.0`, then the suite and `claude plugin validate .`. The branch diff shows the version bump from 0.2.0, so the check fails without the change.
3. proving test run: 0, `release-check: ok`; `python3 -m unittest discover -s tests` exit 0, `Ran 46 tests ... OK`; `~/.nvm/versions/node/v25.3.0/bin/claude plugin validate .` exit 0, `Validation passed with warnings` (one pre-existing warning about CLAUDE.md at the plugin root)
4. feedback command: 0, `Ran 46 tests in 1.304s` / `OK`
5. acceptance: 3 of 3 checked, none failed. Status paragraph says 0.3.0; skill table shows 0.3.0 for `fix-bug`, `review` and `pr-sweep`; the reviewer agent is listed in the agents line, which carries no version column, so its 0.3.0 status is stated by the paragraph only; `grep "planned 0.3.0" README.md` finds nothing.
6. scope: ok. Branch changes `.claude-plugin/plugin.json`, `CHANGELOG.md`, `README.md`, `docs/changes/0001-plugin-overhaul/spec.md` and the ticket file.
7. tests intact: ok, no test file changed on the branch
