---
id: T12
title: A case or parameter form the reader does not model inside a substitution blocks the call
blocked_by: [T11]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    README.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_case_or_parameter_form_the_reader_does_not_model_blocks_the_call: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `echo "$(case x in x) echo a;| *) git tag v1;; esac)"` and `echo "$(cat <(case x in a) echo hi;; esac) ; git tag v1 )"`; exits 2 naming a `case` it cannot read on `echo "$(f() case x in x) git tag v1;; esac; f)"`, `echo "$(repeat 1 case x in x) git tag v1;; esac)"`, `echo "$(echo;\` / `case x in x) git tag v1;; esac)"` (lines joined by a newline), `echo "$(case x in ($(echo a)) echo hi;; esac; git tag v1)"`, `echo "$(case x in x(|y)) git tag v1;; esac)"` and `echo "$(case x { x) echo a;; })"; git tag v1; echo ")"`; exits 2 saying bash and zsh read it differently on `echo "$(echo ${x/)/y}; git tag v1)"`; and exits 0 silently on `echo "$(case x in a) echo hi;; esac)"`, `echo "$(case x in (a) echo hi;; esac)"`, `echo "$(cat <(echo a))"` and `echo "$(echo ${x:-a})"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `echo "$(f() case x in a) echo "''";; esac)"; git commit -am x; echo "''"` and `echo "$(case x { x) echo a;; })"; git commit -am x; echo ")"`'
status: in-progress
executed_by: single
branch: ticket/0003-T12
---

## Context

From the sixth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-30 of a7e72cc"): the five Importants at `_common.py:815`, `:861`, `:853`, `:850` and `:803`, all in the `case` tracking T11 added to `closing_paren`, and the Decisions taken at that review and at this ticket's gate. Since T10, `closing_paren` decides where a double-quoted substitution ends for every reader, so a `)` it takes as the end, or skips as a pattern's, hides the text after it. Four of the five are regressions from T11 (`74c8228` blocked every tag form); `case x { ... }` came in with T10. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

Decided at this ticket's gate, after four rounds of reviews finding `case` forms the reader did not model:

- `closing_paren` keeps its `case` tracking for the forms bash documents: `case` at a command position it knows, a head of the subject and `in`, an optional leading `(` on a pattern, `;;` and `;&`. Two forms are modelled because they are cheap and certain: zsh's `;|` returns a body to its patterns as `;;` does (bash rejects it), and the `(` of a process substitution `<(` or `>(` clears the redirect target, so the first word inside is at command position.
- Anything else around a `case` raises an `Unreadable` that carries its reason, as `Unclosed` does: a whole-word `case` (`word_at`) that the reader does not open at a command position it knows, wherever it sits, including as a redirect target or a head word; a `(` in a pattern after its first character (a `$(...)`, a zsh glob group, an extglob); a second head word other than `in` (zsh's and bash's `case x { ... }`). This covers zsh's `f() case`, `function f { case`, `() { case`, `repeat 1 case`, `coproc case`, `for i (1) case`, `foreach i (1) case` and a `case` after a backslash-newline, without a list of leaders to keep complete. `deploy-gate` blocks it with a message naming a `case` form it cannot read, not its too-long message, and `read_error` passes the reason to `red-guard`, `secret-guard` and `ticket-sync`. The cost, accepted at the gate: a bare `case` argument inside a substitution, such as `"$(echo case)"` or `"$(grep -w case f)"`, is blocked. So T11's assertion on `git log --grep "$(echo case)"; git tag v1; echo "$(echo esac)"` changes from the release-authorisation message to this one, still exit 2; that is the only existing assertion this ticket may change, and the Evidence says so.
- Found while cutting this ticket and taken into it: a `${...}` holding `)` inside a double-quoted substitution, `echo "$(echo ${x/)/y}; git tag v1)"` or `echo "$(x=${y:-)} ; git tag v1)"`, passes `deploy-gate`; zsh reads the `${...}` whole and runs the tag, bash 3.2 rejects the call, and `74c8228` misses it too. Inside `closing_paren`, read a `${...}` whole with `parameter_close`, and raise `ShellsDiffer` where bash's bracket count ends the span elsewhere, as T9 decided for every place the shells part.
- Left out, to its own change after 0.5.1: the commit hooks do not read a commit inside a double-quoted substitution or a heredoc body (`docs/backlog.md`). The probes show it as "commit" misses; they are not this ticket's.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` printing to stderr before fixing it, including each shell's own grammar (`repeat`, `coproc`, `foreach`, `for i (...)`, `function f {`, `f()`, `() {`, `{ } always { }`, `select`, `case x {`, `;|`, glob groups, extglob, `<(` and `>(`, `${...}` with `)`, `(`, `}` and quotes in each operator form), and probe each new branch's own boundaries the same way before handing it on: every branch of `closing_paren` is a possible bypass, and a fail-closed rule is a possible over-block of forms both shells run. Add every member that gets past a hook to the proving test before the fix. The T6, T7, T10 and T11 timing cases must still finish under their limits.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them and the one T11 assertion named in Context.
- The T6, T7, T10 and T11 timing cases still finish under their limits.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry and the README's `deploy-gate` paragraph say a `case` form the gate does not read inside a substitution is blocked.

## Evidence
