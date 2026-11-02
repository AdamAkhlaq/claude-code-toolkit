---
id: T15
title: A span ends where the shells end it, and a zsh glob group or `=word` is read as zsh reads it
blocked_by: [T14]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    README.md,
    docs/backlog.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_spans_end_where_the_shells_end_them_and_zsh_words_name_what_they_run: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming a quote left open on `` echo `: "`; git tag v1; echo "x" ``, `` x=`: "`; git tag v1; echo "x" ``, `` echo `echo "a`; git tag v1; echo `echo b"` ``, `` echo `: ''`; git tag v1; echo ''x'' `` and `` echo `echo \`echo ''a\``; git tag v1; echo `echo b''` ``; exits 2 naming bash and zsh on `(( y = ##'' )); git tag v1 # ''`, `(( y = ##" )); git tag v1 # "`, `echo $(( ##'' )); git tag v1 # ''`, `echo $[ ##'' ]; git tag v1 # ''`, `(( ${x/)/} + ##a )); git tag v1`, `(( ${x:-)} + ##a )); git tag v1`, `(( $''\'')'' + ##a )); git tag v1` and `setopt nonomatch; echo x(N)#y; git tag v1`; exits 2 naming release authorisation on `=git tag v1` and `{=git tag v1}`; and exits 0 silently on `echo $(( ${x:-1} + 1 ))`, `((echo ''a'') )`, `f() { :; }; f`, `echo a=b` and `x=$(echo a); echo "$x"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `=git commit -am x`, `(( ${x/)/} + ##a )); git commit -am x` and `` echo `: "`; git commit -am x; echo "x" ``'
status: done
executed_by: single
branch: ticket/0003-T15
---

## Context

From the ninth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-11-01 of a6f928f"): the six Importants at `_common.py:765`, `:1069`, `:1055`, `:727`, `deploy_gate.py:76` and `deploy_gate.py:10`, and the four Nits, all routed to this ticket at that review's gate. The fourth Nit, on `intent.md:77`, is fixed by the intent amendment that appended this ticket, so three are left here. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`. Every bypass below was confirmed in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git`, and `is_git_commit` is False on every commit form, so `red-guard`, `secret-guard` and `ticket-sync` miss them too.

**A backtick script that leaves a quote open (`_common.py:765`, a regression from T14).** The backtick branch of `source_text` keeps `shell_source(script)` in place of the span's text, so the commit hooks can read a commit inside it. `shell_source(': "')` returns `: "` without raising, so the outer text holds an open quote that `shell_tokens` pairs with a later quote, and everything between becomes one quoted word:

- ``echo `: "`; git tag v1; echo "x"`` reads as ``['echo', '`', ':', '`; git tag v1; echo x', '"']``, so it gets past the gate. Bash prints a syntax error for the span and then runs the tag. The `x=`, leading-span and newline forms, and ``echo `echo "a`; git tag v1; echo `echo b"` ``, do the same. `28f3cbb` blocked all of them as `Unclosed`.
- The `'` forms, ``echo `: '`; git tag v1; echo 'x'`` and the nested ``echo `echo \`echo 'a\``; git tag v1; echo `echo b'` ``, which zsh runs too, were already open at `28f3cbb` and `main`.

Decided at the tickets gate: raise `Unclosed` when a backtick span's script ends inside a quote. The reading stays in the text, because the commit hooks read it from the tokens. The check must also cover a nested span whose own script leaves a quote open.

**A quote inside arithmetic (`_common.py:1069` and `:687`, open since `28f3cbb`).** Inside `((...))`, `$((...))` and `$[...]`, zsh reads `'` and `"` as characters, as in the character code `##'`. Bash reads them as quotes. `arithmetic_at` and `source_text` read them as quotes, so the scan finds no close, the `((` is taken for two subshells, and the `#` after it is read as a comment that hides the line. These all get past the gate, and zsh runs the tag:

- `(( y = ##' )); git tag v1 # '`
- `(( 1 ' )); git tag v1 # '`
- `(( y = ##" )); git tag v1 # "`
- `echo $(( ##' )); git tag v1 # '`
- `echo $[ ##' ]; git tag v1 # '`
- `for (( i = ##'; i < 0; i++ )); do :; done; git tag v1 # '`

Decided at the tickets gate: a `'` or `"` inside `((...))`, `$((...))` or `$[...]` raises ShellsDiffer, because bash reads a quote there and zsh reads a character. This blocks `$(( "1" + 1 ))`, which bash accepts, and that cost is accepted. Apply the rule in `arithmetic_at`, `arithmetic_close` and `source_text`'s arithmetic and bracket states, so no reader treats such a `((` as anything else first.

**A `)` inside `${...}` or `$'...'` in arithmetic (`_common.py:1055`, open since `28f3cbb`).** `arithmetic_at` counts a `)` inside `${...}` or `$'...'`, so it takes `((` for two subshells and `##a` for a comment. The eighth review's `##a` finding therefore stays open for these forms:

- `(( ${x/)/} + ##a )); git tag v1` and `(( ${x:-)} + ##a )); git tag v1` get past the gate, and zsh runs the tag.
- `(( $'\')' + ##a )); git tag v1` gets past, and bash runs it.

Step over `${...}` with `parameter_close` and `$'...'` with `ansi_c_span` in `arithmetic_at`, as `source_text` does. Do the same in `arithmetic_close`: inside `$((`, the `${` check in `closing_paren` catches it today only by accident.

**A zsh glob group before `#` (`_common.py:727`, open since `28f3cbb`).** After any `(` of kind `""`, `source_text`'s `)` branch starts a word. That includes a `(` in the middle of a word, which zsh reads as a glob group, so a `#` straight after its `)` is read as a comment. To zsh it is part of the word. `setopt nonomatch; echo x(N)#y; git tag v1` gets past the gate, and zsh runs the tag. Bash rejects `x(` as a syntax error. Give a `(` that follows a character other than a metacharacter, `$`, `<`, `>` or `=` the same treatment as an array's `(`, so a `#` after its `)` raises ShellsDiffer. `f()` must keep its reading: probe `f()#x`, `f() #x` and `f()`, newline, `{ :; }` in both shells, and leave them as they are now unless a shell disagrees.

**zsh's `=word` (`deploy_gate.py:76`, open since `main`).** zsh's `EQUALS` option, on by default, expands an unquoted word `=name` at the start of a word to the path of the command `name`. So `=git tag v1` runs `/usr/bin/git tag v1`, and `{=git tag v1}` does too. The gate's basename check and `find_commit` do not know `=git`. Decided at the tickets gate: wherever a word is tested as a program name (in the gate's anchors and its `git`, `eval` and shell checks, and in `find_commit`), also test it with one leading `=` removed. Bash runs `=git` as a command named `=git`, so reading it as `git` over-blocks only a command no one has, and needs no ShellsDiffer. Probe `==git`, `\=git`, `'='git`, `x=git` in command position, and `=git` after `sudo`, `env` and `{`, in both shells, before relying on it.

**The docstring (`deploy_gate.py:10`).** The module docstring names the three `Unmodelled` reasons, but covers the `ShellsDiffer` ones only with "one bash and zsh read differently". That leaves `LITERAL_BODY_IN_SUBSTITUTION` and `HASH_AFTER_ARRAY` unnamed, though T14's Acceptance asked for every reason both carry. Name each reason `ShellsDiffer` and `Unmodelled` carry after this ticket, including the new arithmetic-quote and glob-group reasons.

**The Nits, folded in:**

- `README.md:76`, `CHANGELOG.md:9` and the `deploy_gate.py` docstring say a `case`, a `#` comment ending in a backslash, and a quoted heredoc body holding a backslash-newline block the call "inside a substitution". Inside a backtick span none of them blocks now: `` echo `case x in x) echo hi;; esac` `` exits 0. There is no bypass, since the span ends at its backtick either way. Say "a `$(...)`, `<(...)` or `>(...)` span" in all three places.
- `README.md:76` says "a word in quotes names no program", which no longer holds for a quoted brace. `brace_group_words` splits after quote removal, so `echo "{git" tag v1` is blocked. Name that over-block beside the brace-group sentence, in the README and in `CHANGELOG.md:9`.
- `CHANGELOG.md:9` does not record the two blocks T14 lifted inside a backtick span: a `#` comment ending in a backslash, and a quoted heredoc body holding a backslash-newline. Add one clause saying both are now read.

Seam: the hook scripts as subprocesses. Write the proving test first, and commit it failing (stage in one call, commit in its own) before any code change.

Per `CLAUDE.md`, before fixing, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` that prints to stderr. This includes the new line on span-end scans: probe `arithmetic_at`, `arithmetic_close` and the backtick branch with each construct holding the closing character (quotes, `${...}`, `$'...'`, backticks, `$(...)`, heredocs). Probe every step that rewrites or matches text in each context `CLAUDE.md` names. Add every member that gets past a hook to the proving test before the fix, and probe each new branch's boundaries the same way before handing it on.

The commit hooks' gap on a commit inside a double-quoted substitution or a heredoc body stays in `docs/backlog.md` for its own change. The T6, T7, T10, T11, T12 and T13 timing cases must still finish under their limits. Run the T14 timing rows again and record them.

Existing assertions this may change: none expected. Any existing assertion that changes is listed in the Evidence, with the reason.

Amended by the executor, 2026-11-01:

- **The `${...}` and `$'...'` forms block as read differently, not for release authorisation.** The probes showed the shells part on all three. Bash 3.2 counts the `)` in `${x/)/}` and reads `(( ${x/)/} + 1 ))` as nested subshells (`+: command not found`), while zsh reads it as arithmetic. Bash reads `$'\')'` as an ANSI-C quote, and zsh does not. So `arithmetic_end` raises ShellsDiffer on them, as `closing_paren` already does for an unbalanced `${...}` inside a substitution, and the proving sentence was amended in the test commit (1ecebcf).
- **More members, all fixed and in the proving test**, each getting past the gate at `a6f928f`:
  - backticks: ``echo `: $'a`; git tag v1; echo 'x'`` and `` echo `echo \`: "\``; git tag v1; echo "x" ``
  - glob groups: a `#` inside the group (`x(a|#b)`, and `x(#qN)` and `*(#qN)` with `extendedglob`); a space inside it (`x(a b)#y`); a group after `"x"`, `${x}`, `$x`, `~` or an escaped `\(`; nested and chained groups (`x((a)|b)#y`, `x(a)(b)#y`); a group inside `[[ ]]`
  - `=word`: `env =git`, `command =git`, `x=1 =git`, `true && =git`, `echo $(=git tag v1)` and `=bash -c 'git tag v1'`
- **The glob-group rule.** A `(` that does not start a word, and is not after `$`, `<`, `>` or `=`, opens a glob group, unless a `)` follows straight away as in `f()`. So does any `(` inside one. Inside a group, a `#` where a comment could start raises ShellsDiffer, and so does one straight after its `)`. The `((` arithmetic branch now needs a word start, so `x((1))#y` is a glob group too: zsh runs the tag after it, where the reader had taken `((1))` for arithmetic.
- **One scan per shell.** `arithmetic_at` and `arithmetic_close` are replaced by `arithmetic_end` and `bracket_close`. `bracket_close` reads arithmetic as bash does, or as zsh does, in one scan that records the close of every bracket it meets and where each quote and `${` is. `source_text` keeps those scans across a call, so a run of nested `((` holding quotes is read once. A first version decided each such `((` with a fresh scan: 2,000 nested `((echo 'a'` took 12.9 s in the gate against 0.04 s at `a6f928f`. With the cached scans that row of 10,000 levels takes 0.26 s.
- **Accepted costs, as the tickets gate decided.** `echo $(( "1" + 1 ))` and `(( x = 'a' ))` now block. `\=git` and `'='git` are read as `git`, though zsh does not expand them.
- **A follow-up found here.** On macOS's case-insensitive filesystem, `GIT tag v1` runs `git` in both shells and gets past the gate, at `a6f928f` too, and `=GIT tag v1` does the same in zsh. Matching program words case-insensitively changes how a consumer's patterns apply, so this ticket does not decide it: it is a line in `docs/backlog.md`, which this ticket's files now list.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them and assertions listed in the Evidence with the reason.
- The T6, T7, T10, T11, T12 and T13 timing cases still finish under their limits.
- A backtick span whose script ends inside a quote raises `Unclosed`, nested spans included.
- A `'` or `"` inside `((...))`, `$((...))` or `$[...]` raises ShellsDiffer in every reader that decides where arithmetic ends.
- `arithmetic_at` and `arithmetic_close` step over `${...}` and `$'...'`.
- A `#` straight after the `)` of a `(` that opens in the middle of a word raises ShellsDiffer, and `f()` reads as before.
- A word `=name` is tested as a program name both with and without its leading `=`, in `deploy-gate` and in `find_commit`.
- The `deploy_gate.py` module docstring names every reason `Unmodelled` and `ShellsDiffer` carry.
- `CHANGELOG.md` and the README's `deploy-gate` paragraph describe the new reading, and the three Nits are fixed as Context says.

## Evidence

### Evidence 2026-11-01 17:58

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
.........................................................................................
----------------------------------------------------------------------
Ran 89 tests in 24.579s

OK
```

**Probing before the fix.** Each family in Context was checked in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git` that prints to stderr: 34 backtick and arithmetic forms and 35 glob-group and `=word` forms. Every form that got past a hook went into the proving test, which was committed failing (1ecebcf). The gate failed first on ``echo `: "`; git tag v1; echo "x"``, exiting 0, and red-guard failed on `=git commit -am x`, also exiting 0.

**Shell facts from the probes:**

- A backtick span's script that leaves a quote open is a syntax error inside the span, and bash goes on to run the rest of the call.
- Bash 3.2 counts a `)` inside `${...}` within `((`. It reads `(( ${x/)/} + 1 ))` as nested subshells and `(( ${x:-(} + 1 ))` as `(: command not found`, where zsh reads both as arithmetic.
- Bash reads `$'\')'` inside `((` as an ANSI-C quote, and zsh reads it as `')`.
- zsh reads `'` inside `((` as a character (`bad math expression ... '1'`). Both shells accept `"1"` there, so `$(( "1" + 1 ))` is the accepted cost.
- zsh reads `x(N)`, `x(a b)`, `x(a|#b)` and `x((1))` as one word with a glob group, and a `#` straight after its `)` stays in the word. Bash rejects `x(` as a syntax error. `f()#x`, `f() #x` and `f()` with a newline then `{ :; }` define a function in both shells, with the `#` as a comment.
- zsh expands `=git` to the path of `git` after `env`, `command`, `exec`, `nohup`, `time`, an assignment and `&&`, and inside `$(...)`. It does not expand `==git`, `\=git` or `'='git`. Bash runs `=git` as a command named `=git`.

**The fix.**

- **Backticks.** `source_text` checks the reading it keeps for a backtick span with `quote_left_open` and raises Unclosed when it ends inside a quote. A nested span is checked when its own reading is made.
- **Arithmetic.** `arithmetic_end` decides where arithmetic ends, and whether a `((` is arithmetic, from bash's reading and, when a quote or `${` lies inside, zsh's reading too. It raises ShellsDiffer on a quote either shell reads as arithmetic, and on readings that end apart. `closing_paren` and `source_text` both use it, with `source_text` keeping the scans across the call. `source_text` also raises on a quote while inside arithmetic or `$[...]`, and checks each `$[` with `arithmetic_end`.
- **Glob groups.** `source_text` pushes a glob kind for a `(` in the middle of a word. A `#` inside the group where a comment could start, or straight after its `)`, raises ShellsDiffer. The `((` branch needs a word start.
- **`=word`.** `program_name` reads a word past one leading `=`. The gate's anchors and `find_commit` use it.

**Docs.**

- The `deploy_gate.py` docstring names every reason ShellsDiffer, Unclosed and Unmodelled carry.
- CHANGELOG and README describe the new reading. The three Nits are fixed as Context says.
- The `_common.py` docstrings for `source_text`, `closing_paren` and `find_commit` say what changed.

No existing assertion changed.

**Probe sweeps on the final code**, compared with the hooks at `a6f928f` extracted from git:

- **New families.** In the 69 family forms, the 78 boundary forms (each new branch's trigger inside single quotes, `$'...'`, double quotes, backticks, heredoc bodies, comments, `[[ ]]`, arithmetic and `case` patterns, with an escaped backslash before it and straight after `{`), and the ninth review's 20 forms, nothing gets past the gate except `=GIT tag v1`, the backlogged case-insensitive family. No commit is missed outside a double-quoted substitution.
- **T14's probe files** (236 forms) still give 0 gate bypasses. The only commit misses are in double-quoted substitutions, the gap `docs/backlog.md` keeps for its own change.
- **Earlier corpora.** The 657 cases from 0003's earlier sweeps give 2 misses, both `eval` of a variable (the README's known limit, missed at `a6f928f` too), and 0 changed results.
- **Over-blocks.** Of 39 everyday commands (arithmetic, zsh glob qualifiers such as `ls *(.)` and `ls **/*.py(N)`, arrays, functions, backticks, `=` in arguments, `=ls -la`, git, find, awk and sed), only `echo $(( "1" + 1 ))` and `(( x = 'a' ))` changed, both newly blocked, as decided.

**Timing.** These are gate (`readings`) and `is_git_commit` times, at the fix against `a6f928f`:

- Every T14 row is within 0.1 s of before.
- New rows: 10,000 `((echo 'a') ` take 0.23 s and 1.75 s (0.17 s and 1.73 s before). 10,000 nested `((echo 'a'` take 0.26 s and 2.36 s (0.19 s and 2.35 s before). 20,000 `(( ${x} ));`, 10,000 nested `(( ${x}`, 20,000 `x(N)`, 20,000 nested `x(`, 20,000 `` `: "a"` `` and 10,000 `$[ ${x} ]` are each within 0.15 s of before.
- 20,000 `=git status;` now reaches the gate's word budget (Unreadable), as 20,000 `git status;` would, since each `=git` is now read as `git`.
- A first version decided each quoted `((` with a fresh scan and took 12.9 s on 2,000 nested `((echo 'a'` against 0.04 s before. That is why `bracket_close` keeps its scans.
- The T6, T7, T10, T11, T12 and T13 timing tests pass.

`claude plugin validate .` passes, with the same `.DS_Store` warnings as before.

**Live check, 2026-11-01, on the final code.** Headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` sessions ran one Bash call per command, with no `RELEASE_AUTHORIZED` and no marker. The first used a throwaway repo with `"gatedCommands": ["^git tag "]`:

| Command                                     | Result                                                                                                                |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| ``echo `: "`; git tag v1; echo "x"``        | blocked: "a backtick span whose script leaves a quote open ..."                                                       |
| `(( y = ##' )); git tag v2 # '`             | blocked: "bash and zsh read a quote inside arithmetic differently ..."                                                |
| `(( ${x/)/} + ##a )); git tag v3`           | blocked: "bash and zsh end arithmetic holding a `${...}` ..."                                                         |
| `setopt nonomatch; echo x(N)#y; git tag v4` | blocked, by secret-guard first: "... a `#` inside or straight after a `(...)` that opens in the middle of a word ..." |
| `=git tag v5`                               | blocked: matches `^git tag `                                                                                          |
| `env =git tag v6`                           | blocked: matches `^git tag `                                                                                          |
| `echo $(( ${x:-1} + 1 ))`                   | ran: `2`                                                                                                              |
| `f() { echo f-ran; }; f`                    | ran: `f-ran`                                                                                                          |
| `((echo 'sub-ran') )`                       | ran: `sub-ran`                                                                                                        |
| ``x=`echo "it's"`; echo "x=$x"``            | ran: `x=it's`                                                                                                         |

The second used another throwaway repo with `"feedbackCommand": "echo boom-red; exit 1"` and a modified `app.py`:

| Command                                    | Result                                                                                                    |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `=git commit -am x`                        | blocked: "Commit stopped: the feedback command is red."                                                   |
| `(( ${x/)/} + ##a )); git commit -am x`    | blocked: "red-guard could not read this Bash call (bash and zsh end arithmetic ...)"                      |
| ``echo `: "`; git commit -am x; echo "x"`` | blocked: "red-guard could not read this Bash call (a backtick span whose script leaves a quote open) ..." |
| `echo $(( ${x:-1} + 1 ))`                  | ran: `2`                                                                                                  |

No tag was created and nothing was committed in either repo.

### Verifier 2026-11-01 18:02

Verdict: pass
Checks:

1. ticket integrity: ok. `id`, `title`, `blocked_by`, `files`, `proves`, `status: in-progress`, `executed_by` and `branch` are all present, and Evidence quotes a run of the feedback command.
2. proving test present and meaningful: ok. `DeployGateTests.test_spans_end_where_the_shells_end_them_and_zsh_words_name_what_they_run` is new, and `RedGuardTests.test_reworded_commits_are_recognised` gains 7 rows. Both run the hooks as subprocesses. With this branch's `tests/test_hooks.py` against the hooks of `change/0003-fix-deploy-gate-bypass`, both fail: ``0 != 2 : echo `: "`; git tag v1; echo "x"`` and `0 != 2 : =git commit -am x`. Row by row against the old gate, 40 of the 41 blocking rows exited 0 there (the double-quoted `$(( ##' ))` row was already blocked) and exit 2 here, and the 10 rows that must pass exit 0 under both. Stub-`git` probes confirm that zsh runs the tag on `x(N)#y`, `=git`, `(( y = ##' ))` and `(( ${x/)/} + ##a ))`, and bash runs it on ``echo `: "`; git tag v1``.
3. proving test run: exit 0, `Ran 2 tests in 5.758s OK`.
4. feedback command: exit 0, `Ran 89 tests in 25.620s OK`.
5. acceptance: 10 of 10 checked, none failed. (a) The proving test passes (check 3). (b) The test diff only adds; no existing assertion changed. (c) The timing `assertLess` cases pass in the feedback run. (d) The backtick rows, nested ones included, exit 2 with "leaves a quote open" (`Unclosed(QUOTE_IN_BACKTICKS)`). (e) A quote in `((`, `$((` and `$[` raises `QUOTE_IN_ARITHMETIC` through `arithmetic_end`, called from `closing_paren` and from `source_text`'s `((` and `$[` branches, and `source_text` also checks inside arithmetic. (f) `arithmetic_at` and `arithmetic_close` are replaced by `arithmetic_end`/`bracket_close`, which step over `$'...'` and `${...}` as each shell does and raise ShellsDiffer where the two end apart, per the executor's amendment. My probes confirmed that bash does not run the tag on the `${x/)/}` form. (g) The glob-group rows exit 2 naming bash and zsh, and `f() { :; }; f`, `f()#x` newline `{ :; }` and `echo x(N)` exit 0. (h) `program_name` strips one `=` and is used in `deploy_gate.readings` and `find_commit`. (i) The docstring names every ShellsDiffer, Unclosed and Unmodelled reason that `_common.py` raises. (j) CHANGELOG and README describe the new reading, and the three Nits (span wording, quoted-brace over-block, lifted backtick blocks) are in the diff.
6. scope: ok. The changed files are `CHANGELOG.md`, `README.md`, `docs/backlog.md`, `hooks/scripts/_common.py`, `hooks/scripts/deploy_gate.py`, `tests/test_hooks.py` and the ticket file, all within `files`.
7. tests intact: ok. `git diff change/0003-fix-deploy-gate-bypass...HEAD -- tests/` shows additions only, with no deletions, skips or loosened values.
