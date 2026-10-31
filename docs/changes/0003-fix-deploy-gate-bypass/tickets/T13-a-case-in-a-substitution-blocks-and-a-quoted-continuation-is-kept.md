---
id: T13
title: A case inside a substitution blocks the call, and a backslash-newline is deleted only where the shells delete it
blocked_by: [T12]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    README.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_case_in_a_substitution_blocks_and_a_quoted_backslash_newline_is_kept: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `bash -c ''echo a # x \` / `git tag v1''`, `bash -c $''echo a # x \` / `git tag v1''` and `eval ''cat <<"E"` / `x\` / `E` / `git tag v1` / `E''` (lines joined by a newline); exits 2 naming a `case` on `echo "$(case x in (x|esac) git tag v1;; esac)"`, `echo "$(case x in x|esac) git tag v1;; esac)"`, `echo "$(<<EOF case x in a) "; git tag v1; echo " ;; esac)"`, `echo "$([[ a || case == in ]] && echo a) "; git tag v1; echo " ;; esac)"` and `echo "$(case x in a) echo hi;; esac)"`; and exits 0 silently on `echo a # trailing \` / `ls`, `bash -c ''echo a \` / `&& ls''`, `sed ''/x/a\` / `y'' f`, `echo "$(cat case.txt)"` and `echo "$(echo ${x:-"\")"})"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `bash -c ''echo a # x \` / `git commit -am x''` and `eval ''cat <<"E"` / `x\` / `E` / `git commit -am x` / `E''`'
status: todo
---

## Context

From the seventh review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-31 of d0fb265"): the four Importants at `_common.py:507`, `:869`, `:921` and `:926`, the five Nits folded into this ticket at that review's gate, and the Decisions taken at that gate and at this ticket's. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

**The regression (`_common.py:507`).** T12 made `shell_source` read a call holding a backslash-newline twice, once with `joined(command)` and once as written, and return the joined reading when the two agree. `joined` deletes every unescaped backslash-newline, including inside `'...'` and `$'...'`, where bash and zsh keep it, and the agreement check runs `joined` over the written reading too, so it never sees that. A script handed to `bash -c`, `zsh -c` or `eval` then reaches its own reading without its backslash-newline, and a `#` comment or a quoted heredoc body in it swallows the next line: `bash -c 'echo a # x \`, newline, `git tag v1'` passes all four hooks, and both shells run the tag. `a7e72cc` blocked it.

Decided at this ticket's gate: a backslash-newline is deleted only where the written reading's own lexer finds it in unquoted text, double-quoted text or an unquoted heredoc body. Inside `'...'`, `$'...'` or a quoted heredoc body it is kept, as both shells keep it. At the end of a `#` comment it is kept and ends the comment, as both shells end it. A script passed to `bash -c` or `eval` then reaches its own `shell_source` call with the backslash-newline in place, and that call applies the same rule. Do not add a second quote scanner for this: one that misreads a `'` inside double quotes would skip a continuation the shells delete and hide `"$\`, newline, `(git tag v1)"`. Take the positions from `source_text`'s own pass over the written text. Keep the agreement check for the places where deleting a continuation moves where a quote, substitution, heredoc or comment ends.

`comment_end`'s block on a comment ending in a backslash stays only where bash and zsh part, inside a substitution. At the top level, `echo a # trailing \`, newline, `ls` is read as the shells read it, so the review's Nit at `_common.py:519` closes. Check that claim in both shells before relying on it.

Failing closed on any backslash-newline in single quotes was weighed and rejected. It would block `sed '/x/a\`, newline, `y' f`, `python3 -c '...'` with a continuation, and multi-line `bash -c` scripts in every project that has a `feedbackCommand`, since `red-guard` blocks any call it cannot read.

**The `case` tracking (`_common.py:869`, `:921`, `:926`).** Since T10, `closing_paren` decides where a substitution ends for every reader, so a `case` it opens or closes where the shells do not hides the text after the next `)`. Three Importants of this kind are in the seventh review, five in the sixth, and more in earlier rounds:

- `esac` read as the end of a `case` when it is a pattern word (`(x|esac)`)
- a `case` opened after a heredoc delimiter
- a `case` opened as an operand inside `[[ ... ]]`

Decided at this ticket's gate: any whole-word `case` (`word_at`) that `closing_paren` reaches raises `Unmodelled`, wherever it sits. That covers every `$(...)`, `<(...)` or `>(...)` span and the parentheses nested in them, quoted or not. Delete the `case` tracking and every piece of state that only it uses: the `cases` stack, the `head`, `pattern` and `body` phases, `;;`/`;&`/`;|`, the pattern `(` rules, and `in`/`esac`. That probably includes `COMMAND_LEADERS`, `command_start` and `target`, but check what else reads them before deleting. Word boundaries stay as `word_at` reads them, so these are not a `case`:

- `"$(cat case.txt)"`
- `"$(echo 'case')"`
- `"$(echo "case")"`

A `case` outside any substitution is still read by shlex as before. The reason string becomes "a `case` inside a substitution". The cost accepted at the gate: `x="$(case $1 in a) echo A;; esac)"` and `"$(echo case)"` are blocked by `deploy-gate` and by the commit hooks. Claude can rephrase with `if`, or move the `case` out of the substitution. So these existing assertions may change, still exit 2 or now exit 2, and no others:

- T12's silent forms at `tests/test_hooks.py:453-458`, which now block naming a `case`
- the `case` forms in T12's release-authorisation group at `:405-408`, which now name the `case`
- T12's red-guard `case` cases, which stay exit 2

The Evidence lists each change.

**The Nits, folded in:**

- `CHANGELOG.md` lines 10 and 12, the `red-guard` and `secret-guard`/`ticket-sync` entries, name the `Unmodelled` reasons: a `case` inside a substitution, and a backslash-newline that changes where a span ends.
- `deploy_gate.py:236`: the `Unmodelled` message no longer says "where the substitution ends", since a comment or heredoc raises it with no substitution involved.
- `parentheses_balance` (`_common.py:994`) skips a double-quoted span with `double_quoted`, not `find`, so `${x:-"\")"}` is not called read differently. Check in bash 3.2 and zsh first that both shells read it the same.
- The `f() { case ... }` Nit is covered by the new rule. It is now blocked by decision, which the CHANGELOG states.
- The `deploy_gate.py` module docstring and the `Unmodelled` class docstring name every reason that class carries.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing, staged in one call and committed in its own, before any code change. Per `CLAUDE.md`, before fixing, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` printing to stderr. A backslash-newline needs checking in each quoting and grammar context:

- unquoted, `"..."`, `'...'` and `$'...'`
- unquoted and quoted heredoc bodies
- a `#` comment at the top level and inside `$(...)` and `"$(...)"`
- inside `${...}`, backticks and arithmetic
- in the script of `bash -c`, `zsh -c` and `eval`

Probe each new or changed branch's boundaries the same way before handing it on. Add every member that gets past a hook to the proving test before the fix. The commit hooks' gap on a commit inside a double-quoted substitution or a heredoc body stays in `docs/backlog.md` for its own change, so the probes may show it; it is not this ticket's. The T6, T7, T10, T11 and T12 timing cases must still finish under their limits.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them and the assertions named in Context, each listed in the Evidence.
- The T6, T7, T10, T11 and T12 timing cases still finish under their limits.
- `closing_paren` holds no `case` state, and `joined` is not applied inside a single-quoted or ANSI-C span.
- `CHANGELOG.md` and the README's `deploy-gate` paragraph say a `case` inside a substitution blocks the call, and describe where a backslash-newline is deleted and where it is kept. The commit hooks' CHANGELOG entries name both `Unmodelled` reasons.
- The `deploy-gate` `Unmodelled` message and the docstrings named in Context match what the code raises.

## Evidence
