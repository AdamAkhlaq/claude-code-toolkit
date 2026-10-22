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
status: done
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

### Evidence 2026-10-22 18:01

Command: a release check (manifest says 0.4.0, CHANGELOG has a dated 0.4.0 section, no `planned` in the README, the intent is `shipped`, every component name in PHILOSOPHY's Enforced by column is a link, the test suite is OK, `claude plugin validate .` passes) followed by `python3 -m unittest discover -s tests`

Exit code: 0

```
release-check: ok
Ran 49 tests in 1.358s

OK
```

Before the bump the same check exited 1 on the manifest version.

### Verifier 2026-10-22 18:12

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok, the release check is reproducible from the ticket (manifest version, dated CHANGELOG section, README grep, intent status, PHILOSOPHY links, suite, validator) and the manifest version alone would fail it before the bump
3. proving test run: 0, manifest says 0.4.0; CHANGELOG has `## [0.4.0] - 2026-10-22`; `grep -i planned README.md` finds nothing; `Ran 49 tests ... OK`; `claude plugin validate .` exits 0 with only the expected root CLAUDE.md warning
4. feedback command: 0, `Ran 49 tests in 1.425s` / `OK`
5. acceptance: 3 of 3 checked, none failed. Intent status is `shipped` with an amendment naming v0.1.0 to v0.4.0; all 15 PHILOSOPHY rows have every backticked component as a link and every link target exists on disk
6. scope: ok, branch changes plugin.json, CHANGELOG.md, README.md, intent.md, spec.md and the ticket file only
7. tests intact: ok, no changes under tests/ on the branch
