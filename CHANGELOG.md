# Changelog

All notable changes to this plugin are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- `toolkit-graph` reads a ticket whose `files` or `blocked_by` list a formatter wrapped over several lines, which prettier does for long lists.

## [0.2.0] - 2026-10-22

Phase 1: plan through build. The four gates and the build loop are live, so a change can go from an idea to merged tickets inside one plugin.

### Added

- User-invoked skills `guide`, `intent`, `spec`, `plan`, `tickets` and `implement`: the four gates and the graph walk.
- Model-invoked skills `grilling`, `glossary`, `verify` and `claude-md`: the discipline the gates and executors share.
- Agents `researcher`, `implementer` and `verifier`.
- `templates/adr.md` for one-way-door decisions recorded by `plan`.
- `tests/test_components.py`: structural checks that every skill and agent keeps the plugin's invocation rules and that the README and `PHILOSOPHY.md` tables stay complete.

### Changed

- Branch and commit conventions for the build: ticket branches are `ticket/<NNNN>-<Tn>`, ticket commits carry a `Ticket:` trailer, and `single` execution works in the main working tree. Recorded as an amendment to the spec of change 0001.

## [0.1.0] - 2026-10-21

Phase 0: plumbing. The plugin installs, the hooks enforce, the graph tool runs, and `setup` prepares a repo. No workflow skills yet.

### Added

- Plugin and marketplace manifests. Install as `toolkit@adamakhlaq`.
- `setup` skill: prepares a repo with `.claude/toolkit.json`, the `docs/` tree, `GLOSSARY.md` and `REVIEW.md`.
- Hooks, each a no-op until `.claude/toolkit.json` exists: `protect-paths`, `format-lint`, `secret-guard`, `lock-tests`, `ticket-sync`, `deploy-gate`.
- `bin/toolkit-graph`: `new`, `frontier`, `validate`, `status` and `render` over a change's ticket graph.
- Templates for `intent.md`, `spec.md`, `plan.md`, tickets, `REVIEW.md` and `toolkit.json`.
- `PHILOSOPHY.md`, `GLOSSARY.md`, and the repo's own first change under `docs/changes/0001-plugin-overhaul/`.

[Unreleased]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/releases/tag/v0.1.0
