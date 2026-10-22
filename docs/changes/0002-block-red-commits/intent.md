---
id: "0002"
slug: "block-red-commits"
status: building
originator: "Adam Akhlaq"
accepted_by: "Adam Akhlaq"
created: "2026-10-22"
---

# Intent: no commit lands while the feedback command is red

## Origin

The candidate list recorded at the end of change 0001, item 1:

> A pre-commit hook that runs the feedback command, because the executor committed on red once by hand in phase 2.

From the conversation that produced this document, in the originator's words:

> Change 0001 is done and released as v0.4.0. [...] help me choose change 0002 from the candidates in the memory note.

The originator chose "Red-commit hook" from the candidates, then answered the two questions below with the recommended options.

The failure it comes from, as recorded in the evidence of ticket 0001-T3 at 2026-10-22 17:32:

> The first run after that edit exited 1 [...] That commit (`9e94a85`) was made on red, against the executor contract; this run supersedes it.

## Problem

An executor can commit while the feedback command is red, and nothing stops it. The rule against it exists only as text: `agents/implementer.md` steps 6 and 7 say red means not done and commit after verifying, and the `verify` skill says the same. Text can be missed. In 0001-T3 it was: after a verifier reopen, the executor edited `skills/pr-sweep/SKILL.md`, committed it as `9e94a85`, and ran the suite only afterwards, which exited 1.

Who has it: the maintainer of any repo that uses the toolkit, and every executor that commits, whether `single`, subagent, team or headless. What it costs: a ticket branch holds a commit that fails the project's own checks, the ticket's evidence and its commit disagree, and the only thing that caught it in 0001-T3 was the executor confessing in its next evidence entry. Had it not, the first to notice would have been the verifier, or, if a later green commit hid it, nobody, leaving a broken commit in the history that `git bisect` and reverts land on. Unattended runs are exactly where nobody is watching for this.

## Proposed outcome

In a repo with `.claude/toolkit.json` and a `feedbackCommand`, a commit Claude attempts while the feedback command is red does not land. Claude is told the commit was stopped and sees the failing output, so it fixes the code and tries again. Commits made while the feedback command is green land as before, slower only by the time the command takes.

The one deliberate red commit in the workflow still lands: the failing regression test that `fix-bug` commits before its fix, where nothing is staged but test files and the change's own documents. No human is asked to approve anything for this to work, so it holds in headless and subagent runs too.

It is shown working in a real Claude Code session with the plugin loaded, not only in unit tests, and `PHILOSOPHY.md` names it as the enforcer of the rule it now enforces.

## Affected users and systems

- Every consuming repo with `.claude/toolkit.json`. Repos without the file are untouched.
- Commits made by Claude through its Bash tool. Commits a human makes in their own terminal are not covered.
- `hooks/hooks.json`, `hooks/scripts/` and `hooks/scripts/_common.py`, where the two existing commit hooks (`secret_guard.py`, `ticket_sync.py`) recognise `git commit`. `tests/test_hooks.py`.
- The skills and agents that commit and describe the rule today: `agents/implementer.md`, `skills/fix-bug/SKILL.md` step 7, `skills/verify/SKILL.md`.
- `README.md` hooks table, `PHILOSOPHY.md` "Enforced by" column, `CHANGELOG.md`.

## Constraints

- Standard library only. With no `.claude/toolkit.json`, the hook exits 0 with no output.
- Claude Code runs command hooks with a default timeout of 600 seconds. A PreToolUse hook that times out does not block the call unless it declares `onFailure: "block"`, which needs Claude Code 2.1.295 or later; 2.1.304 is installed here. This repo's feedback command takes about 1.4 seconds, but a consumer's may take minutes.
- Composition over configuration: no setting that turns the rule off.
- A red suite is red whatever the cause, including a failure unrelated to the current work, as `verify` already says.

## Open questions

- Resolved, decision: only commits Claude attempts are covered, not a human's terminal commits. Nothing is installed into `.git/hooks`.
- Resolved, decision: a red commit is stopped outright, with one exception: a commit whose staged files are only test files and the change's documents, which is the shape of `fix-bug`'s regression-test commit. No human prompt.
- Resolved, fact: the hook timeout and `onFailure` behaviour above, from the Claude Code hooks reference, read 2026-10-22.
- Open, decision, owner the originator at the spec gate: whether a commit that stages only `docs/` files runs the feedback command at all. Assumed for now that it does not, because gate and ticket-claim commits cannot change the result in a typical repo and running a slow suite on each would add minutes to every gate.
- Open, decision, owner the originator at the spec gate: what happens when the feedback command outlives the hook timeout, letting the commit through or stopping it.
- Open, decision, owner the originator at the spec gate: whether the feedback command runs against the working tree or only what is staged, when the two differ.
- Open, fact, for the spec: how a PreToolUse block behaves under `bypassPermissions` and inside subagents. The hooks reference does not say; settle it in a live session.

## Amendment 2026-10-22: spec decisions

The spec widens the exception from "test files and the change's documents" to test files and every workflow document (anything under `docs/`, `GLOSSARY.md`, `REVIEW.md`), so gate, claim and verifier commits on a red tree land too. The open questions are settled there: docs-only commits skip the check; a feedback command that does not finish in time stops the commit; the check runs against the working tree. The fact on permission modes is settled live: a block holds under `bypassPermissions` and inside subagents. The same probe found that the existing hooks resolve paths against the main checkout inside a worktree; that is change 0003.

## Amendment 2026-10-22: building

Seven tickets, T1 to T7, in one chain, executed `single` as the plan records, on the integration branch `change/0002-block-red-commits`.
