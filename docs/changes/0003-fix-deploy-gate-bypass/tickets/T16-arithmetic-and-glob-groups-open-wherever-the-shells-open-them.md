---
id: T16
title: Arithmetic and glob groups open wherever the shells open them
blocked_by: [T15]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    hooks/scripts/red_guard.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    README.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_arithmetic_and_glob_groups_open_wherever_the_shells_open_them: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `if((x=1<<E));then :;fi`, `while((0<<E));do :;done`, `for((i=0;i<1<<E;i++));do :;done`, `!((0<<E))` and `{((x=1<<E))}`, each followed by `git tag v1` and `E` on lines of their own, and on `echo $[ $(: ]; echo 1) + ##a ]; git tag v1`; exits 2 naming bash and zsh on `{(( 1 '' )); git tag v1; } # ''`, `repeat 1 {(( 1 '' )); git tag v1; } # ''`, `f(){(( 1 '' )); git tag v1; }; f # ''`, `[[ a == (a)#y ]]; git tag v1`, `[[ a == (a|#b) ]]; git tag v1`, `setopt nonomatch; echo (a|#b); git tag v1` and `setopt nonomatch; print -r -- (N)#y; git tag v1`; and exits 0 silently on `echo $[ $(echo "1") + 1 ]`, `if((1));then echo y;fi`, `(echo a) # note`, `[[ (a == a) ]] && echo y` and `echo x(N)`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `if((x=1<<E));then :;fi`, `git commit -am x` and `E` on lines of their own'
status: todo
---

## Context

From the tenth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-11-01 of 19f6f8b"): the four Importants at `_common.py:715`, `:748`, `:728` and `deploy_gate.py:11`, and the three Nits, all routed to this ticket at that review's gate. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`. Every bypass below was confirmed in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git`, and `is_git_commit` is False on every commit form, so `red-guard`, `secret-guard` and `ticket-sync` miss them too.

**A `((` glued to a reserved word or to zsh's `{` (`_common.py:715`, a regression from T15).** T15 made `source_text`'s `((` branch need `starts_word`, so that `x((1))#y`, a zsh glob group, is not taken for arithmetic. But bash and zsh also open arithmetic at a `((` straight after a reserved word, and zsh after its word-starting `{`. There the `((` now falls through to the glob kind, a `<<` inside it is read as a heredoc, and a quote inside it pairs with a later one:

- `if((x=1<<E));then :;fi`, newline, `git tag v1`, newline, `E` gets past the gate, and bash runs the tag. So do its `while((`, `for((` and `!((` forms. `a6f928f` blocked all four.
- `{((x=1<<E))}` in the same shape gets past, and zsh runs it. Also blocked at `a6f928f`.
- `{(( 1 ' )); git tag v1; } # '`, its `"` form, `{{((`, `{(( 1 ' ))};`, `repeat 1 {((` and `f(){((` get past, and zsh runs the tag. These were open at `a6f928f` too.

Decided at the tickets gate: a `((` is a candidate for arithmetic at a word start, and also straight after a reserved word or after a run of zsh's `{`, with no space between. Elsewhere in a word it stays a glob group. Before relying on the list of reserved words, probe each one in both shells, glued to `((`: `if`, `elif`, `then`, `else`, `while`, `until`, `do`, `for`, `!`, `time`, `repeat`, `{`, `}`, and `f()`. Use the same position test for the candidacy that `keyword_position` uses for `case`, extended to reserved words.

**A `]` inside a `$(...)` nested in `$[...]` (`_common.py:748`, open since `a6f928f`).** `brackets` is a bare counter, so a `]` inside the nested substitution closes the `$[`, and the `#` of `##a` after it is read as a comment. `echo $[ $(: ]; echo 1) + ##a ]; git tag v1` gets past the gate, and zsh runs the tag. `arithmetic_end(command, index + 1, "[]")` at line 743 finds the right `]` and drops it. The same counter makes T15's new quote check fire on a quote inside a nested substitution, so `echo $[ $(echo "1") + 1 ]` is blocked, though both shells accept it (the first Nit).

Decided at the tickets gate: push `$[` onto `parens` as arithmetic, closed by its own `]`, and delete the `brackets` counter. Then a nested `$(...)` is a `WORD` on top of it, its `]` does not count, and the quote check does not fire inside it.

**A `(` at the start of an argument word (`_common.py:728`, open since `a6f928f`).** zsh reads a `(` that starts a word in argument position as a glob group, and so does a `(` that starts a pattern word inside `[[ ]]`. T15 gave the glob kind only to a `(` in the middle of a word, so these get kind `""`: the `)` starts a word, and a `#` after it, or after `|` inside it, is read as a comment. All of these get past the gate, and zsh runs the tag:

- `[[ a == (a)#y ]]; git tag v1` and `[[ a == (a|#b) ]]; git tag v1`, with no option set
- `setopt nonomatch; echo (a|#b); git tag v1`
- `echo ((a)|b)#y; ...`
- `print -r -- (N)#y; ...`
- `setopt extendedglob nonomatch; echo (#i)x; ...`

Decided at the tickets gate: give the glob kind to a word-start `(` in argument position. That is a `(` after another word of the same simple command that is not a reserved word, or a `(` inside `[[ ]]` after `==`, `!=`, `=` or `=~`. A `(` in command position keeps its subshell reading, and so does a grouping `(` inside `[[ ]]` after `[[`, `!`, `&&`, `||` or another `(`. Probe both readings in both shells before relying on them: `(a)#x` at command position, `[[ (a == a) ]]#x`, `[[ ! (a == b) ]]`, `if (a); then`, `time (a)` and `{ (a) }`.

**The docstring (`deploy_gate.py:11`).** The docstring's phrase "a `'...'` span or an unbalanced bracket after `$$` inside double quotes" ties the `'...'` reason to `$$`. But `_common.py:952` raises it for a `'...'` span inside a double-quoted `${...}`: `echo "${x:-'}'}"` blocks with no `$$` in it, and `echo "$$'a}'"` gets past. Say "a `'...'` span inside a double-quoted `${...}` holding a character that changes where it ends, an unbalanced bracket after `$$` inside double quotes", as `CHANGELOG.md:9` puts it. Then check every other reason in the docstring against its raise site, one by one.

**The Nits, folded in:**

- `_common.py:672`: the over-block of `echo $[ $(echo "1") + 1 ]`, fixed by the stack change above.
- `red_guard.py:78`: `only_bookkeeping` tests `os.path.basename(words[0])`. Use `program_name`, so `=git status` counts as bookkeeping as `git status` does.
- `_common.py:984`: the `CASE_IN_SUBSTITUTION` message says "inside a substitution". Say "inside a `$(...)`, `<(...)` or `>(...)` span", as the README and CHANGELOG do, and update any test that asserts the old words, listing it in the Evidence.

Seam: the hook scripts as subprocesses. Write the proving test first, and commit it failing (stage in one call, commit in its own) before any code change.

Per `CLAUDE.md`, before fixing, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` that prints to stderr. The extended reader-step line applies to every changed match: the `((` candidacy and the argument-position test, each probed straight after `{` and after a reserved word with no space between, in both command and argument position, inside single quotes, `$'...'`, double quotes, backticks, heredoc bodies, comments, `[[ ]]`, arithmetic and `case` patterns, and with an escaped `\\` before it. The span-end line applies to the new `$[` entry on the stack: probe it with each construct holding a `]`. Add every member that gets past a hook to the proving test before the fix, and probe each new branch's boundaries the same way before handing it on.

The commit hooks' gap on a commit inside a double-quoted substitution or a heredoc body stays in `docs/backlog.md` for its own change. The T6, T7, T10, T11, T12 and T13 timing cases must still finish under their limits. Run T15's timing rows again and record them.

Existing assertions this may change: a test asserting the old `CASE_IN_SUBSTITUTION` words. Any existing assertion that changes is listed in the Evidence, with the reason.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them and assertions listed in the Evidence with the reason.
- The T6, T7, T10, T11, T12 and T13 timing cases still finish under their limits.
- A `((` straight after a reserved word or a run of `{` is decided by `arithmetic_end`, as one at a word start is, and a `((` in the middle of any other word stays a glob group.
- `$[` is an entry on `source_text`'s bracket stack, closed by its own `]`, and the `brackets` counter is gone.
- A word-start `(` in argument position, and one starting a pattern word inside `[[ ]]`, is a glob group, so a `#` inside it or straight after its `)` raises ShellsDiffer. A `(` in command position, and a grouping `(` inside `[[ ]]`, reads as before.
- The `deploy_gate.py` module docstring names every reason `Unmodelled`, `Unclosed` and `ShellsDiffer` carry, each as its raise site has it.
- `red_guard.py`'s `only_bookkeeping` names programs with `program_name`, and the `CASE_IN_SUBSTITUTION` message names the span kinds.
- `CHANGELOG.md` and the README's `deploy-gate` paragraph describe the new reading.

## Evidence
