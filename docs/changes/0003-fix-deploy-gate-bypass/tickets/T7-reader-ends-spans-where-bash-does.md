---
id: T7
title: The shell reader ends quotes, heredocs and substitutions where bash does
blocked_by: [T6]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_reader_ends_quotes_heredocs_and_substitutions_where_bash_does: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `echo $''a\''b''; git tag v1; echo ''c''`, on `cat <<E''OF''`, `EOF`, `git tag v2` and `E` on four lines, on `cat <<E:OF`, `E:OF`, `git tag v3` and `E` on four lines, on ``echo `echo \`git tag v4\`` ``, and on `x="$( : # )`, `git tag v5` and `)"` on three lines, and exits 0 silently on `cat <<E''OF''`, `git tag v6` and `EOF` on three lines; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py blocks with the feedback output on `echo $''a\''b''; git commit -am x; echo ''c''` and on `cat <<E''OF''`, `EOF`, `git commit -am x` and `E` on four lines'
status: todo
---

## Context

From the third review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-25 of cd72334"): the Importants at `_common.py:167`, `_common.py:175`, `deploy_gate.py:198` and `deploy_gate.py:224`, and the Decisions taken at that review. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

Four places where the reader ends a span somewhere bash does not, so text bash runs is read as part of a quote, a heredoc body or the wrong substitution:

- `_common.QUOTED`, used by the fallback after shlex fails, reads `$'a\'b'` as the plain single-quoted `'a\'` and pairs every later quote wrongly. T4 (`d73214a`) introduced it: at `a90e0c2` the first case blocked. Read `$'...'` with backslash escapes before the plain `'...'` alternative, and take a backslash pair as one unit in `FALLBACK_TOKEN`'s unquoted branch.
- `_common.HEREDOC` ends the delimiter at the first character outside `[\w.-]` or at a closing quote. Bash's delimiter is the whole word after `<<`, up to whitespace or an operator, with its quotes removed, and it is quoted when any quote or backslash appears anywhere in it: `<<E'OF'` ends at a line `EOF` and its body is literal, and `<<E:OF` ends at `E:OF`.
- `deploy_gate.substitutions` ends a backtick span at the next backtick even when it is escaped. Inside backticks, `` \` `` is a nested backtick: skip it when looking for the close, and read the inner text with each `` \` `` turned into a backtick, so the nested substitution is found by the recursion.
- `deploy_gate.closing_paren` counts a `)` inside a `#` comment. Outside quotes, a `#` at the start of a word starts a comment that runs to the newline; skip it.

`red-guard` reads through the same `_common` functions, so the first two forms are pinned for it as well.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check each form's whole family in bash with a stub program before fixing it, not only the reported case: other characters in a delimiter (`<<"E"OF`, `<<\EOF`, `<<E\OF`, `<<-E'OF'`), other escapes inside `$'...'`, deeper backtick nesting, a `#` comment in a `$(...)` outside double quotes. Add every family member that gets past the gate to the proving test before the fix. A stub `git` function writes into `$x` when it runs inside `x="$(...)"`, so have it print to stderr.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry names the four forms.

## Evidence
