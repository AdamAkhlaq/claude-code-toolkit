---
id: T14
title: A backtick span, a zsh brace group and arithmetic are read as the shells read them
blocked_by: [T13]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    README.md,
    docs/backlog.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_backticks_brace_groups_and_arithmetic_are_read_as_the_shells_read_them: with gatedCommands ["^git tag "], deploy_gate.py exits 2 naming release authorisation on `` echo `bash -c ''echo a # x \\` / `git tag v1''` ``, `` echo "`bash -c ''echo a # x \\` / `git tag v1''`" ``, `` x=`: # ` / `bash -c ''echo a # x \` / `git tag v1''` ``, `` `# ` / `eval ''echo a # x \` / `git tag v1''` ``, `(( y = ##a )); git tag v1`, `echo $(( ##a )); git tag v1`, `echo $[ ##a ]; git tag v1`, `{git tag v1}`, `true&&{git tag v1}`, `if {git tag v1}; then :; fi` and `echo "$({git tag v1})"` (lines joined by a newline); exits 2 naming a `case` on `echo "$({case x in x) echo ")"; git tag v1; echo "(" ;; esac})"`; and exits 0 silently on `` x=`echo a # note` ``, `` echo `echo ''a\` / `b''` ``, `find . -name x -exec echo {} \;`, `echo $(( 16#ff ))` and `echo a \` / `# c` / `ls`; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py exits 2 on `{git commit -am x}`, `` echo `bash -c ''echo a # x \\` / `git commit -am x''` `` and `` x=`: # ` / `bash -c ''echo a # x \` / `git commit -am x''` ``'
status: todo
---

## Context

From the eighth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-31 of 28f3cbb"): the six Importants at `_common.py:599`, `:855`, `:630` (twice), `:901` and `deploy_gate.py:8`, the five Nits and the Out of pass over-block folded into this ticket at that review's gate, a seventh bypass found while cutting it, and the Decisions taken at both gates. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

**Backtick spans (`_common.py:599`, `:630`, `:855`).** `source_text` reads an unquoted backtick span by flipping a `backtick` flag at each backtick it reaches, and joins backslash-newlines while the flag is set. Three bypasses come from that:

- A `#` comment inside the span runs on to the newline and swallows the closing backtick, so the flag stays set and a later single-quoted `bash -c` or `eval` script loses its backslash-newline: `` x=`: # ` ``, newline, `bash -c 'echo a # x \`, newline, `git tag v1'` passes, and both shells run the tag. Open since before T13.
- Inside the span, `\\` before a newline in single quotes is taken for a continuation, though the pair is an escaped backslash: ``echo `bash -c 'echo a # x \\``, newline, `` git tag v1'` `` reaches the inner reader as `echo a # x \git tag v1`. A regression from T13; `d0fb265` blocked it.
- `substitution_end` (`:855`) unescapes a double-quoted backtick span and then joins it, so the `\` and newline the unescape leaves are deleted inside single quotes. The same form inside `"..."` passes. A regression from T13.

Decided at this ticket's gate: read a backtick span as both shells do. They find the closing backtick first, then read the text inside as a script. So an unquoted backtick span ends at its first unescaped backtick (`escaped_close`, as `substitution_end` already does inside double quotes), and its script is made in one left-to-right pass over backslash pairs:

- `\\` gives `\`
- `` \` `` gives `` ` ``
- `\$` gives `$`
- `\"` gives `"`, inside double quotes only
- `\` and a newline is deleted
- any other `\x` is kept as is

That script is then read as a script of its own, with the continuation rules T13 gave `shell_source`. A `\` and newline left by the pass is a continuation in unquoted text there and is kept in single quotes, as the shells do. Check that in `/bin/bash` 3.2 and `/bin/zsh` before relying on it, for `\\`, `\\\\` and `\\\` before a newline, in unquoted, `"..."`, `'...'` and `$'...'` text inside the span, and with the span itself unquoted and inside `"..."`. Delete the `backtick` flag and every branch that only it uses (`:599`, the `joined(span) if backtick` at `:614`, and the `backtick or` at `:633` and `:665`), and the `joined` after the unescape at `:855`. The commit hooks read `shell_tokens`, so a `git commit` inside an unquoted backtick span must still reach `find_commit` after the change, as the existing red-guard backtick cases check. Modelling the span was weighed against blocking any `#` comment or backslash-newline inside one, and chosen: it is what both shells do, it needs no grammar state, and it blocks nothing new.

**A zsh brace group (`_common.py:901`, and found while cutting this ticket).** zsh opens a brace group at a `{` stuck to the next word in command position and closes it at a `}` ending an unquoted word. `zsh -c '{prog a}'` runs `prog a`, and so do `true&&{prog a}`, `if {prog a}; then :; fi`, `{x=1 prog a}` and `{echo a;}`. bash reads `{prog` as a word. In 0003 this gives two bypasses, both open since before T13:

- `echo "$({case x in x) echo ")"; git tag v1; echo "(" ;; esac})"` passes, because `closing_paren` counts a `case` only after a metacharacter. zsh runs the tag.
- `{git tag v1}`, `true&&{git tag v1}`, `if {git tag v1}; then :; fi` and `echo "$({git tag v1})"` pass, because the word `{git` names no program. zsh runs the tag. `is_git_commit("{git commit -am x}")` is False, so `red-guard`, `secret-guard` and `ticket-sync` miss the commit form too.

Decided at this ticket's gate: model it. In `shell_tokens`, after brace expansion, split a leading unquoted `{` off a word into its own token when another character follows it, and a trailing unquoted `}` off a word that holds more than it. A `{}` word stays whole, so `find . -exec echo {} \;` is unchanged. Every hook then sees `git` as a program word. The gate already treats every unquoted word as a possible program, so `echo {git tag v1}` blocks, as `echo git tag v1` already does. In `closing_paren`, count `{` as a word start before `case`, so `{case` raises `Unmodelled(CASE_IN_SUBSTITUTION)`. From the probes in zsh 5.9: `{echo a}b}` prints `a}b`, `{echo "a}"}` prints `a}`, `{echo {} a}` prints `{} a`, `echo a}` is a parse error, and `}case` and `!case` are not keywords. Probe the rest of the family in both shells before fixing: `{` before each reserved word zsh accepts, after `&&`, `||`, `|`, `;`, `(`, a newline, `then`, `do` and `else`, and nested braces.

**`#` inside arithmetic (`_common.py:630`).** `source_text`'s comment branch is taken inside `((...))`, `$((...))` and `$[...]`, where `##a` is a character code. `(( y = ##a )); git tag v1` and `for (( i = ##a; i < 0; i++ )); do :; done; git tag v1` pass, and both shells run the tag; with `echo $(( ##a )); git tag v1` and `echo $[ ##a ]; git tag v1`, zsh runs it. Open since `main`. `source_text` already counts `arithmetic` and `brackets`; do not open a comment while either is non-zero. `closing_paren` skips arithmetic whole and needs no change; check that `arithmetic_close` itself does not read `#` as a comment.

**The docstring (`deploy_gate.py:8`).** The module docstring names the `case` and the backslash-newline reasons but not `COMMENT_IN_SUBSTITUTION`, which T13's acceptance required. Name it, and every other reason `Unmodelled` and `ShellsDiffer` carry after this ticket, and delete the `docs/backlog.md` line about it.

**The Nits and the Out of pass item, folded in:**

- `CHANGELOG.md:9`: drop "or a `case`" from the opening clause about a `$(...)` that holds a quoted `)`, since any `case` there now blocks. Drop "zsh's" before `"$(f() { case ...; })"`, since `f() { ...; }` is the POSIX form bash runs too.
- `_common.py:666` and `:633`: their messages say bash and zsh differ inside a backtick span, where both join. The backtick branch goes away under the decision above. Check that no message raised for a backtick span still claims the shells differ.
- `README.md:76`: the backslash-newline sentence says it is kept "inside single quotes or `$'...'`". Inside a backtick span both shells delete it there too. Say so.
- `README.md:76`: the `case` sentence says a `case` "anywhere inside a substitution" blocks, but `cat <(case x in x) echo hi;; esac)` at the top level is read and not blocked. That opens no bypass, since the text stays in the reading. Scope the sentence to what blocks. Do not add a block.
- `_common.py:1022`: the `skip_heredoc_bodies` docstring's last sentence reads "in a body that does not to `literal`". Make it "in a body that does not expand is appended to `literal`".
- Out of pass: `echo a \`, newline, `# c`, newline, `ls` raises `Unmodelled`. The written reading does not start a word after a dropped backslash-newline (`_common.py:599-603`), so the `#` is not read as a comment there, and the two readings differ. Both shells delete the backslash-newline and read `# c` as a comment. Keep the word-start state across a deleted backslash-newline, and check both shells first.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing, staged in one call and committed in its own, before any code change. Per `CLAUDE.md`, before fixing, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` that prints to stderr, and probe every step that rewrites or matches the text in each context `CLAUDE.md` names:

- inside single quotes, `$'...'`, double quotes and backticks
- in heredoc bodies and comments
- inside `[[ ]]`, arithmetic and `case` patterns
- with an escaped `\\` before it, and straight after `{`

Add every member that gets past a hook to the proving test before the fix. Probe each new or changed branch's boundaries the same way before handing it on. The commit hooks' gap on a commit inside a double-quoted substitution or a heredoc body stays in `docs/backlog.md` for its own change. The T6, T7, T10, T11, T12 and T13 timing cases must still finish under their limits. Run the T13 timing harness's backtick rows again, and record them.

Existing assertions this may change: T13's blocked group at `tests/test_hooks.py:519` (``echo `echo a # x \``, ...) asserts only "Blocked" and should still block, now for release authorisation. Any other existing assertion that changes is listed in the Evidence, with the reason.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them and assertions listed in the Evidence with the reason.
- The T6, T7, T10, T11, T12 and T13 timing cases still finish under their limits.
- `source_text` holds no `backtick` flag. A backtick span, quoted or not, ends at its first unescaped backtick, and its script is unescaped and joined in one pass before it is read.
- `shell_tokens` splits a zsh brace group's `{` and `}` off the words they touch, and keeps a `{}` word whole.
- No `#` comment opens inside `((...))`, `$((...))` or `$[...]`.
- The `deploy_gate.py` module docstring names every reason `Unmodelled` and `ShellsDiffer` carry. The `docs/backlog.md` line about it is gone.
- `CHANGELOG.md` and the README's `deploy-gate` paragraph describe the backtick, brace-group and arithmetic reading, and the five Nits are fixed as Context says.

## Evidence
