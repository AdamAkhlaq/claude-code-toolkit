---
id: T11
title: A substitution inside double quotes ends where bash and zsh end it, or the call is blocked
blocked_by: [T10]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_substitution_in_double_quotes_ends_where_the_shells_end_it: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `git log --grep "$(echo case)"; git tag v1; echo "$(echo esac)"`, on `echo "$(cat <<<EOF` / `)"; git tag v1; echo "x"` / `EOF` and on `echo "$( ((1 <<EOF))` / `)" "a"; git tag v1 # "` / `EOF` (lines joined by newlines); exits 2 saying bash and zsh read it differently on `echo "$$(" ; git tag v1 ; echo ")"` and `echo "$${x" ; git tag v1 ; echo "}"`; exits 2 saying a substitution never closes on `echo "$(echo hi`; and exits 0 silently on `echo "$(cat case.txt)"`, `echo "$$(echo hi)"` and `echo "$${HOME}"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py blocks with the feedback output on `echo "$(cat case.txt)" && git commit -am x` and `echo "$( echo $((1 <<EOF)) x` / `)"; git commit -am x` / `EOF`'
status: in-progress
executed_by: single
branch: ticket/0003-T11
---

## Context

From the fifth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-30 of 74c8228"): the three Importants at `_common.py:722`, `_common.py:718` and `_common.py:588`, and the Decisions taken at that review and at this ticket's gate. Every one is a regression from T10: since T10, `closing_paren` and `double_quoted` decide where a double-quoted string ends for every reader, so a misread that used to make `deploy-gate` read more now hides the text after it. At `c96a43e` each bypass below was blocked. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

- `closing_paren` counts `case` and `esac` wherever `keyword_at` finds the word between non-word characters, so `case.txt`, `$case` or `echo case` inside `"$(...)"` makes it skip the real `)`. Count them only at command position: at the start of the span or after `;`, `&`, `|`, `(`, a newline or a reserved word, with only blanks between.
- `closing_paren` reads a heredoc at any `<<`, including inside a here-string `<<<` and a shift in `((...))`, `$((...))` or `$[...]` after the start of the span. Step over `<<<` as one unit, and skip `((...))`, `$((...))` and `$[...]` with `arithmetic_close` (or its bracket equivalent) before testing for a heredoc.
- `double_quoted` and `parameter_close` test for `$(`, `${` and a backtick one character at a time, so the second `$` of `$$` opens a substitution. Facts checked at this ticket's gate in `/bin/bash` 3.2 and `/bin/zsh`: inside double quotes both shells expand `"$$(echo hi)"` as the PID then a literal `(echo hi)`, and `"$${HOME}"` as the PID then `{HOME}`; an odd run, `"$$$(echo hi)"`, runs the substitution in both; ``"$$`echo hi`"`` runs the backtick span in both. They differ only where the bracket is unbalanced: bash's parser takes the `(` or `{` after an even run as opening a span and ends the string where that span closes, zsh at the next `"`. Decided at the gate: take a run of `$` whole with `dollar_run`; after an even run read the `(` or `{` as literal text, as both shells expand it, and raise `ShellsDiffer` only when reading it as bash's parser does would end the string elsewhere.
- Decided at the gate, from `docs/backlog.md`: a `$(...)`, backtick span or `${...}` inside double quotes that runs to the end of the call raises `Unreadable`, so any future overrun fails closed rather than hiding the rest of the call. The shells reject such a call, so blocking it costs nothing. `deploy-gate` blocks it with a message saying a substitution never closes, not its too-long message.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` printing to stderr before fixing it (`case`/`esac` as a word in arguments, file names, variables, after `;;`, after `in`, nested in a subshell; `<<<` with each kind of quote and a heredoc after it on the line; `<<` inside `((`, `$((` and `$[` at and after the start of the span; runs of one to four `$` before `(`, `{`, a backtick and a quote, balanced and unbalanced, inside `"..."` and inside a double-quoted `${...}`), and probe each fix's own boundaries the same way before handing it on, as `CLAUDE.md`'s rule on a reader whose answer decides what other readers skip asks: every branch of `closing_paren`, `arithmetic_close`, `double_quoted` and `parameter_close` is a possible bypass. Add every member that gets past a hook to the proving test before the fix. The T6, T7 and T10 timing cases must still finish under their limits.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them.
- The T6, T7 and T10 timing cases still finish under their limits.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry says a call whose double-quoted substitution never closes is blocked.

## Evidence
