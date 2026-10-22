---
id: "0002"
slug: "block-red-commits"
status: accepted
go_no_go: go
decided_by: "Adam Akhlaq"
created: "2026-10-22"
---

# Spec: no commit lands while the feedback command is red

## Outcome

A new hook, `red-guard`, stops any `git commit` Claude attempts in a repo with `.claude/toolkit.json` while the feedback command is red, and hands Claude the failing output. A commit made on green lands as before. A commit whose changes are only workflow documents or test files, which covers `fix-bug`'s failing regression test and every gate, claim and verifier commit, lands without the feedback command running. The block holds under every permission mode and inside subagents, and a feedback command that does not finish in time stops the commit rather than letting it through.

This widens the intent's exception from "test files and the change's documents" to test files and all workflow documents; see the intent's amendment of 2026-10-22.

## Scope

In scope:

- The `red-guard` hook: its script, its entry in `hooks/hooks.json`, and unit tests in `tests/test_hooks.py`.
- A live proof in a headless Claude Code session with the plugin loaded.
- The text that states the rule today: `agents/implementer.md`, `skills/verify/SKILL.md`, `skills/fix-bug/SKILL.md` step 7.
- `README.md` hooks table, `PHILOSOPHY.md` "Enforced by" column and prose, `CHANGELOG.md`.
- Release 0.5.0: `version` in `.claude-plugin/plugin.json` and the `CHANGELOG.md` section. The `v0.5.0` tag is pushed after merge, on the maintainer's go.

Out of scope, though a reader might assume otherwise:

- Commits a human makes in their own terminal. Nothing is installed into `.git/hooks`.
- Merge commits made by `git merge`, including the merges `implement` makes of verified ticket branches. They are not `git commit` and are not checked; the ticket was verified green before the merge.
- A commit that leaves part of the working tree unstaged. The feedback command runs against the working tree, so a commit that stages only some of the pending changes is checked against more than it contains. See Design notes.
- The worktree bug in the existing hooks (`secret-guard`, `ticket-sync`, `protect-paths`, `lock-tests` resolve paths against `CLAUDE_PROJECT_DIR`, the main checkout, not the worktree the command runs in). It is change 0003, through `/toolkit:fix-bug`, right after this one.
- Caching a green result so that a commit straight after a `verify` run skips the second run. The cost is accepted.
- An eval case. The hook is deterministic; the unit tests and the live proof cover it.
- Any new key in `.claude/toolkit.json`.

## Requirements

### When it runs

1. On a Bash command that is not a `git commit`, as `_common.is_git_commit` recognises one, `red-guard` exits 0 with no output and does not run the feedback command.
2. The checkout a commit lands in is resolved from, in order: the directory of a `git -C <dir>` in the command; the directory of a leading `cd <dir> &&` in the command; the `cwd` field of the hook event; `CLAUDE_PROJECT_DIR`. Everything below reads that checkout's top level, as `git rev-parse --show-toplevel` reports it, never the main checkout when the commit is in a worktree.
3. With no `.claude/toolkit.json` in that checkout, or with `feedbackCommand` missing or empty, `red-guard` exits 0 with no output.
4. The pending changes are every path `git status --porcelain` reports in that checkout: staged, unstaged and untracked files that are not ignored. This includes a `git add` earlier in the same command, which has not run yet when the hook fires.
5. When every pending change is a workflow document or a test file, the feedback command does not run and the commit proceeds. A test file is a path matching `testGlobs` in `.claude/toolkit.json`, with the same glob rules as the other hooks.
6. When at least one pending change is neither, `red-guard` runs the feedback command exactly as configured, through the shell, from the checkout's top level.

### What it decides

7. The feedback command exits 0: the commit proceeds, and `red-guard` prints nothing.
8. The feedback command exits non-zero: the commit is blocked (exit 2). The message names the command and its exit code, quotes at most the last 40 lines of its combined output, says the commit was stopped because the feedback command is red, and says to fix the code and commit again, never to edit a test to reach green.
9. The feedback command has not finished after 570 seconds: it is stopped, and the commit is blocked with a message that names the limit and says a feedback command that cannot finish is treated as red.
10. The hook entry declares `timeout: 600` and `onFailure: "block"`, so a `red-guard` that is itself killed or times out on a `git commit` stops the commit.
11. An unexpected error inside `red-guard` on a command that is not a `git commit` lets that command through, so a fault in the hook never blocks unrelated Bash commands.

### Proof

12. `tests/test_hooks.py` covers requirements 1 to 9 and 11 by running the script on synthetic events against temporary git repositories, with feedback commands that pass, fail and hang.
13. In a headless session with the plugin loaded from a clone, against a temporary repo with `.claude/toolkit.json`, each of these is observed and its transcript quoted in the ticket's evidence: a commit with a source change on red is blocked and the session reports the failing output; the same commit lands once the source is green; a commit staging only a failing test file lands; a commit made from a worktree under `.claude/worktrees/` runs the feedback command in that worktree. At least the red-commit block is shown under `--permission-mode bypassPermissions`.

### Documentation and release

14. `README.md`'s hooks table has a `red-guard` row: fires before `git commit`, config keys `feedbackCommand` and `testGlobs`, and its effect in one line.
15. `PHILOSOPHY.md` names `red-guard` in the "Enforced by" column of "Skills advise, hooks enforce" and in that section's list of what hooks enforce.
16. `agents/implementer.md`, `skills/verify/SKILL.md` and `skills/fix-bug/SKILL.md` step 7 say that `red-guard` enforces the rule they state, and fix-bug says why its failing-test commit is let through.
17. `.claude-plugin/plugin.json` is at `0.5.0`, `CHANGELOG.md` has a `0.5.0` section listing `red-guard`, and `python3 -m unittest discover -s tests` and `claude plugin validate .` pass.

## Policy conflicts flagged

Sources checked: `intent.md`, `GLOSSARY.md`, `PHILOSOPHY.md`, the repo `CLAUDE.md`, the maintainer's global `CLAUDE.md`, `docs/adr/` (empty), `.claude/skills/` (absent, no policy skills), and other live changes (none).

- **Seams before tests, tests before code** (`PHILOSOPHY.md`, owner the maintainer). `fix-bug` commits a failing test on purpose. Resolved: a commit whose changes are only test files and workflow documents skips the check (requirement 5).
- **Verification is independent** (`PHILOSOPHY.md`). The verifier commits its reopen verdict to the ticket while the code may be red. Resolved: the verdict is a workflow document, so the commit skips the check.
- **Composition over configuration** (`PHILOSOPHY.md`). Resolved: no new configuration key and no switch to turn the rule off. The hook reuses `feedbackCommand` and `testGlobs`.
- **Never make a hook act on a project without `.claude/toolkit.json`; standard library only** (repo `CLAUDE.md`). Resolved by requirements 3 and the script's imports.
- **No commit without the maintainer's go** (both `CLAUDE.md` files). No conflict: the hook can only stop commits, never make one.
- **The worktree bug in the existing hooks.** Out of scope here and deferred to change 0003, decided by the maintainer on 2026-10-22. `red-guard` must not repeat it (requirement 2).
- **`REVIEW.md` is missing from this repo**, and `/toolkit:review` runs one pass per section of it. Open, owner the maintainer, to settle before `/toolkit:review 0002`: add one, or run the default passes the glossary names.
- **Subagents decline to commit under the maintainer's global `CLAUDE.md`.** Observed on 2026-10-22: a general-purpose subagent asked to commit refused even with the approval relayed, because the approval did not come from the user directly. This bears on the plan's execution decision, since `implementer` commits as its last step. Open, owner the maintainer, to settle in `/toolkit:plan 0002`.

## Design notes

- Script `hooks/scripts/red_guard.py`, beside `secret_guard.py` and `ticket_sync.py`, sharing `_common.py`. Added to the `Bash` PreToolUse group in `hooks/hooks.json` after `secret-guard`, so a commit with a secret is refused before a slow suite runs.
- Narrowing the entry with `"if": "Bash(git *)"` would keep `onFailure: "block"` off every other Bash call. The reference calls `if` best-effort and runs the hook anyway when unsure, which is safe here. Whether the plugin validator accepts `if` and `onFailure` in a plugin's `hooks.json` is checked in the plan; the probe on 2026-10-22 showed it accepts `onFailure`.
- The internal 570-second limit sits under the 600-second hook timeout so that the block message is the hook's own, not the harness's generic "timed out".
- Working tree, not the staged snapshot: the hook fires before `git add` in `git add -A && git commit`, so the index is stale at that moment, and checking out the index into a temporary directory would run without the repo's installed dependencies and build caches. The gap left is a commit that deliberately stages only part of the pending changes.
- Facts established live on 2026-10-22 with a probe plugin under Claude Code 2.1.304: an exit-2 PreToolUse block stops the call under `bypassPermissions` and inside a subagent; `onFailure: "block"` stops the call when the hook times out; after a `cd` into a worktree the event's `cwd` is the worktree while `CLAUDE_PROJECT_DIR` stays the main checkout.
