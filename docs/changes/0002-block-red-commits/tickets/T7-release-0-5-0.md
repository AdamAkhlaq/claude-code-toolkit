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
status: todo
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
