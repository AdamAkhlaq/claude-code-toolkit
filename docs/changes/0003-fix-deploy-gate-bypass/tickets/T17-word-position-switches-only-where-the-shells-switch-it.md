---
id: T17
title: Word position switches only where the shells switch it
blocked_by: [T16]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    README.md,
    docs/backlog.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_word_position_switches_only_where_the_shells_switch_it: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `echo $(:;;)#; git tag v1`, its `;&`, `;|` and `;;&` forms and `cat <(:;;)#; git tag v1`, and on `time -p((x=1<<E))`, `for i (a)((x=1<<E))` and `foreach i (a)((x=1<<E));end`, each followed by `git tag v1` and `E` on lines of their own; exits 2 naming bash and zsh on `x=(a <<E)` followed by `git tag v1` and `E` on lines of their own, `> (a|#b); git tag v1`, `! < (N)#y; git tag v1`, `>|(a)#y; git tag v1`, `>&(a|#b); git tag v1`, `echo x <<<(a|#b); git tag v1`, `<>(a|#b); git tag v1`, `echo $(echo a;#b); git tag v1`, `echo $(echo a|#b); git tag v1` and `cat <(echo a|#b); git tag v1`; and exits 0 silently on `f() { (echo a # c` newline `echo b) }`, `function f { (echo a # c` newline `echo b) }`, `case x in (x) (echo a # c` newline `echo b);; esac`, `case x in (x) echo a | (cat # c` newline `);; esac` and `x=$(echo a; # note` newline `)`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `echo $(:;;)#; git commit -am x` and `> (a|#b); git commit -am x`'
status: in-progress
executed_by: single
branch: ticket/0003-T17
---

## Context

From the eleventh review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-11-02 of f1448b5"): the nine Importants at `_common.py:644`, `:692`, `:683`, `:891`, `:636`, `:840`, `:607`, `:809` and `:830`, and the five Nits, all routed to this ticket at that review's gate. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`. Every form below was confirmed in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git`, against the hooks at `f1448b5` and at `19f6f8b`. Repro list: the review section's Important lines.

T16 added `WordPosition` to `_common.py`. It tracks whether the next word names a command, sits in `[[ ]]`, in a `case` pattern, or is a redirection's target, and `source_text` uses it to read a `(` that starts a word as a subshell or a glob group. Three findings are regressions from that model and five are bypasses in the same families that were already open.

**Regressions from T16.**

- **A case separator with no `case` open (`_common.py:644`).** `WordPosition.operator` enters pattern mode on every `;;`, `;&`, `;|` or `;;&`. Inside a `$(...)` or `<(...)` span with no `case`, the span's `)` is then read as a pattern's `)` and the `WORD` is never popped, so a `#` after it is read as a comment. `echo $(:;;)#; git tag v1`, its `;&`, `;|` and `;;&` forms, `echo $(echo a` newline `;;` newline `)#; git tag v1` and `cat <(:;;)#; git tag v1` get past every hook, and bash runs the tag. They were all blocked at `19f6f8b`.
- **A function body (`_common.py:692`).** After the `)` of `f()`, `pop("")` leaves argument position, so the `{` after it does not keep command position, and a word-start `(` in the body is read as a glob group. `function f {` does the same after the name. `f() { (echo a # c` newline `echo b) }`, `f () { (echo a; echo b # c` newline `) }` and `function f { (echo a # c` newline `echo b) }` are blocked as ShellsDiffer, though both shells run them.
- **A pattern's leading `(` (`_common.py:683`).** In `case x in (x) ...`, the leading `(` is pushed as a glob group, and `pop` restores pattern mode after its `)`, so the whole body until `esac` is read as pattern text. `case x in (x) (echo a # c` newline `echo b);; esac` and `case x in (x) echo a | (cat # c` newline `);; esac` are blocked, though both shells run them.

**Bypasses already open at `19f6f8b`.**

- **`<<` inside a bash array (`_common.py:891`).** `x=(a <<E)`, `git tag v1`, `E` on lines of their own, and its `x+=(` and `declare -a x=(` forms: bash 3.2 rejects only that line and runs the rest, and zsh rejects the whole script. The reader takes the `<<` for a heredoc and skips the lines.
- **A `(` that is a redirection's target (`_common.py:636`).** `WordPosition.argument()` ignores a pending target, so `> (a|#b); git tag v1`, `! < (N)#y; git tag v1`, `>|(a)#y; git tag v1` and `>&(a|#b); git tag v1` read as subshells, while zsh reads a glob group and runs the tag.
- **`<<<(`, `<>(` and `>&(` read as process substitution (`_common.py:840`).** `before in ("<", ">")` opens a `WORD` at a `(` after the last character of any redirection operator. `echo x <<<(a|#b); git tag v1` and `<>(a|#b); git tag v1` get past, and zsh runs the tag.
- **`time -p((` (`_common.py:607`).** `time -p((x=1<<E))`, `git tag v1`, `E` on lines of their own: bash runs the tag, and the `((` is read as a glob group whose `<<E` is a heredoc.
- **A `#` after an operator inside a span (`_common.py:809`).** bash 3.2 reads the `#` in `$(echo a;#b)` as part of a word and ends the span at the next `)`, while zsh reads a comment. `echo $(echo a;#b); git tag v1`, `echo $(echo a|#b); git tag v1`, `cat <(echo a|#b); git tag v1` and `x=$(if true;then :;fi;#b); git tag v1` get past, and bash runs the tag.

**Scope (`_common.py:830`).** T16 also opens arithmetic at a `((` straight after a `)`, which closes zsh's `for i (a)((x=1<<E))` and `foreach i (a)((x=1<<E));end`. The review gate decided to keep it: those two forms go into the proving test, and the backlog line about them is removed in the same commit.

**Assumed at the tickets gate, from the shells' behaviour and the conventions earlier rounds settled, cheap to reverse:**

1. A case separator enters pattern mode only while a `case` opened at that depth is still open: `WordPosition` counts the `case`s it opens per depth, `esac` or zsh's `}` closes one, and each bracket push saves the count and its pop restores it. Inside a `$(...)`, `<(...)` or `>(...)` span, a `case` already raises Unmodelled.
2. A pattern's leading `(` ends the pattern at its `)` when a blank, a newline or `;` follows, where bash and zsh both end it (`case x in (x) echo A;; esac` and `(x)` then a newline run `A` in both). When a word character or `|` follows, as in `(x)b)` or `(x)|y)`, bash rejects it and zsh reads the pattern on, so the `(` stays a glob group and a `#` there still raises ShellsDiffer.
3. The `)` of `NAME()` and the name after `function` keep command position, so the body's `{` and the `(` after it read as they do in command position.
4. A `<<` inside an array raises ShellsDiffer, as do the other forms the two shells part on.
5. A redirection's pending target is argument position. A `(` straight after `<` or `>` opens a process substitution only when that `<` or `>` is the start of its own `<(` or `>(` token. Any other `(` there, after `<<<`, `<>`, `>&`, `>|` or a blank, is the target and reads as a glob group.
6. After `time`, a `-p` word keeps command position, and a `((` glued to it is a candidate for arithmetic, like one glued to a reserved word.
7. Inside a `$(...)`, `<(...)` or `>(...)` span, a `#` straight after an operator character, with no blank or newline between, raises ShellsDiffer: bash reads it as part of a word and zsh as a comment. One after a blank or newline is still a comment.

**The Nits, folded in:**

- `CHANGELOG.md:10` and `:12`: say "a `case` inside a `$(...)`, `<(...)` or `>(...)` span", as `CASE_IN_SUBSTITUTION` now does.
- `_common.py:565`: `COMMENT_IN_SUBSTITUTION` gets the same span wording.
- `red_guard.py:78`: `only_bookkeeping` now takes `=git status` and `=git add -A` as bookkeeping. Say so in the red-guard bullet at `CHANGELOG.md:10`.
- `README.md:76`: add one sentence on `$[...]` ending at its own `]`, so `$[ $(echo "1") + 1 ]` runs.
- `_common.py:686`: `push(WORD)` zeroes `case_words` and `pop` does not restore it. Save and restore it with the rest of the state (assumption 1 may subsume this).

Seam: the hook scripts as subprocesses. Write the proving test first, and commit it failing (stage in one call, commit in its own) before any code change.

Per `CLAUDE.md`, before fixing, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` that prints to stderr. That includes each case separator, each redirection operator before `(` with and without a blank, `function NAME` and `NAME()` with `{` and with `(`, a pattern's leading `(` followed by each kind of character, and each operator before a `#` inside `$(...)`, `<(...)`, `>(...)`, backticks and `"$(...)"`. The new `CLAUDE.md` line on reader states applies to every state `WordPosition` switches on. Probe each switching token where its opener is absent, inside a `$(...)` that holds none, and across each bracket the reader pushes and pops. Run everyday forms that hold the state, such as function and `case` bodies, through the hooks. The reader-step and span-end lines apply to each changed match. Add every member that gets past a hook to the proving test before the fix, and every form newly blocked that both shells run to the silent list.

The commit hooks' gap on a commit inside a double-quoted substitution or a heredoc body stays in `docs/backlog.md` for its own change. The T6, T7, T10, T11, T12 and T13 timing cases must still finish under their limits. Run T16's timing rows again and record them.

Existing assertions this may change: none expected. Any existing assertion that changes is listed in the Evidence, with the reason.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them and assertions listed in the Evidence with the reason.
- The T6, T7, T10, T11, T12 and T13 timing cases still finish under their limits.
- A case separator switches `WordPosition` to pattern mode only while a `case` it opened at that depth is open, and a span's `)` always pops its own entry.
- `NAME()` and `function NAME` keep command position for the body. A pattern's leading `(` ends the pattern at its `)` where both shells end it there.
- A `<<` inside an array, and a `#` straight after an operator character inside a `$(...)`, `<(...)` or `>(...)` span, raise ShellsDiffer.
- A redirection's pending target is argument position, and only a `<(` or `>(` token opens a process substitution.
- `time -p` keeps command position, and a `((` glued to `-p` there is a candidate for arithmetic.
- `for i (a)((x=1<<E))` and `foreach i (a)((x=1<<E));end` are in the proving test, and their line is gone from `docs/backlog.md`.
- The `deploy_gate.py` module docstring names every new ShellsDiffer reason, as its raise site has it.
- The five Nits are fixed, and `CHANGELOG.md` and the README's `deploy-gate` paragraph describe the new reading.

## Evidence
