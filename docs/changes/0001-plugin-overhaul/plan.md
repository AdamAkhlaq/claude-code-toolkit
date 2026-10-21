---
id: 0001
slug: plugin-overhaul
status: accepted
execution: single
concurrency: 1
created: 2026-10-21
---

# Plan: build the plugin in four phases

## Approach

Build the plugin in phases that each ship an installable version. Plumbing first, so every later skill is written and tested against a working install. The repo adopts its own workflow from the moment the gate skills exist, so later phases are built using earlier ones.

## Execution

`single`. One agent in one session with the originator at the keyboard. The work is sequential by nature: each phase depends on the previous one being installed, and the earliest phases are plumbing where the originator wants to review every file. There is no graph to parallelise until phase 1 exists, and by then the tickets for phases 2 and 3 can be run through the plugin itself.

## Seams

Tests live at these boundaries and nowhere else:

- `bin/toolkit-graph`: unit tests over fixture change folders for `frontier`, `validate` (cycles, unresolved edges, overlapping files) and `new`.
- Hook scripts: each run against sample tool-call JSON on stdin, asserting exit code and stderr, both with and without a `toolkit.json` present.
- Manifests: `claude plugin validate .` passes.
- End to end: load with `claude --plugin-dir .` in a throwaway repo, run `/toolkit:setup`, trigger each hook once.

Skill prose is not unit-tested. Phase 3 adds a `claude plugin eval` suite that exercises the skills on real tasks.

## Phases

### Phase 0: plumbing, 0.1.0

1. Write `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
2. Write the maintainer `CLAUDE.md`, seed `GLOSSARY.md` with the workflow's own terms, `README.md`, `CHANGELOG.md`, MIT `LICENSE`, `.gitignore`, and a permissions-only `.claude/settings.json` for this repo.
3. Write `bin/toolkit-graph` with `new`, `frontier`, `validate`, `status`, `render`, plus its tests.
4. Write the six hook scripts and `hooks/hooks.json`, plus their tests.
5. Write the templates: `intent.md`, `spec.md`, `plan.md`, `ticket.md`, `REVIEW.md`, `toolkit.json`.
6. Write the `setup` skill.
7. Validate, smoke-test the install, commit, tag `v0.1.0`.

### Phase 1: plan through build, 0.2.0

1. Model-invoked skills: `grilling`, `glossary`, `verify`, `claude-md`.
2. Agents: `researcher`, `verifier`, `implementer`.
3. User-invoked skills: `guide`, `intent`, `spec`, `plan`, `tickets`, `implement`.
4. Run this repo's next change through the new skills end to end. Commit, tag `v0.2.0`.

### Phase 2: test and deploy, 0.3.0

1. `fix-bug` with the `lock-tests` flow.
2. `reviewer` agent, `review` skill, `REVIEW.md` template wired in.
3. `pr-sweep`. Commit, tag `v0.3.0`.

### Phase 3: maintain and hardening, 0.4.0

1. `diagnose`, `postmortem`, `eval-case`, `policy-skill`.
2. `deploy-gate` behaviour exercised end to end.
3. `evals/` suite for the plugin and a GitHub Action running validate. Commit, tag `v0.4.0`.

## Interrogation

What could break: the hook scripts, because they run inside every consumer's session and a bug there blocks real work. That is why they get the strictest tests and the no-config-means-no-op rule.

Riskiest step: `implement` walking the graph with parallel executors. A wrong frontier or an overlapping file set corrupts the integration branch. `toolkit-graph validate` runs before any executor starts, and worktree-per-ticket contains the blast radius to one branch.

Could a stranger implement this from the plan alone: for phases 0 and 2, yes. For phase 1 the skill prose carries the judgment and needs `PHILOSOPHY.md` and `spec.md` read first, which this plan links.

## Rejected alternatives

- A catalog of files users copy into each project. Rejected because copied files drift and a process must not.
- Tickets in GitHub issues first. Rejected for now: local files keep the git audit trail and need no adapter. GitHub becomes a mirror later.
- A linear chain of stages with no ticket graph. Rejected: the originator prefers agent-scheduled execution over hand-scheduled stages.
- An automated release pipeline with changesets. Rejected: manual versioning is enough for one maintainer.
- Multi-harness support. Rejected until another harness is actually in use.
