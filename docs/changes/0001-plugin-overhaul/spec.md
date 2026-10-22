---
id: 0001
slug: plugin-overhaul
status: accepted
go_no_go: go
decided_by: Adam Akhlaq
created: 2026-10-21
---

# Spec: the toolkit plugin

## Outcome

Installing `toolkit@adamakhlaq` gives a Claude Code session a complete workflow from idea to merged code: `/toolkit:intent` through `/toolkit:pr-sweep`, with the build stage run as a ticket graph, every stage leaving a committed artifact, and hooks enforcing the rules that must always hold.

## Scope

In scope: the plugin manifests, every skill, agent, hook, executable and template listed below, the repo's own documentation, and this repo adopting the workflow for its own changes.

Out of scope: a GitHub issue tracker mirror, support for harnesses other than Claude Code, and a CI eval pipeline for consuming repos.

## Identity and distribution

- Marketplace name `adamakhlaq`, defined in `.claude-plugin/marketplace.json` with one entry whose source is `./`.
- Plugin name `toolkit`, defined in `.claude-plugin/plugin.json`. Skills are invoked as `/toolkit:<name>`.
- Install: `claude plugin marketplace add AdamAkhlaq/claude-code-toolkit` then `claude plugin install toolkit@adamakhlaq`.
- Versions follow semver, bumped by hand in `plugin.json`, recorded in `CHANGELOG.md`, tagged in git.

## Repository layout

```
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
skills/<name>/SKILL.md
agents/<name>.md
hooks/hooks.json
hooks/scripts/<name>.sh
bin/toolkit-graph
templates/{intent,spec,plan,ticket,REVIEW,toolkit.json}.md
docs/changes/<NNNN>-<slug>/{intent,spec,plan,review}.md and tickets/*.md
docs/adr/NNNN-<slug>.md
docs/incidents/YYYY-MM-DD-<slug>.md
evals/
CLAUDE.md  GLOSSARY.md  PHILOSOPHY.md  README.md  CHANGELOG.md  LICENSE
```

## Components

Skills. User-invoked skills carry `disable-model-invocation: true` and a human-facing description. Model-invoked skills carry a trigger-rich description.

| Skill          | Invocation | Produces or enforces                                                                                                                                  |
| -------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `setup`        | user       | `.claude/toolkit.json`, `docs/changes/`, `GLOSSARY.md`, `REVIEW.md`, a proposed permissions allowlist, a definition of done in the repo's `CLAUDE.md` |
| `guide`        | user       | Routes the user to the right skill for their situation                                                                                                |
| `intent`       | user       | `intent.md` from any input, gated by a definition of ready                                                                                            |
| `spec`         | user       | `spec.md` from `intent.md`, with policy conflicts flagged                                                                                             |
| `plan`         | user       | `plan.md` in plan mode, interrogated, with seams and the execution decision                                                                           |
| `tickets`      | user       | `tickets/*.md` as a validated graph of tracer bullets                                                                                                 |
| `implement`    | user       | Walks the graph frontier, hands tickets to the configured executor, merges after verification                                                         |
| `fix-bug`      | user       | Reproduction as reported, minimised failing test, locked fix                                                                                          |
| `review`       | user       | Three `REVIEW.md` passes, findings in `review.md` and on the PR                                                                                       |
| `pr-sweep`     | user       | Resolves comments and failing checks until the PR is green                                                                                            |
| `diagnose`     | user       | Read-only diagnosis of a finding, written as a new `intent.md`                                                                                        |
| `postmortem`   | user       | Incident record in `docs/incidents/`, follow-up intent, eval case                                                                                     |
| `eval-case`    | user       | A prompt plus checks under `evals/` from a past task or incident                                                                                      |
| `policy-skill` | user       | A new skill encoding one policy, with trigger tests                                                                                                   |
| `glossary`     | model      | Terms coined, challenged and recorded in `GLOSSARY.md`                                                                                                |
| `verify`       | model      | Runs the feedback command, quotes output, records evidence in the ticket                                                                              |
| `claude-md`    | model      | Creates or trims `CLAUDE.md`, adds a line when a correction repeats                                                                                   |
| `grilling`     | model      | Numbered question rounds with recommended answers, used by `intent`, `spec` and `plan`                                                                |

Agents, each with a name, a when-to-use description and a tool allowlist.

| Agent         | Role                                                                                |
| ------------- | ----------------------------------------------------------------------------------- |
| `implementer` | Works one ticket in one worktree: failing test, code, verify, commit, status update |
| `verifier`    | Re-runs a ticket's checks in a fresh context, passes or reopens it                  |
| `reviewer`    | Executes one `REVIEW.md` pass                                                       |
| `researcher`  | Read-only exploration of code or sources, reports with citations                    |

Hooks, registered in `hooks/hooks.json`, each reading `.claude/toolkit.json` and exiting silently when it is absent.

| Hook            | Event                                 | Config key              | Behaviour                                                    |
| --------------- | ------------------------------------- | ----------------------- | ------------------------------------------------------------ |
| `protect-paths` | PreToolUse Edit, Write                | `protectedPaths`        | Block, naming the approval route                             |
| `format-lint`   | PostToolUse Edit, Write               | `formatters`, `linters` | Run on the changed file only                                 |
| `secret-guard`  | PreToolUse Bash matching `git commit` | none                    | Scan the staged diff for credential patterns, block on a hit |
| `lock-tests`    | PreToolUse Edit, Write                | `testGlobs`             | Block while `.claude/.tests-locked` exists                   |
| `ticket-sync`   | PreToolUse Bash matching `git commit` | none                    | Ask when source is staged and no ticket file is              |
| `deploy-gate`   | PreToolUse Bash                       | `gatedCommands`         | Block unless `RELEASE_AUTHORIZED` is set                     |

Executable `bin/toolkit-graph`, dependency-free, with subcommands `new` (allocate the next change id), `frontier`, `validate`, `status` and `render`.

## Artifact conventions

- Change id is a zero-padded sequence allocated by `toolkit-graph new`. Commits carry a `Change: NNNN` trailer. Ticket ids are `NNNN-Tn`.
- `intent.md` requires Origin, Problem and Proposed outcome. Affected users and systems, Constraints and Open questions are optional. Its frontmatter `status` is one of `proposed`, `accepted`, `building`, `shipped`, `abandoned`.
- `plan.md` frontmatter carries `execution` as one of `single`, `subagents`, `team`, `headless`, plus `concurrency`. An Execution section states the reason.
- A ticket's frontmatter carries `id`, `title`, `blocked_by`, `files`, `proves`, `status`, optional `serial` and `executor`, and on completion `executed_by` and `branch`.
- Every executor works one ticket in one worktree on one branch and merges into the integration branch only after `verifier` passes.
- After a gate, an artifact is amended with a dated `## Amendment` section, never rewritten.

## Per-project configuration

`.claude/toolkit.json` keys: `protectedPaths`, `formatters`, `linters`, `testGlobs`, `feedbackCommand`, `gatedCommands`, `concurrency`, `tracker`. All optional. `setup` writes the file with commented defaults inferred from the repo.

## Invocation rules

A user-invoked skill may call model-invoked skills through the Skill tool, naming them as `toolkit:<name>`. No skill calls a user-invoked skill. Shared discipline lives in model-invoked skills, never in cross-folder file references.

## Policy conflicts flagged

- The plugin docs state that a `CLAUDE.md` at the plugin root is not loaded and that validate warns about it. This repo wants a maintainer `CLAUDE.md`. Resolution: keep it, verify in phase 0, drop `--strict` if that is the only warning.
- `review` sits beside Claude Code's built-in code review and `researcher` beside the built-in Explore agent. Resolution: keep both, because `review` adds the spec-compliance pass and `researcher` adds citation discipline. Revisit if they prove redundant.
- The originator's global rule requires end-to-end reproduction of bugs. The philosophy prefers fast unit tests. Resolution, recorded in `PHILOSOPHY.md`: reproduce as reported first, then minimise to the fastest test that fails for the same reason.

## Amendment 2026-10-21: hooks and the graph tool are Python

Hook scripts are `hooks/scripts/<name>.py`, not `.sh`, and share `hooks/scripts/_common.py`. The graph tool is Python too. Both use the standard library only, so a consuming repo needs `python3` and `git` and nothing else, and there is no `jq` dependency. One extra config key exists: `secretAllowlist`, paths where credential-looking strings are expected, read by `secret-guard`. Path patterns with no `/` other than a trailing one match anywhere in the tree.

## Amendment 2026-10-22: build conventions settled in phase 1

- The integration branch is `change/<NNNN>-<slug>`; ticket branches are `ticket/<NNNN>-<Tn>`, created from it. Ticket commits carry a `Ticket: <NNNN>-<Tn>` trailer beside `Change: <NNNN>`.
- Worktrees live at `.claude/worktrees/<NNNN>-<Tn>/`, excluded through `.git/info/exclude`. In `single` execution the ticket branch is checked out in the main working tree, because a worktree exists to isolate concurrent executors and there is only one.
- The executor leaves a ticket `in-progress` with its evidence; only the `verifier` sets `done` or `reopened`, so the frontier never unblocks a dependent before verification.
- A one-way-door decision in a plan is recorded as an ADR from `templates/adr.md`, which joins the template list.
- The invocation rules (user-invoked skills carry `disable-model-invocation: true`, no skill names a user-invoked skill, every agent has a tool allowlist) and the completeness of the README and `PHILOSOPHY.md` tables are checked by `tests/test_components.py`, resolving the open question on whether composition over configuration gets a script.
- In `single` execution the `implement` skill follows the executor steps in `agents/implementer.md` itself, in the session. This is the one cross-folder file reference in the plugin, kept so the executor contract exists in exactly one place.

## Amendment 2026-10-22: phase 2 conventions

- A bug fix is a change. `fix-bug` allocates a change folder with an `intent.md` whose origin is the report and a one-ticket graph whose `proves` is the regression test; a spec and a plan are not required for it.
- `review.md` joins the change folder's artifacts, written by `review`, with every Important finding as a checkbox closed by a fix commit hash or a named waiver. Findings are also posted to the pull request as inline comments so that `pr-sweep` can resolve them.
- `pr-sweep` is the one skill that pushes, with the user's approval per push and never by force. The structural test now states that rule instead of the earlier never-push heuristic.
- Phase 2 was executed through the workflow: tickets T1 to T4 under this change, `single` execution on `change/0001-phase-2`, one fresh-context verifier per ticket. T3 was reopened twice by verifiers, both times correctly, and fixed in the session rather than stopping the run, since the originator was the executor.

## Amendment 2026-10-22: phase 3 conventions

- Eval cases use the `claude plugin eval` layout: `evals/<case>/prompt.md` plus `graders/*.md`. Each case needs at least one deterministic grader. `regex` graders are JavaScript regexes, so case-insensitivity is `flags: i`. On this maintainer's machine the runner refuses a Bash grant, so the plugin's own cases need none.
- `postmortem` and `policy-skill` write eval cases from `templates/eval-case.md` directly rather than through `eval-case`, which is user-invoked and therefore not callable from a skill.
- Templates that ship fenced YAML use `<PLACEHOLDER>` rather than `{{PLACEHOLDER}}`, which prettier rewrites.
- CI runs the unit tests and `claude plugin validate .` without `--strict`, because the root `CLAUDE.md` warning is expected. `claude plugin validate` needs no credentials. The eval suite is run by hand before a release.
- `templates/incident.md` and `templates/policy-skill.md` join the template list.
