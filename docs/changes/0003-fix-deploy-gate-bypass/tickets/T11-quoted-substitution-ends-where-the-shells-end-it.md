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

### Evidence 2026-10-30 20:35

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
.....................................................................................
----------------------------------------------------------------------
Ran 85 tests in 18.708s

OK
```

Per `CLAUDE.md`, each family was checked first in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` printing to stderr, every case also run through `deploy_gate.readings` and `_common.is_git_commit`, and every member that got past a hook went into the proving test, committed failing before the code changed (c0205a3). Members beyond the review's cases: `case` as a word in `$case`, `case-x`, `${case}`, `a/case`, `case=1`, `x=case` and as a pattern (`case case in case)`); `<<<` with no space, a space, and each kind of quote; `<<` in `$(( (1) <<EOF ))` and `for ((i=1<<EOF; ...))`; `$$$$(`; and `$$(` and `$${` inside a double-quoted `${...}`.

Two changes to the test after that commit, both found while making it pass. The red-guard case `echo "$$(" ; git commit -am x ; echo ")"` was in the list that expects the feedback output, but the gate's decision makes it a call bash and zsh read differently, which red-guard blocks as unreadable: it moved to its own assertion that red-guard blocks it naming bash and zsh. And two cases were added for faults the boundary probe found in the first draft, below: `cat <<EOF`, `$$(git tag v1)`, `EOF` is silent, and 70,000 nested `"$$(` are blocked in under 5 s.

The fix:

- `closing_paren` reads command position as bash's grammar does: at the start of the span and after `;`, `&`, `|`, `(`, a newline or one of `!`, `{`, `do`, `elif`, `else`, `if`, `then`, `time`, `until`, `while`, and not after a word, an assignment or a redirect's target. `case` opens there only as a whole word (`word_at`, which ends a word at a metacharacter, replaces `keyword_at`), and each open `case` is tracked by depth through its head (subject and `in`), its patterns (where `esac` ends it and a `(` is the optional pattern paren) and its body (where `;;` or `;&` returns to patterns). It steps over `<<<` as one unit, and skips `((...))` and `$[...]` with `arithmetic_close`, which now takes either bracket pair, before testing for a heredoc.
- `double_quoted` and `parameter_close` take a run of `$` whole (`dollar_quoted`): after an odd run the last `$` can open a span, and after an even run a `(` or `{` is text, as both shells expand it. `literal_bracket_close` finds where bash's parser would close that bracket and checks that zsh's reading of the same text, as text (`read_as_text_reaches`), reaches it without ending the quote, or the `${...}` it is in; where they part, the call raises `ShellsDiffer`. Each answer is cached and a verified bracket is jumped over, and past 16 such brackets nested inside one another the call is `Unreadable`.
- A substitution or `${...}` inside double quotes that runs to the end of the call raises `Unclosed`, a kind of `Unreadable` that carries its reason: `deploy-gate` blocks it saying the substitution never closes, and `read_error` passes the reason to `red-guard`, `secret-guard` and `ticket-sync`. The backlog line is gone.
- `deploy_gate.substitutions` reads double-quoted text in `shell_source`'s output as quoted, since every substitution there already reached `spans` in T10, and takes a run of `$` whole, so `"$$(git tag v1)"` and the same line in an unquoted heredoc body, which neither shell runs, are silent.

Boundaries of the new code, probed the same way (75 cases): `case` after every leader word and operator, a quoted or substituted subject, `in` on its own line, blank lines before a pattern, `(x)`, `a|x)`, `*)` with no `;;` before `esac`, `;&`, a nested `case` in a body, `case` and `esac` as patterns, `echo esac` and `echo in` in a body, a `)` in a substitution or subshell in a body; `case` after `>f`, `<f`, `2>f`, `x=1`, `$(echo x)` and `;`, in a `#` comment, escaped, quoted, after `<<<` and in a heredoc body; `$[ 1 <<EOF ]`, nested `$[`, `$[ "]" ]`, `((1)) &&`, `((x = 1 << 2))` and nested subshells; runs of two to five `$` before `(`, `{`, a backtick, `\(` and a space, balanced and unbalanced, nested, and inside a double-quoted `${...}`; and the heredoc-body and double-quoted forms of `deploy_gate.substitutions`. All are blocked or silent as bash and zsh run them, except forms both shells reject (`if case ...` with no `then`, `;;&`, which neither has, a nested unbalanced `$$(`), which the hook blocks, and `while case ...`, which loops forever in zsh and which the hook blocks. The probe found two faults in the first draft, both fixed above: the check after `$${` inside `${...}` did not test the closing `}` itself, which closes zsh's `${...}`, and `deploy_gate.substitutions` still opened a span at the second `$` of `$$(` in double-quoted text and heredoc bodies. Every probe set from T10 and the fifth review (`cases` 1 to 4, 125 cases) still shows no `deploy-gate` miss.

Timing through `deploy_gate.readings` and `is_git_commit`, all under 1.8 s: 50 nested `"$$(` around 250,000 characters (an early draft was exponential here, and the cached draft after it took 55 s on 70,000 nested `$$(`, which the nesting cap fixed), 250 nested `$${`, 60,000 flat `$$(x)`, 70,000 nested unbalanced `$$(`, 200 nested `case`, 60,000 `case` words, 30,000 `;;` in one `case`, 30,000 `((1)) &&` and 50,000 `$[1]` in one substitution, and T10's 40 nested `$((echo "`. The T6, T7 and T10 timing tests pass. `claude plugin validate .` passes with the same warnings as before this branch (untracked `.DS_Store` files).

`red-guard` still does not read a commit inside a double-quoted substitution or a heredoc body (`echo "$$$(git commit -am x)"`, `cat <<EOF` / `$$$(git commit -am x)` / `EOF`), the line kept in `docs/backlog.md`.

Live check, 2026-10-30: first in this session, which loads the plugin from this checkout (`git log --grep "$(echo case)"; git tag v1-live; echo "$(echo esac)"` blocked by `deploy-gate`; `echo "$(echo case.txt)" "$$(echo hi)" "$${HOME}"` ran), then in a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, `"feedbackCommand": "echo boom-red; exit 1"`, a modified `app.py`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command. No tag was created and nothing was committed.

| Command                                                          | Result                                                                                                                                    |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `git log --grep "$(echo case)"; git tag v1; echo "$(echo esac)"` | blocked: "Blocked: '...' matches gated command pattern '^git tag '"                                                                       |
| `echo "$$(" ; git tag v2 ; echo ")"`                             | blocked: "Blocked: red-guard could not read this Bash call (bash and zsh end the double-quoted text holding $$( at different places ...)" |
| `echo "$(cat <<<EOF` / `)"; git tag v3; echo "x"` / `EOF`        | blocked: "Blocked: 'echo "$(cat <<<EOF ... matches gated command pattern '^git tag '"                                                     |
| `echo "$(echo hi`                                                | blocked: "Blocked: red-guard could not read this Bash call (a substitution inside double quotes never closes) ..."                        |
| `echo "$(cat case.txt 2>/dev/null)" && git commit -am x`         | blocked: "Commit stopped: the feedback command is red."                                                                                   |
| `echo "$$(echo hi)" "$${HOME}" "$(echo case)"`                   | ran: `<pid>(echo hi) <pid>{HOME} case`                                                                                                    |
