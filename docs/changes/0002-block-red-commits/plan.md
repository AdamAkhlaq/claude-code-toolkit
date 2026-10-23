---
id: "0002"
slug: "block-red-commits"
status: accepted
execution: single
concurrency: 1
created: "2026-10-22"
---

# Plan: no commit lands while the feedback command is red

## Approach

All new behaviour lives in one script, `hooks/scripts/red_guard.py`, registered in `hooks/hooks.json` in the `Bash` PreToolUse group directly after `secret_guard.py`, with `"if": "Bash(git *)"`, `"timeout": 600` and `"onFailure": "block"`. It reuses `_common.py`: `read_event`, `tool_input`, `is_git_commit`, `load_config`, `first_match`, `git`, `block`. One helper is added to `_common.py`, `commit_checkout(event, command)`, which resolves the checkout a commit lands in (spec requirement 2); it lives in `_common` because change 0003 will move the existing hooks onto it.

Work happens in this order, each step a ticket:

1. **The gate.** `red_guard.py` recognises a `git commit`, loads `.claude/toolkit.json` and `feedbackCommand` from the project, runs the feedback command through the shell from the checkout root, and blocks on non-zero with the command, exit code and last 40 lines of combined output (requirements 1, 3, 6, 7, 8). Registered in `hooks.json` and given a README hooks-table row in the same ticket, because `test_every_hook_script_is_registered_and_documented` in `tests/test_components.py` turns red otherwise (requirement 14). In this ticket every commit with any pending change runs the check.
2. **The skip set.** Pending changes come from `git status --porcelain -z` (staged, unstaged, untracked not ignored, rename targets). When every one is a workflow document (`docs/`, `GLOSSARY.md`, `REVIEW.md` at the checkout root) or matches `testGlobs` via `first_match`, the feedback command does not run (requirements 4, 5).
3. **The checkout.** `_common.commit_checkout` takes the directory of `git -C <dir>`, else of a leading `cd <dir> &&`, else the event's `cwd`, else `CLAUDE_PROJECT_DIR`, resolved relative to the event's `cwd`, then `git rev-parse --show-toplevel`. `red_guard.py` reads config, pending changes and runs the feedback command there (requirement 2).
4. **Time limit and fault tolerance.** `run_feedback(command, cwd, limit)` starts the command in its own process group, and on passing `limit` (570 seconds in production) kills the whole group, so a hung `npm test` does not leave a `node` child behind, and returns a result the caller turns into the "cannot finish is red" block (requirement 9). `main` catches any unexpected exception: on a non-commit command it exits 0; on a commit it blocks with the error, which is what `onFailure` would do anyway but with a readable message (requirements 10, 11).
5. **The words.** `PHILOSOPHY.md` names `red-guard` in the "Skills advise, hooks enforce" row and its prose list; `agents/implementer.md` steps 6 and 7, `skills/verify/SKILL.md` and `skills/fix-bug/SKILL.md` step 7 say the hook enforces the rule, and fix-bug says why its failing-test commit passes (requirements 15, 16). The proving test is a new component test: every hook script is linked in PHILOSOPHY's "Enforced by" column. It also exposes that `ticket-sync` is missing there today; this ticket adds it to the "Artifacts are tool-agnostic" row, since it keeps the ticket files, the source of truth, in step with the code.
6. **The live proof.** Headless sessions with the plugin loaded from a clone, against a temporary repo with a `.claude/toolkit.json` whose feedback command can be flipped red and green: red source commit blocked (also under `--permission-mode bypassPermissions`), same commit lands on green, test-only red commit lands, `git add -A && git commit` is caught (the `if` filter fires on a compound command), commit from a worktree under `.claude/worktrees/` runs the feedback command there. Transcripts quoted in evidence; anything the unit tests missed gets a unit test (requirement 13).
7. **Release 0.5.0.** `plugin.json` to `0.5.0`, `CHANGELOG.md` `[Unreleased]` entries moved under `0.5.0`, unit tests and `claude plugin validate .` green (requirement 17). No tag in the ticket: `v0.5.0` is tagged after the PR merges, on the maintainer's go, through `deploy-gate`.

Before `/toolkit:review 0002`, `REVIEW.md` is added at the repo root from `templates/REVIEW.md`, adjusted to this repo (Markdown skills, stdlib Python hooks, the plugin validator), as its own workflow-document commit on the integration branch. It is not a ticket: it changes no behaviour of the plugin.

## Execution

`single`, concurrency 1. The seven tickets form one chain: T1 to T4 all edit `red_guard.py` and `tests/test_hooks.py`, so nothing could run in parallel. A general-purpose subagent declined to commit under the maintainer's global `CLAUDE.md` on 2026-10-22, and the `implementer` agent's last step is a commit. The maintainer gave one go for the whole implement run, covering local ticket commits and merges into `change/0002-block-red-commits` only; pushing, the pull request, the merge to main and the tag each wait for a separate go.

No ticket is a one-way door. Everything lands on a local branch; the tag, the only irreversible step, happens after merge and outside the graph.

## Seams

- **The hook script as a subprocess** (`run_hook` and `HookCase` in `tests/test_hooks.py`): a synthetic PreToolUse event on stdin, a temporary git repo, a configured feedback command such as `python3 -c "raise SystemExit(1)"`. Catches every decision, message, skip-set and checkout-resolution rule. Misses whether Claude Code fires the hook, honours exit 2, `if` and `onFailure`, and what `cwd` it really sends.
- **`red_guard.run_feedback(command, cwd, limit)` imported directly** in `tests/test_hooks.py`: catches the time limit and the process-group kill in about a second with `limit=1`. Misses the harness's own 600-second timeout, which the probe of 2026-10-22 covered.
- **The repo's shape rules** (`tests/test_components.py`): catches registration in `hooks.json`, the README row, and PHILOSOPHY naming every hook. Misses behaviour.
- **A headless Claude Code session** with the plugin loaded from a clone (`claude --plugin-dir . -p`), against a temporary repo. The one slow seam, because the outcome (Claude's commit is stopped in a real session, in any permission mode, from a worktree) can only be seen there. Run in T6 and re-run by its verifier; costs tokens, not in the feedback command.

## Interrogation

- **What could break?** A fault in `red-guard` could stop every commit, or with `onFailure: "block"` every Bash call. Contained three ways: the `if` filter keeps the hook off non-git commands, requirement 11's catch-all lets non-commits through, and the unit tests run on every ticket. Second: `is_git_commit` splits on whitespace, so `echo git commit` counts as a commit and runs the check; this matches the two existing commit hooks and is left as is. Third: a slow suite now runs twice per ticket, once in `verify` and once at commit; accepted in the spec.
- **Which step is riskiest?** T3, parsing a directory out of a shell string. Contained by parsing only the two leading forms (`git -C <dir>`, `cd <dir> &&`) and falling back to the event's `cwd` for everything else, which the probe showed is the shell's real directory; T6 checks the worktree case live.
- **Does red-guard guard this change's own commits?** No. The plugin is not loaded in the session doing the work, so the hook cannot block T1 to T7; the executor still runs the feedback command before every commit, as today.
- **Could someone who never saw the conversation implement this from the plan and tickets?** Yes: the spec's requirements are numbered and testable, each ticket names its requirements, seam and proving test, and the probe facts are recorded in the spec's Design notes.

## Rejected alternatives

- **A git pre-commit hook installed by `setup`.** Would also cover the maintainer's terminal commits, but the plugin cannot ship it, every consuming repo would need an install step, and the maintainer chose Claude's commits only.
- **Asking a human on red.** Nobody can answer in a headless or subagent run, so it would either block or open unpredictably.
- **Testing the staged snapshot in a temporary checkout.** Exact, but runs without the repo's installed dependencies and build caches, so consumer suites would go red for the wrong reason; and the index is stale under `git add -A && git commit`.
- **Folding the check into `secret-guard` or `ticket-sync`.** One hook, one rule: the README table, the PHILOSOPHY column and the block messages stay readable.
- **Caching a green result by tree hash.** Saves the second suite run but adds state that can go stale; not worth it before a slow suite has been seen.
- **An environment variable to shorten the time limit in tests.** An undocumented knob anyone could set in production; the imported `run_feedback` seam needs none.

No ADR: nothing here is a one-way door.

## Amendment 2026-10-23: review of 82106a2

Fixes from `review.md`, recorded against the spec's amendment of the same date. The entry in `hooks/hooks.json` drops `"if": "Bash(git *)"`. `_common.py` gains `shell_tokens` (a `shlex` tokeniser that splits control operators), `find_commit`, `git_options` and `same_repository`, and holds `DEFAULT_TEST_GLOBS` for both `lock-tests` and `red-guard`. Step 3's `commit_checkout` composes `cwd`, the leading `cd` and `git -C` as the shell does and falls back when the result is not a checkout. `run_feedback` writes output to a temporary file and waits for the process, not the pipe, so a background child left by a green command no longer holds the hook to the limit.
