# Changelog

All notable changes to this plugin are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-21

Phase 0: plumbing. The plugin installs, the hooks enforce, the graph tool runs, and `setup` prepares a repo. No workflow skills yet.

### Added

- Plugin and marketplace manifests. Install as `toolkit@adamakhlaq`.
- `setup` skill: prepares a repo with `.claude/toolkit.json`, the `docs/` tree, `GLOSSARY.md` and `REVIEW.md`.
- Hooks, each a no-op until `.claude/toolkit.json` exists: `protect-paths`, `format-lint`, `secret-guard`, `lock-tests`, `ticket-sync`, `deploy-gate`.
- `bin/toolkit-graph`: `new`, `frontier`, `validate`, `status` and `render` over a change's ticket graph.
- Templates for `intent.md`, `spec.md`, `plan.md`, tickets, `REVIEW.md` and `toolkit.json`.
- `PHILOSOPHY.md`, `GLOSSARY.md`, and the repo's own first change under `docs/changes/0001-plugin-overhaul/`.

[Unreleased]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/releases/tag/v0.1.0
