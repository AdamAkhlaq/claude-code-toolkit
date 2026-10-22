# Changelog

All notable changes to this plugin are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.0] - 2026-10-22

Phase 3: maintain and hardening. The loop closes: findings from running software and incidents re-enter the workflow as intents, lessons become eval cases, policies become skills, and the plugin tests itself. This completes change 0001.

### Added

- `diagnose` skill: read-only diagnosis of a finding from running software, written as a new `intent.md`.
- `postmortem` skill and `templates/incident.md`: a blameless incident record under `docs/incidents/`, follow-up intents, and an eval case.
- `eval-case` skill and `templates/eval-case.md`: a prompt plus graders under `evals/` in the format `claude plugin eval` runs.
- `policy-skill` skill and `templates/policy-skill.md`: one policy as a model-invoked skill in the repo's `.claude/skills/`, with two trigger tests.
- `evals/`: the plugin's own eval suite, three cases that pass with the plugin and fail without it.
- `.github/workflows/validate.yml`: unit tests and `claude plugin validate .` on every pull request and push to main. Validation needs no credentials.
- A unit test pinning the deploy gate's block message, after the gate was exercised end to end in a real session.
- Glossary terms: incident, follow-up, eval case, grader.

### Changed

- `tests/test_components.py` checks the shape of every eval case: a named prompt, at least one grader of a known type, and at least one deterministic grader.

## [0.3.0] - 2026-10-22

Phase 2: test and deploy. Bugs are reproduced before they are fixed, reviews run as independent passes, and pull requests are swept to green. This is the first phase built through the workflow itself: four tickets under `docs/changes/0001-plugin-overhaul/tickets/`, each verified in a fresh context before merge.

### Added

- `fix-bug` skill: reproduce as reported, narrow to the fastest failing test, commit it, lock tests with `.claude/.tests-locked`, fix, verify, unlock. Leaves a change folder with the report as origin and the regression test as its one ticket.
- `reviewer` agent and `review` skill: one read-only reviewer per pass in `REVIEW.md`, findings merged into `docs/changes/<change>/review.md` and posted to the pull request, every Important finding fixed or waived by name.
- `pr-sweep` skill: works unresolved review threads and failing checks until the pull request is green, pushes only with approval, stops on design-level comments, repeated check failures and merge conflicts.
- `templates/REVIEW.md` states the finding format reviewers return.
- Glossary terms: reproduction, regression test, test lock, review pass, waiver.

### Changed

- `tests/test_components.py` states the push rule directly: a user-invoked skill either never pushes, or pushes only with approval and never by force.

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

[Unreleased]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/releases/tag/v0.1.0
