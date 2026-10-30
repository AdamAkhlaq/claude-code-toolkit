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
status: done
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

### Evidence 2026-10-30 18:19

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
....................................................................................
----------------------------------------------------------------------
Ran 84 tests in 15.392s

OK
```

Per `CLAUDE.md`, the family was checked first in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` printing to stderr, each case run through `deploy_gate.readings` and `_common.is_git_commit` as well, and every member that got past a hook went into the proving test, committed failing before the code changed (f98eb2d, then 5a59992 for the rest of the family). Members beyond the ticket's cases: ``"`echo '"'`"``, `"${x:-$(echo "'")}"`, ``"${x:-`echo "'"`}"``, `"${x:-${y:-"'"}}"`, an escaped backtick span inside a double-quoted backtick span, a backslash-newline before the substitution, and a `#` comment or a quoted-delimiter heredoc holding `"` inside `"$(...)"`. bash 3.2 rejects the last two, and a `case` inside `"$(...)"`, but zsh runs the gated command after them, so they are read as zsh reads them and blocked. In a double-quoted `${...}`, bash takes a `'...'` span as a quote and zsh as literal text; they end the span apart only when it holds `}`, `"`, a backtick or a `$(`, `${` or `$[`, which now raises `ShellsDiffer`.

The fix, in `_common`:

- `shell_source` reads each double-quoted string with `double_quoted`, which reads `$(...)` (`closing_paren`), a backtick span and `${...}` (`parameter_close`) in their own context, writes them back as an empty `$()` or `${}`, and appends each substitution's script to `spans`. Every flat reader after it, shlex included, sees no quote inside the string. `shell_source`'s own quote state now only tracks `'`.
- `closing_paren` and `keyword_at` moved from `deploy_gate.py` to `_common`. `closing_paren` reads `"` with `double_quoted`, so two-deep nesting works, skips backtick spans and `$'...'` spans (the `$'` check is now `ansi_c_span`, shared with `shell_source`), and reads a `((` whose inner `(` closes just before the outer `)` as arithmetic, where `<<` is a shift. `ansi_c_close` became `escaped_close(command, index, mark)` so backtick spans use it too.
- `deploy_gate.readings` reads every span `shell_source` collected, so `echo "$(echo "git tag v7")"` stays silent and `echo "$(git tag v1)"` is still caught.

Boundaries of the new code, probed the same way: backticks, `$'\''`, `$$'\''` and an escaped `"` inside `"$(...)"`; `"$(...)"` holding `"$(echo ")")"`; `$((...))` holding a heredoc, a quote, `2#1`, a nested `$((`, or a non-arithmetic `$((echo x) )`; `"${x:-{a}}"`, `"${x:-\}}"`, `"${x#"}"}"`, `"${x/'}'/a}"`, `"${x:-'\}'}"`, an unclosed `'` and three-deep `${`; `"a\"b'"`, `"a\\"`, `"#"`, and a heredoc on the line of a double-quoted substitution. All are blocked or silent as bash and zsh run them, apart from two the hook blocks that both shells reject (`"${x:-'`'}"`, `"${x:-'${y'}"`). The probe found two faults in the first draft, both fixed before this evidence: `"$(( 1 <<EOF\n))"; git tag v1\nEOF`got past because`closing_paren`read the shift as a heredoc (a regression against the flat reader, now in the proving test), and nesting`$((echo "`doubled the reading at every level, 20 levels taking 21 s, because a non-arithmetic`((`is read twice;`closing_paren` is now cached per call, and a 40-level case is in the proving test, which fails without the cache.

Timing through `deploy_gate.readings` and `is_git_commit`, all under 1.2 s: a 290,000-character double-quoted word of `a'`, 20,000 distinct `$()` and 50,000 backtick spans in one string, 100,000 `'` inside a double-quoted `${...}`, 200 nested closed `$((`, 100 nested `$(( "`. Deeper nesting (300 `"$(`, 2,000 `${`) is blocked as too long to read or by `RecursionError`, which every hook catches and blocks on. `claude plugin validate .` passes with the same warnings as before this branch (untracked `.DS_Store` files).

`red-guard` still does not read a commit inside a double-quoted substitution or a heredoc body, such as `echo "$(git commit -am x)"`: reading one needs `red_guard.py` and `commit_checkout` changed and the heredoc-body reader moved out of `deploy_gate.py`, so it did not fall out of this ticket's files, and its line in `docs/backlog.md` stays. A quote inside such a substitution no longer hides a commit after it, which `RedGuardTests.test_reworded_commits_are_recognised` pins.

Live check, 2026-10-30: first in this session, which loads the plugin from this checkout, then in a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, `"feedbackCommand": "echo boom-red; exit 1"`, a modified `app.py`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command. No tag was created and nothing was committed.

| Command                                                                | Result                                                                                                         |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `x="$(printf "%s" "a'b")"; git tag v1; y="$(printf "%s" "c'd")"`       | blocked: "Blocked: 'x="$(printf "%s" "a'b")"; git tag v1; ...' matches gated command pattern '^git tag '"      |
| `echo "${x:-'"'}"; git tag v2; echo "'"`                               | blocked: "Blocked: red-guard could not read this Bash call (bash and zsh read '"' inside "${...}" differently" |
| `echo "$(( 1 <<EOF` / `))"; git tag v3` / `EOF`                        | blocked: "Blocked: 'echo "$(( 1 <<EOF ... matches gated command pattern '^git tag '"                           |
| `x="$(printf "%s" "a'b")"; git commit -am x; y="$(printf "%s" "c'd")"` | blocked: "Commit stopped: the feedback command is red."                                                        |
| `echo "$(echo "'")"; echo "git tag v8"`                                | ran: `'` then `git tag v8`                                                                                     |

### Verifier 2026-10-30 19:25

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `DeployGateTests.test_a_substitution_inside_double_quotes_is_read_in_its_own_context` was added on this branch and drives `deploy_gate.py` as a subprocess. It holds every `proves` case (v1 to v6 blocked, v7 and v8 silent) and 5 new commands in `RedGuardTests.test_reworded_commits_are_recognised`, which asserts exit 2 and the feedback output. With the integration branch's `_common.py` and `deploy_gate.py` in a scratch copy, both tests fail (`AssertionError: 0 != 2 : x="$(printf "%s" "a'b")"; git tag v1; ...` and the same for `git commit -am x`). Each `proves` command, run on its own through both versions of the hook, gets past the base code and blocks or stays silent as claimed on this branch.
3. proving test run: 0, `Ran 2 tests in 3.138s OK` (both proving tests run on their own)
4. feedback command: 0, `Ran 84 tests in 17.178s OK`
5. acceptance: 4 of 4 checked, none failed. The proving test passes (check 3). The other tests pass, and the diff under `tests/` adds lines without removing any (51 to 52 test methods). The T6 and T7 timing tests, `test_the_gate_never_fails_open_on_a_long_or_nested_call` and `test_the_reader_ends_quotes_heredocs_and_substitutions_where_bash_does`, pass under their 5 s limits (2.53 s for both together). The `CHANGELOG.md` `[Unreleased]` `deploy-gate` entry now says "A `$(...)`, backtick span or `${...}` inside double quotes is read in its own quoting context".
6. scope: ok (`CHANGELOG.md`, `hooks/scripts/_common.py`, `hooks/scripts/deploy_gate.py`, `tests/test_hooks.py`, and the ticket)
7. tests intact: ok (no deleted lines under `tests/`, and no skip or expected-failure markers)
