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

### Evidence 2026-10-30 21:13

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 20.255s

OK
```

Per `CLAUDE.md`, each family was checked first in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` printing to stderr, every case also run through `deploy_gate.readings` and `_common.is_git_commit`, and every member that got past a hook went into the proving test, committed failing before the code changed (53d38ce). Members beyond the review's cases, all regressions from T11 unless noted: `case` after `function f()`, `f ()`, `() {`, `{ ... } always {`, `coproc {` and `repeat 1 {`; patterns `x|(y)` and `@(x|y)`; `diff <(case ...) <(...)`; `${x#*)}` (since T10, like `${x/)/y}`); and a family the review did not name, which both shells run: a redirect operator holding `&` or `|` (`>&1`, `&>f`, `>|f`, `2>&1`, `<&0`) left the reader at a command start, so `echo "$(echo a >&1 case x in a) "; git tag v1; echo " ; esac)"` opened a `case` that is not there and hid the tag. After a redirect's target the reader is no longer at a command start, and `>f case ...`, which bash reads as a command named `case` and zsh as a `case`, is blocked under the new rule.

Three changes to the tests beyond the failing commit's new test, each for a reason found while working. The ticket's Context says `case` as a head word raises; the red-guard case `echo "$(case case in case) echo a;; esac)"; git commit -am x` that T11 added uses `case` as the subject and as a pattern, both positions the reader models, so the rule raises on a `case` everywhere except the subject and a pattern, which keeps that test unchanged as the acceptance asks. T11's release-authorisation loop held two forms of the `"$(echo case)"` cost, the `git log --grep` one the Context names and `echo "$(echo case)"; git tag v1; echo "$(echo esac)"` beside it; both moved to their own assertion that the block names the `case`, in 53d38ce. And a timing case, 200 nested `"$(echo ${x:-"` blocked in under 5 s, was added after the fix, from the timing run below.

The fix, in `closing_paren`:

- A word start reads `case` (`word_at`) in every branch: at a command start it opens one; as the subject or a pattern it is read; anywhere else, including a redirect's target, it raises `Unmodelled` ("a `case` inside a substitution that is not at a command start it knows"), a kind of `Unreadable` that carries its reason as `Unclosed` does. A second head word other than `in` raises it too (`case x { ... }`), and the reader steps past `in` so its letters do not count as a pattern.
- Each `case` tracks whether its current pattern has started: a `(` before anything else is the optional paren, and any later `(`, such as a `$(...)`, a glob group or an extglob, raises `Unmodelled`. `;;`, `;&` and zsh's `;|` return a body to its patterns, read as one unit.
- A `<` or `>` before `(` is a process substitution, not a redirect, so the first word inside is at a command start. A redirect's target ends a command start.
- A `${...}`, after a run of `$` of any length since zsh's lexer takes a `$` before `{` as opening one, is read whole with `parameter_close`, and `parentheses_balance` checks its parentheses as bash 3.2 counts them, outside quotes and escapes: where they do not balance, the call raises `ShellsDiffer`.
- `deploy-gate` blocks `Unmodelled` with "deploy-gate does not read <reason>, so it cannot tell where the substitution ends or whether this Bash call runs a gated command", and `read_error` passes the reason to `red-guard`, `secret-guard` and `ticket-sync`.

Boundaries of the new code, probed the same way (48 cases): a `${...}` holding `(`, `)`, `)(`, `((a))`, a quoted or escaped parenthesis, a nested `$(...)` or a nested `${...}` holding `)`; runs of two to four `$` before `{` balanced and unbalanced, quoted and unquoted and in a heredoc body; `in(x)`, `in` after a newline, `in` before a newline and `(x)`, `case x in esac`, two `case` in a row, a nested `case` in a body, `;|` and `;&` before `(y)`, a comment before a pattern and before `esac`, a quoted or substituted subject, a subshell or a substitution in a body, `esac` after `;` or a newline with no `;;`; `< (`, `<(...) >f`, `>f;`, `2>&1;` and `>&2 &&` before a `case`, and `<f case`; `case` as an argument and `xcase`, `case-`, `case.txt` and `esac` as words. All are blocked or silent as bash and zsh run them, apart from the accepted cost (`echo "$(echo case)"`, blocked) and forms both shells reject or that run no tag. The probe found one fault in the first draft, fixed above: an even run of `$` before `{` (`$${x/)/y}`) skipped the `${...}` check, and zsh reads it as one. Every probe set from T10, T11 and the sixth review (`cases` 1 to 14) shows no `deploy-gate` miss.

Timing through `deploy_gate.readings` and `is_git_commit`, all under 2 s: the T11 set (nested and flat `$$(`, 70,000 nested unbalanced `$$(`, 200 nested `case`, 60,000 `case` words, 30,000 `;;`, 30,000 `((1))`, 50,000 `$[1]`, T10's 40 nested `$((echo "`), and for T12 200 and 40 nested `"$(echo ${x:-"`, 50,000 `${x}` in one substitution, 30,000 `(x)` patterns and a run of 100,000 `$` before `{`. 30,000 nested `${x:-` inside a substitution reaches Python's recursion limit at once, which `deploy-gate`, `red-guard` and `secret-guard` block. The T6, T7, T10 and T11 timing tests pass. `claude plugin validate .` passes with the same warnings as before this branch (untracked `.DS_Store` files).

The commit hooks still do not read a commit inside a double-quoted substitution or a heredoc body, the line kept in `docs/backlog.md` for its own change; every remaining "commit" miss in the probes is one.

Live check, 2026-10-30, first in this session, which loads the plugin from this checkout (`echo "$(case x in (a) echo hi;; x) echo matched;; esac)" "$(echo ${HOME:-none} | wc -c | tr -d ' ')"` ran and printed `matched 18`; `echo "$(echo a >&1 case x in a) "; git tag v1-live; echo " ; esac)"` was blocked by `red-guard`), then in headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` sessions, one Bash call per command, no `RELEASE_AUTHORIZED` and no marker. In a throwaway repo with `"gatedCommands": ["^git tag "]`, `"feedbackCommand": "echo boom-red; exit 1"` and a modified `app.py`:

| Command                                                                                                  | Result                                                                                                                                                                  |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `echo "$(case x in x) echo a;\| *) git tag v1;; esac)"`                                                  | blocked: "Blocked: '...' matches gated command pattern '^git tag '"                                                                                                     |
| `echo "$(repeat 1 case x in x) git tag v2;; esac)"`                                                      | blocked: "Blocked: red-guard could not read this Bash call (a `case` inside a substitution ...)"                                                                        |
| `echo "$(echo a >&1 case x in a) "; git tag v3; echo " ; esac)"`                                         | blocked: "Blocked: red-guard could not read this Bash call (a `case` inside a substitution ...)"                                                                        |
| `echo "$(echo ${x/)/y}; git tag v4)"`                                                                    | blocked: "Blocked: red-guard could not read this Bash call (bash and zsh end a substitution holding a `${...}` with an unbalanced parenthesis at different places ...)" |
| `echo "$(case x { x) echo a;; })"; git commit -am x; echo ")"`                                           | blocked: "Blocked: red-guard could not read this Bash call (a `case` whose subject is not followed by `in`) ..."                                                        |
| `echo "$(case x in (a) echo hi;; x) echo matched;; esac)" "$(echo ${HOME:-none} \| wc -c \| tr -d ' ')"` | ran: `matched 18`                                                                                                                                                       |
| `echo "$(cat <(echo a))"`                                                                                | ran: `a`                                                                                                                                                                |

`red-guard` runs first there, so `deploy-gate`'s own two new messages were checked in a second throwaway repo with `gatedCommands` alone: `echo "$(echo a >&1 case x in a) "; git tag v3; echo " ; esac)"` was blocked with "Blocked: deploy-gate does not read a `case` inside a substitution ..., so it cannot tell where the substitution ends or whether this Bash call runs a gated command", and `echo "$(echo ${x/)/y}; git tag v4)"` with "Blocked: bash and zsh end a substitution holding a `${...}` with an unbalanced parenthesis at different places ..., so deploy-gate cannot tell whether this Bash call runs a gated command". No tag was created and nothing was committed in either repo. The `case` reason was reworded after the live run, from "where it cannot tell a command starts" to "that is not at a command start it knows", so the `deploy-gate` sentence does not say "cannot tell" twice; the feedback run above is after that change.

### Verifier 2026-10-30 21:18

Verdict: reopen
Checks:

1. ticket integrity: ok (all frontmatter fields present, Evidence quotes the feedback command run; the change has no `plan.md`, so the seam is the one the ticket names, the hook scripts as subprocesses)
2. proving test present and meaningful: the test is added on this branch, drives `deploy_gate.py` and `red_guard.py` as subprocesses, and every one of its blocking cases exits 0 against the integration branch's hooks (both test methods fail there, first on `echo "$(case x in x) echo a;| *) git tag v1;; esac)"` and `echo "$(f() case x in a) echo "'";; esac)"; git commit -am x; echo "'"`). But the behaviour the ticket claims, that a `case` or `${...}` form the reader does not model inside a substitution blocks the call, does not hold when a backslash-newline splits the word: with a stub `git`, `/bin/zsh` runs the tag and `deploy_gate.py` exits 0 silently on `echo "$(ca\`+newline+`se x in x) git tag v1;; esac)"`, `echo "$(c\`+newline+`ase x in x) git tag v1;; esac)"`, `echo "$(case\`+newline+` x in x) git tag v1;; esac)"` and `echo "$(echo $\`+newline+`{x/)/y}; git tag v1)"` (bash 3.2 runs none of them). The integration branch misses them too, so they are not regressions, but they are in this ticket's family; the top-level reader joins the lines (`gi\`+newline+`t tag v1` and `echo "$(gi\`+newline+`t tag v1)"` are blocked), and `closing_paren`'s word start and `${` checks do not.
3. proving test run: exit 0, `Ran 3 tests in 7.204s OK` (the new DeployGateTests test, RedGuardTests.test_reworded_commits_are_recognised and the changed T11 test, run alone)
4. feedback command: exit 0, `Ran 86 tests in 20.290s OK` (`python3 -m unittest discover -s tests`)
5. acceptance: 4 of 4 checked, none failed. Proving test passes (check 3). Every other test passes; the test diff against the integration branch changes only the T11 loop, where `git log --grep "$(echo case)"; ...` and its `echo "$(echo case)"; ...` sibling move from "release authorisation" to "does not read a `case`", still exit 2, the second with its reason in the Evidence. The T6, T7, T10 and T11 timing cases pass under their 5 s limits in the feedback run. `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry and the README's `deploy-gate` paragraph both say a `case` form the gate does not read inside a substitution is blocked.
6. scope: ok (CHANGELOG.md, README.md, hooks/scripts/_common.py, hooks/scripts/deploy_gate.py, tests/test_hooks.py and the ticket)
7. tests intact: ok (no assertion deleted, nothing skipped; the one changed expected message is the cost the ticket accepts, still exit 2, reason recorded)

Reopen reason: `deploy-gate` passes a `case` or `${` that a backslash-newline splits inside a double-quoted substitution, which zsh joins and runs (`echo "$(ca\`+newline+`se x in x) git tag v1;; esac)"`, `echo "$(echo $\`+newline+`{x/)/y}; git tag v1)"`); join line continuations in `closing_paren`'s reading, or block them there, add these to the proving test first, and probe the backslash-newline family at every word and operator the reader checks (`case`, `in`, `esac`, `;;`, `;&`, `;|`, `<(`, `>(`, `$`-runs before `{`).
