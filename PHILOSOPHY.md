# Philosophy

This toolkit is opinionated. Every skill, agent and hook exists to serve one of the principles below. When a piece of the workflow conflicts with a principle, the principle wins and the piece changes.

Each principle names what enforces it. A principle without an enforcer is only a wish.

## At a glance

| Principle                             | In one line                                                          | Enforced by                                                                                                                                                                                                                                             |
| ------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| One shared language                   | Define a term once in `GLOSSARY.md`, use it everywhere               | `glossary`                                                                                                                                                                                                                                              |
| Open front door, fixed exit           | Start from anything, always end in a committed `intent.md`           | `intent`                                                                                                                                                                                                                                                |
| Every gate leaves an artifact         | Each stage commits a file, amended later but never rewritten         | `intent`, `spec`, `plan`, `tickets`                                                                                                                                                                                                                     |
| Tickets are tracer bullets            | One behaviour per ticket, provable, fits one session                 | `tickets`, [`toolkit-graph`](./bin/toolkit-graph)                                                                                                                                                                                                       |
| Seams before tests, tests before code | Agree where tests go, write the failing test, then the code          | `plan`, [`lock-tests`](./hooks/scripts/lock_tests.py)                                                                                                                                                                                                   |
| Reproduce before fixing               | Reproduce as the user hit it, then narrow to a fast test             | `fix-bug`                                                                                                                                                                                                                                               |
| Verification is independent           | The author never judges their own work                               | `verify`, `verifier`                                                                                                                                                                                                                                    |
| Autonomy is tiered by reversibility   | Reversible work runs unattended, irreversible work waits for a human | `tickets`, [`deploy-gate`](./hooks/scripts/deploy_gate.py)                                                                                                                                                                                              |
| Execution is pluggable                | The ticket is the contract, the executor is a recorded choice        | `plan`, `implement`                                                                                                                                                                                                                                     |
| Skills advise, hooks enforce          | Anything that must always hold is a hook or a CI check               | [`protect-paths`](./hooks/scripts/protect_paths.py), [`format-lint`](./hooks/scripts/format_lint.py), [`secret-guard`](./hooks/scripts/secret_guard.py), [`lock-tests`](./hooks/scripts/lock_tests.py), [`deploy-gate`](./hooks/scripts/deploy_gate.py) |
| Deterministic where possible          | If a script can do it, a script does it                              | [`toolkit-graph`](./bin/toolkit-graph), [`format-lint`](./hooks/scripts/format_lint.py)                                                                                                                                                                 |
| Composition over configuration        | A different workflow is a different skill, not a setting             | none yet                                                                                                                                                                                                                                                |
| Artifacts are tool-agnostic           | Markdown in git is the source of truth                               | [`setup`](./skills/setup/SKILL.md), [`toolkit-graph`](./bin/toolkit-graph)                                                                                                                                                                              |
| Mistakes become memory                | Repeated mistakes go to `CLAUDE.md`, incidents become evals          | `claude-md`, `postmortem`, `eval-case`                                                                                                                                                                                                                  |
| The loop closes                       | Findings from running software re-enter as intents                   | `diagnose`, `postmortem`                                                                                                                                                                                                                                |

## Before building

### One shared language

A term is defined once, in `GLOSSARY.md` at the repo root, and then used everywhere: code, tickets, conversation. When people and agents use different words for the same thing they misunderstand each other and spend many words saying little. A shared vocabulary makes names consistent, code easier to navigate, and every message shorter.

### Open front door, fixed exit

Work can start from anything: a conversation, a pasted ticket, a one-line idea, an alert, or "explore this and tell me what is wrong". It always ends in a committed `intent.md`. Forcing a form before the first conversation kills good ideas. What matters is that enough context is gathered, by searching code, searching the web, or asking questions, before anyone builds. The agent finds facts. The human makes decisions.

### Every gate leaves an artifact

Each stage ends by committing a file: `intent.md`, `spec.md`, `plan.md`, then the ticket files. A committed artifact is a decision you can point at later, and git history records who decided what and when. Changes after a gate are added as a dated amendment, never written over, so the history shows what was known at the time.

## While building

### Tickets are tracer bullets

Each ticket proves one behaviour end to end, fits inside one agent session, and names its proving test before any code is written. Small vertical slices give fast feedback and are easy to verify and hand off. The graph tool checks that tickets form no cycles and that tickets running in parallel do not touch the same files.

### Seams before tests, tests before code

The plan agrees where tests will go. Each ticket writes its failing test first, confirms it fails for the expected reason, then writes the code. Prefer fast unit tests at the agreed seams over slow end-to-end suites, because fast tests get run constantly and slow ones get skipped. The `lock-tests` hook stops anyone editing a test to make it pass.

### Reproduce before fixing

No bug is fixed until it has been reproduced as closely as possible to how it was reported: same environment, same inputs, same route through the product, end to end if that is how the user hit it. A fix for a bug you have not reproduced is a guess, and reproducing it the user's way finds the real cause rather than a nearby one. Once confirmed, narrow it to the fastest test at the nearest seam that still fails for the same reason. That test is committed before the fix and stays as a regression guard.

### Verification is independent

Whoever wrote the code does not judge whether it works. Done means quoted output from the project's feedback command, recorded in the ticket, and then a `verifier` agent re-runs the checks in a fresh context that has not seen the reasoning. An agent that just wrote something believes it works. A verifier runs the checks instead.

### Autonomy is tiered by reversibility

Reversible work runs unattended. Irreversible work, such as a migration, a production deploy or a public API change, waits for a human. The cost of a mistake decides how much supervision it needs. One-way-door tickets are marked `serial: true` and run in the main session with a human watching, the `deploy-gate` hook blocks gated commands until a release is authorised, and the pull request states which kind of door the change was.

### Execution is pluggable

The ticket is the contract. Who executes it, a single agent, subagents, an agent team, or a headless job, is a decision recorded in `plan.md` with its reason. A documentation fix needs one agent. A ten-ticket feature with shared state may need a team. Work you walk away from needs headless runs. Every executor works one ticket in one worktree on one branch, merged into the integration branch only after the verifier passes.

## The system around the work

### Skills advise, hooks enforce

A skill is text the model reads. It can be missed or overridden. A hook is code that runs every time, whatever the model decides. So anything that must always hold is a hook or a CI check: protected paths, formatting, secret scanning, test locking, deploy gating. Everything about how to think is a skill.

### Deterministic where possible

If a script can do it, a script does it, and model judgment is spent on judgment. Scripts give the same answer every time and cost nothing. Asking a model which tickets are ready, or whether a graph has a cycle, invites a different answer each session. The graph tool computes the frontier and validates the graph. Hooks format and lint. Skills call these rather than reasoning about them.

### Composition over configuration

Skills are small and compose. A different workflow is a different skill, not a setting on an existing one, because every option is a path that has to be tested and explained. User-invoked skills orchestrate. Model-invoked skills hold reusable discipline. A user-invoked skill may call model-invoked ones, and no skill ever calls a user-invoked skill.

### Artifacts are tool-agnostic

Every artifact is Markdown with YAML frontmatter, stored in git under `docs/`. Tools change, but files in git are readable by any agent, any editor and any future tool, and they travel with the code they describe. A tracker, if one is connected, is a mirror of the files and never the only copy.

### Mistakes become memory

Nothing is learned only in a transcript, because a lesson in a chat is gone when the session ends. The same correction given twice goes into `CLAUDE.md`. A review flag raised twice goes into `CLAUDE.md`. A postmortem produces an eval case that catches the same class of failure next time.

### The loop closes

Every finding from running software re-enters the workflow as an intent. `diagnose` writes its findings as a new `intent.md`, and `postmortem` does the same for follow-up work, so both pass through the same gates as any other change. Fixes made outside the loop skip the gates, leave no artifact, and teach the system nothing.
