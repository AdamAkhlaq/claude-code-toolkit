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
    docs/backlog.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_case_in_a_substitution_blocks_and_a_quoted_backslash_newline_is_kept: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `bash -c ''echo a # x \` / `git tag v1''`, `bash -c $''echo a # x \` / `git tag v1''` and `eval ''cat <<"E"` / `x\` / `E` / `git tag v1` / `E''` (lines joined by a newline); exits 2 naming a `case` on `echo "$(case x in (x|esac) git tag v1;; esac)"`, `echo "$(case x in x|esac) git tag v1;; esac)"`, `echo "$(<<EOF case x in a) "; git tag v1; echo " ;; esac)"`, `echo "$([[ a || case == in ]] && echo a) "; git tag v1; echo " ;; esac)"` and `echo "$(case x in a) echo hi;; esac)"`; and exits 0 silently on `echo a # trailing \` / `ls`, `bash -c ''echo a \` / `&& ls''`, `sed ''/x/a\` / `y'' f`, `echo "$(cat case.txt)"` and `echo "$(echo ${x:-"\")"})"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `bash -c ''echo a # x \` / `git commit -am x''` and `eval ''cat <<"E"` / `x\` / `E` / `git commit -am x` / `E''`'
status: done
executed_by: single
branch: ticket/0003-T13
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
- amended by the executor, 2026-10-31: three older assertions of the same kind, which the list above missed and which the gate decision changes in the same way, still exit 2: T5's `echo "$(case a in a) git tag v4;; esac)"` (`:217`) and T10's `echo "$(case x in x) echo "'";; esac)"; git tag v1; echo "'"` (`:340`), which now name the `case` instead of release authorisation, and T11's red-guard `echo "$(case case in case) echo a;; esac)"; git commit -am x` (`:834`), which now names the `case` instead of running the feedback command

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

### Evidence 2026-10-31 14:32

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
.......................................................................................
----------------------------------------------------------------------
Ran 87 tests in 23.684s

OK
```

As `CLAUDE.md` asks, each family was checked first in `/bin/bash` 3.2 and `/bin/zsh`, using a stub `git` that prints to stderr. Every member that got past a hook went into the proving test, which was committed failing before the code changed (1afe0e8). The proving test failed on its first case, `bash -c 'echo a # x \`+newline+`git tag v1'`, which exited 0, and red-guard failed on `bash -c 'echo a # x \`+newline+`git commit -am x'`, which also exited 0.

The probes found members beyond the review's cases:

- `zsh -c` and `eval` with a comment that ends in a backslash.
- `"$(bash -c '...')"` and `$(bash -c '...')`, where the single-quoted script sits inside a substitution.
- A regression of the same kind from T12: a quoted heredoc body holding a backslash-newline inside a double-quoted substitution, `echo "$(cat <<'E'`, `x\`, `E`, `git tag v1`, `E`, `)"`. zsh runs the tag, bash does not, and `d0fb265` let it through. It is in the test.

The shells' own behaviour, from the probes:

- Both keep a backslash-newline inside `'...'`, inside `$'...'` (zsh decodes it to a newline, bash keeps both characters), in a quoted heredoc body and at the end of a `#` comment. Both end that comment at its line at the top level, in `( )`, in `{ }` and in a `bash -c` or `eval` script.
- Inside `$(...)`, quoted or not, bash joins a comment that ends in a backslash with the next line and zsh does not. It is the same for a quoted heredoc body.
- Inside backticks, both shells join everything, single quotes included.

The fix:

- **`shell_source`.** It reads the call as written first. In that pass `source_text` records the backslash of each backslash-newline that ends a top-level `#` comment or sits in a top-level quoted heredoc body. The second reading deletes every other backslash-newline (`joined(command, kept)`), and the agreement check stays. When the two agree, the written reading is returned. That reading keeps a backslash-newline inside single quotes and `$'...'`, because `source_text` copies quoted text as it is. It also carries the written spans, so a `$(...)` script is read in turn with its own continuations. Heredoc bodies that expand are returned joined, as the shells join them.
- **`source_text`.** It tracks backtick spans and joins inside them, single quotes and `$'...'` included. It records each unquoted `$(`, `<(` and `>(`. A comment ending in a backslash, or a quoted body holding one, inside such a span or a backtick span raises `Unmodelled` or `ShellsDiffer`. `substitution_holds` checks this with a pointer that only moves forward, so each top-level span is measured once. A double-quoted backtick span's script is joined in `substitution_end`.
- **`closing_paren`.** Any whole word `case` raises `Unmodelled("a `case` inside a substitution")`. All the `case` state is deleted: `cases`, the phases, `;;`/`;&`/`;|`, the pattern `(` rule, `in`/`esac`, `command_start`, `target` and `COMMAND_LEADERS`. Nothing else read them. A comment ending in a backslash raises `Unmodelled` there, and a quoted heredoc body holding a backslash-newline raises `ShellsDiffer`.
- **`parentheses_balance`.** It skips a double-quoted span with `double_quoted`. Both shells run `echo "$(echo ${x:-"\")"}; git tag v1)"`, and it is now read and blocked for release authorisation, not as read differently.
- **`deploy-gate`.** The `Unmodelled` message is now "deploy-gate does not read <reason>, so it cannot tell whether this Bash call runs a gated command".
- **Docs.** The `deploy_gate.py` and `Unmodelled` docstrings name every reason. `CHANGELOG.md` and the README describe the `case` block and where a backslash-newline is kept, and the commit hooks' CHANGELOG entries name both new reasons.

Four changes to existing assertions, each still exit 2, all from the gate's decision that any `case` blocks:

- T12's release-authorisation group (`;|`, `<(case`, `>(case` and `diff <(case`) and its six silent `case` forms moved into its `case` group.
- T5's `echo "$(case a in a) git tag v4;; esac)"` moved to its own assertion naming the `case`.
- T10's `echo "$(case x in x) echo "'";; esac)"; git tag v1; echo "'"` moved to its own assertion naming the `case`.
- T11's red-guard `echo "$(case case in case) echo a;; esac)"; git commit -am x` moved from the feedback-command loop to the red-guard `case` loop.

Context listed the first. The other three were amended into Context by me, the executor, as the same kind.

Probes:

- **Earlier probe sets.** Every probe set from T10 to T12 and the sixth review (`cases` 1 to 18, 506 cases) shows no `deploy-gate` miss and no change in exit code from `d0fb265`.
- **Reviewers' probe files.** The seventh review's bugs and security probe files (87 cases) show one miss, `x='# \`+newline+`git tag v1'; eval "echo $x"`. That is a command built from a variable, which the README states as a limit, and `d0fb265` misses it too.
- **Boundaries of the new code (64 cases).** These cover:
  - backtick spans with single quotes, `$'...'`, `eval`, `bash -c` and a quoted heredoc inside
  - a comment ending in a backslash after a `$(...)`, `"$(...)"`, backtick span or `<(...)` that has closed, and inside `<(`, `>(` and an unclosed `$(`
  - such a comment in `{ }`, `f() { }` and `if`, and after `$$(`, `$((...))` and `${x:-$(...)}`
  - runs of one to three backslashes at a comment's end
  - quoted heredocs with `<<-'E'`, `<<\E` and `<<"E"`, two heredocs on one line, one never closing, and one inside `<(...)`
  - double-quoted `bash -c` and `eval` scripts, and `sh -c`
  - `case` as `ca'se'`, `\case`, after an assignment, nested, unquoted, in a backtick, as `cases`, `Case`, in a comment and in a heredoc body
  - `${...}` holding an escaped or quoted parenthesis, `')'` or `\)`

  All of these are blocked or silent as the shells run them, apart from accepted costs and forms the shells reject. The same eval-of-a-variable form misses, as at `d0fb265`. The over-blocks:
  - a quoted heredoc with a continuation inside backticks, where both shells join
  - two heredocs on one line where only the unquoted one's continuation moves its end
  - `x=1 case` and a nested `"$(... "$(case ...)")"`, under the rule that any `case` blocks

- **Commit hooks.** `is_git_commit` now finds the commit in `bash -c 'echo a # x \`+newline+`git commit -am x'` and in the quoted-heredoc `eval` form, which it missed at `d0fb265`. It also reads `echo a # x \`+newline+`git commit -am x` and the top-level quoted heredoc form, which `d0fb265` called unreadable.

Timing, through `deploy_gate.readings` and `is_git_commit`:

- The T11 and T12 sets are all under 2.2 s.
- 20,000 `$(a) # x \` lines take 0.58 s in the gate.
- 50,000 nested `$(` before such a comment takes 0.15 s.
- 40,000 continuations in single quotes take 0.56 s, and in a backtick span 0.08 s.

The first draft of `substitution_holds` checked every recorded span at every comment, which is quadratic. The 20,000-line case did not finish in 10 minutes, and that is why the pointer exists. `is_git_commit` takes 6 s on 20,000 lines and 13 s on 30,000 heredocs, the same as `d0fb265` on the same inputs without continuations (6.08 s and 13.14 s). The cause is `find_commit`, which copies the rest of the token list at every token. It is not this ticket's, so it is recorded in `docs/backlog.md`, now in this ticket's files. The T6, T7, T10, T11 and T12 timing tests pass. `claude plugin validate .` passes with the same warnings as before this branch (untracked `.DS_Store` files).

Live check, 2026-10-31. I ran headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` sessions with one Bash call per command, no `RELEASE_AUTHORIZED` and no marker. The first ran in a throwaway repo with `"gatedCommands": ["^git tag "]`:

| Command                                                      | Result                                                                                                                                                                      |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bash -c 'echo a # x \` / `git tag v1'`                      | blocked: "Blocked: 'bash -c 'echo a # x \ ..." (matches `^git tag `)                                                                                                        |
| `echo "$(case x in (x\|esac) git tag v2;; esac)"`            | blocked: "Blocked: deploy-gate does not read a `case` inside a substitution, so it cannot tell whether this Bash call runs a gated command. Rephrase it or split the call." |
| `eval 'cat <<"E"` / `x\` / `E` / `git tag v3` / `E'`         | blocked: "Blocked: 'eval 'cat <<"E" ..." (matches `^git tag `)                                                                                                              |
| `echo "$(cat <<'E'` / `x\` / `E` / `git tag v4` / `E` / `)"` | blocked: "Blocked: bash and zsh end a quoted heredoc body holding a backslash-newline inside a substitution at different places ..."                                        |
| `echo a # trailing \` / `echo live-ran`                      | ran: `a`, `live-ran`                                                                                                                                                        |
| `printf '%s\n' 'line \` / `two'`                             | ran: `line \`, `two`                                                                                                                                                        |
| `echo "$(echo ${x:-"\")"})"`                                 | ran: `")`                                                                                                                                                                   |

The second ran in another throwaway repo with `"feedbackCommand": "echo boom-red; exit 1"` and a modified `app.py`:

| Command                                       | Result                                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `bash -c 'echo a # x \` / `git commit -am x'` | blocked: "Commit stopped: the feedback command is red."                                          |
| `echo "$(echo case)"`                         | blocked: "Blocked: red-guard could not read this Bash call (a `case` inside a substitution) ..." |
| `echo a # trailing \` / `echo live-ran`       | ran: `a`, `live-ran`                                                                             |
| `sed -n '1a\` / `added' app.py`               | ran: `added`                                                                                     |

No tag was created and nothing was committed in either repo.

### Verifier 2026-10-31 14:35

Verdict: pass
Checks:

1. ticket integrity: ok. `id`, `title`, `blocked_by`, `files`, `proves`, `status: in-progress`, `executed_by` and `branch` are present, and the Evidence quotes a feedback command run.
2. proving test present and meaningful: ok. `DeployGateTests.test_a_case_in_a_substitution_blocks_and_a_quoted_backslash_newline_is_kept` is new on this branch (1afe0e8), runs `deploy_gate.py` as a subprocess, and covers every form `proves` names. The `RedGuardTests.test_reworded_commits_are_recognised` additions sit in the loop that asserts the feedback command ran (`boom`). I ran both tests against the integration branch's hooks with this branch's `tests/test_hooks.py`, and both fail there: `AssertionError: 0 != 2 : bash -c 'echo a # x \`.
3. proving test run: exit 0, `Ran 2 tests in 4.560s OK` (both tests targeted with `python3 -m unittest -v`).
4. feedback command: exit 0, `Ran 87 tests in 23.799s OK` (`python3 -m unittest discover -s tests`).
5. acceptance: 6 of 6 checked, none failed.
   - Proving test passes: see check 3.
   - Other tests pass unchanged, apart from the listed changes: the full suite passes. The test diff changes only the assertions that Context names, including the three the executor amended in. Each one still exits 2 and now names the `case`.
   - Timing: all 11 `assertLess(time.monotonic() ...)` cases pass within the green suite.
   - `closing_paren` holds no `case` state: confirmed in the diff. `cases`, the phases, `COMMAND_LEADERS`, `command_start` and `target` are gone, and only a `word_at(..., "case")` raise is left. The returned reading never applies `joined` inside quotes: `shell_source("echo 'a\\\nb'")` and `shell_source("echo $'a\\\nb'")` keep the backslash-newline. It is joined only inside a backtick span, and I confirmed in `/bin/bash` and `/bin/zsh` that both shells join it there (`ab`). The joined reading is only used for the agreement check.
   - CHANGELOG and README: the `deploy-gate` entry and README paragraph describe the `case` block and where a backslash-newline is deleted and where it is kept. The `red-guard` and `secret-guard`/`ticket-sync` entries name both `Unmodelled` reasons.
   - Message and docstrings: the `Unmodelled` message no longer mentions a substitution. The `Unmodelled` docstring names all three reasons raised (`_common.py:518`, `:634`, `:902`, `:931`). The `deploy_gate.py` docstring names the `case` and the backslash-newline reasons. It covers the comment ending in a backslash inside a substitution only through "one bash and zsh read differently", which is accurate but does not name it.
6. scope: ok. Every changed file is in `files` or is the ticket itself.
7. tests intact: ok. Every removed assertion line reappears in another assertion that still expects exit 2, and the reason for each is recorded in Context. No skip or expected-failure markers were added, and no timing limit was loosened.

Reproduced independently:

- In both shells, a top-level comment ending in a backslash ends at its line, and a `bash -c` single-quoted script keeps the continuation.
- In bash 3.2 and zsh, `echo "$(echo ${x:-"\")"}; git tag v1)"` runs the tag.
- With `eval "echo a # x \`, newline, `git tag v1"`, neither shell runs the tag, and the gate is silent on it.
- The gate blocks `echo "$(echo case)"` and `x="$(case $1 in a) ...)"`, naming the `case`. It is silent on `"$(echo 'case')"`, `"$(echo "case")"` and `"$(cat case.txt)"`.
