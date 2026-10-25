---
id: T10
title: A substitution inside double quotes is read in its own quoting context
blocked_by: [T9]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_substitution_inside_double_quotes_is_read_in_its_own_context: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `x="$(printf "%s" "a''b")"; git tag v1; y="$(printf "%s" "c''d")"`, `echo "$(echo "''")"; git tag v2; echo "$(echo "''")"`, ``echo "`echo "''"`"; git tag v3; echo "`echo "''"`"``, `echo "$(echo "''")" ; echo '' #'' ; git tag v4`, `echo "$(echo "it''s")"; {git,tag} v5` and `echo "$(echo ''"'')"; git tag v6; echo "$(echo ''"'')"`, and exits 0 silently on `echo "$(echo "git tag v7")"` and `echo "$(echo "''")"; echo "git tag v8"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py blocks with the feedback output on `x="$(printf "%s" "a''b")"; git commit -am x; y="$(printf "%s" "c''d")"`'
status: in-progress
executed_by: single
branch: ticket/0003-T10
---

## Context

From the fourth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-25 of c96a43e"): the Important at `_common.py:237` and the Decision that it becomes its own ticket. This gap predates the round: every case in `proves` already got past the gate at `cd72334`. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

Inside double quotes, `$(...)` and backticks open a new quoting context: in `"$(echo "it's")"` bash reads `"it's"` as a double-quoted word inside the substitution, and the outer string closes at the last `"`. Every flat reader of the source keeps one quote state, so it sees the inner `"` close the outer string and the `'` open a single quote, and every boundary after it is misread: `shell_source` (which then misplaces a `#` comment and heredocs), `expand_braces` and `unquoted_positions`, shlex in `shell_tokens`, and the fallback lexer. `deploy_gate.closing_paren` already tracks quotes inside a substitution; the outer readers do not.

The approach: `shell_source` reads a `$(...)` or backtick span that opens inside double quotes with the full reader, to its matching close, in its own context (its own quotes, comments, heredocs and nested substitutions), hands the span's text to the substitution reader, and keeps an empty `$()` in its place in the source the flat readers see. The outer word then reads as bash quotes it, and `deploy-gate` still reads the span's commands, so the silent and blocking cases in `proves` both hold. A word whose value comes from a substitution, such as `"$(echo git)" tag v1`, stays a stated limit, as a word built from a variable is.

`red-guard` reads through `shell_tokens`, so the fix reaches it; reading a commit inside a double-quoted substitution (`echo "$(git commit -am x)"`) is a separate gap, recorded in `docs/backlog.md`, and out of this ticket's scope unless it falls out of the same code, in which case take that backlog line out in the same commit.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check the whole family in `/bin/bash` and `/bin/zsh` with a stub `git` printing to stderr before fixing (a quote of either kind inside `"$(...)"`, ``"`...`"`` and `"${x:-...}"`; nesting two deep; an escaped `` \` `` inside a double-quoted backtick span; a `)` or `#` inside the inner quotes; a heredoc inside the substitution; the same inside an unquoted heredoc body), and probe the new code's own boundaries the same way before handing it on. Add every member that gets past a hook to the proving test before the fix. The T6 budgets still apply: the span's text is charged once.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them.
- The T6 and T7 timing cases still finish under their limits.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry says a substitution inside double quotes is read in its own quoting context.

## Evidence
