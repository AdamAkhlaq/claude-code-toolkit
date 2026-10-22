---
id: T7
title: Release 0.5.0
blocked_by: [T6]
files:
  [
    .claude-plugin/plugin.json,
    CHANGELOG.md,
    README.md,
    docs/changes/0002-block-red-commits/intent.md,
  ]
proves: "the plugin manifest says 0.5.0, CHANGELOG has a 0.5.0 section dated today that lists red-guard, and the whole test suite and `claude plugin validate .` pass"
status: in-progress
executed_by: single
branch: ticket/0002-T7
---

## Context

Spec requirement 17. Plan approach step 7. Repo `CLAUDE.md` release rules, as in 0001-T11.

- `.claude-plugin/plugin.json` `version` to `0.5.0`.
- `CHANGELOG.md`: a `## [0.5.0] - <today>` section under `[Unreleased]`, with a one-line summary and `### Added` (`red-guard`; the glossary terms red and workflow document; the PHILOSOPHY test) and `### Changed` (`implementer`, `verify` and `fix-bug` name the hook; `ticket-sync` placed in PHILOSOPHY; `_common.commit_checkout`).
- `README.md`: the Status paragraph says 0.5.0.
- `intent.md`: `status: shipped` with a dated amendment naming the release.

No tag here. `v0.5.0` is tagged after the pull request merges, on the maintainer's go, behind `deploy-gate`.

Seam: `python3 -m unittest discover -s tests` and `~/.nvm/versions/node/v25.3.0/bin/claude plugin validate .`.

## Acceptance

- The proving check passes, with only the expected root `CLAUDE.md` warning from validate.
- `intent.md` is `shipped` with the amendment.

## Evidence

### Evidence 2026-10-22 19:48

Before the change, `.claude-plugin/plugin.json` said `"version": "0.4.0"` and `CHANGELOG.md` had no 0.5.0 section, so the proving check did not hold.

- `.claude-plugin/plugin.json`: `0.5.0`.
- `CHANGELOG.md`: `## [0.5.0] - 2026-10-22` under an empty `[Unreleased]`, a summary line, `### Added` (`red-guard`, `_common.commit_checkout`, the glossary terms red and workflow document, the two new component and entry tests) and `### Changed` (the three texts naming the hook, the PHILOSOPHY links including `ticket-sync`).
- `README.md`: the Status paragraph says 0.5.0 and adds "no commit lands while the feedback command is red".
- `intent.md`: `status: shipped`, with the amendment "shipped". No tag: `v0.5.0` waits for the merge and the maintainer's go.

`~/.nvm/versions/node/v25.3.0/bin/claude plugin validate .`:

```
  ❯ root: CLAUDE.md at the plugin root is not loaded as project context. To ship context with your plugin, use a skill (skills/<name>/SKILL.md) instead.

✔ Validation passed with warnings
```

The one warning is the expected root `CLAUDE.md` one, recorded in the 0001 intent.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
----------------------------------------------------------------------
Ran 61 tests in 3.943s

OK
```
