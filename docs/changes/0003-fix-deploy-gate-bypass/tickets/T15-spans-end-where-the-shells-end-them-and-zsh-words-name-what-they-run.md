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
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_spans_end_where_the_shells_end_them_and_zsh_words_name_what_they_run: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming a quote left open on `` echo `: "`; git tag v1; echo "x" ``, `` x=`: "`; git tag v1; echo "x" ``, `` echo `echo "a`; git tag v1; echo `echo b"` ``, `` echo `: ''`; git tag v1; echo ''x'' `` and `` echo `echo \`echo ''a\``; git tag v1; echo `echo b''` ``; exits 2 naming bash and zsh on `(( y = ##'' )); git tag v1 # ''`, `(( y = ##" )); git tag v1 # "`, `echo $(( ##'' )); git tag v1 # ''`, `echo $[ ##'' ]; git tag v1 # ''`, `(( ${x/)/} + ##a )); git tag v1`, `(( ${x:-)} + ##a )); git tag v1`, `(( $''\'')'' + ##a )); git tag v1` and `setopt nonomatch; echo x(N)#y; git tag v1`; exits 2 naming release authorisation on `=git tag v1` and `{=git tag v1}`; and exits 0 silently on `echo $(( ${x:-1} + 1 ))`, `((echo ''a'') )`, `f() { :; }; f`, `echo a=b` and `x=$(echo a); echo "$x"`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `=git commit -am x`, `(( ${x/)/} + ##a )); git commit -am x` and `` echo `: "`; git commit -am x; echo "x" ``'
status: in-progress
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
