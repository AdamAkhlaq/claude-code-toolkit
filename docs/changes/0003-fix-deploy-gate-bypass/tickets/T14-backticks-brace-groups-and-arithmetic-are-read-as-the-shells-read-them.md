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
status: done
executed_by: single
branch: ticket/0003-T14
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

Amended by the executor, 2026-10-31: the family checks found more members than the review listed. All are fixed here and in the proving test, and each gets past the hooks at `28f3cbb`, apart from the one regression guard named below:

- **`#` straight after a substitution's `)`.** The `)` of `$(...)`, `<(...)`, `>(...)` or `$((...))` does not end a word in either shell, but `source_text` started a word there, so `echo $(echo a)#x; git tag v1`, `cat <(echo a)#x; ...`, `x=$(echo a)#x; ...`, `echo $((1))#x; ...` and ``echo `echo a`#x; ...`` read `#x; git tag v1` as a comment, and both shells run the tag. This is the same `#` word-start step as the arithmetic Important, so it is fixed with it: `source_text` keeps a stack of open parentheses, with the kind each closes. After a substitution's `)` the word goes on; after a subshell's, a command `((...))`'s or `f()`'s a word starts, as the shells read it. After an array's `)`, `a=(b)#x` is part of the word to bash and a comment to zsh, so a `#` there raises ShellsDiffer.
- **A `((` that is not arithmetic.** `source_text` took every `((` as arithmetic. Under the new arithmetic rule that would have hidden the comment in `((echo a) # it's`, newline, `); git tag v1; echo "'"`, a regression, and it already hid a heredoc: `echo $((cat <<EOF`, newline, `it's`, newline, `EOF`, newline, `) ); git tag v1; echo "'"` passes at `28f3cbb` and zsh runs the tag. A `((` is now arithmetic only where `closing_paren` would read it so (`arithmetic_at`, which caches each close so a run of `((` is scanned once), and a `$(` inside arithmetic is still a substitution.
- **A `case` inside an unquoted substitution.** A `case` pattern's `)` would pop a parenthesis it did not push, so `source_text` raises `Unmodelled(CASE_IN_SUBSTITUTION)` on a `case` inside a `$(...)`, `<(...)` or `>(...)` span, which T13's decision 1a already called for. This replaces "Do not add a block" in the `README.md:76` Nit above: `cat <(case x in x) echo hi;; esac)` and `x=$(case $1 in a) echo A;; esac)` now block in every hook, so the README sentence is true as written.
- **zsh's brace group** also hides `{\git tag v1}`, `{'git' tag v1}`, `{"git" tag v1}`, `{$'git' tag v1}`, `{ {git tag v1} }`, `a(){git tag v1}; a`, `zsh -c '{git tag v1}'` and `` echo `{git tag v1}` ``. The split runs on words after quote removal, so a quoted brace is split too; a word holding whitespace, which only quotes make, is left whole so a `zsh -c` script stays one word.

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

### Evidence 2026-10-31 20:19

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
........................................................................................
----------------------------------------------------------------------
Ran 88 tests in 23.163s

OK
```

Before fixing, each family in Context was checked in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git` that prints to stderr. Every form that got past a hook went into the proving test, which was committed failing (3766939). It failed first on `` echo `bash -c 'echo a # x \\ ``, newline, `` git tag v1'` ``, where the gate exited 0, and red-guard failed on `{git commit -am x}`, which also exited 0. The members in the Context amendment turned up while fixing. They were added to the test in the fix commit, and each one gets past the hooks at `28f3cbb`, apart from `((echo a) # it's`, newline, `); git tag v1; echo "'"`, which is a guard against a regression found mid-fix.

Shell facts behind the fix, from the probes:

- **Backticks.** Both shells end a backtick span at its first unescaped backtick before reading the text inside, so `` x=`: # ` `` ends its comment at the backtick. The one-pass unescape was compared with both shells for one to five backslashes before a newline, a `$`, a `"`, the end of the span and an escaped nested backtick. The contexts were unquoted, single quotes, double quotes, `$'...'` and `$x`, with the span bare and inside `"..."`. Every real context matched. The only mismatches were harness artifacts: a trailing backslash escaping the harness's own `)`, and three backslashes leaving a nested backtick unescaped.
- **Brace groups.** zsh opens a brace group at a `{` stuck to a command word and closes it at a `}` that ends a word. `{prog a}`, `true&&{prog a}`, `if {prog a}; then :; fi` and `{x=1 prog a}` all run `prog`. `{echo a}b}` prints `a}b` and `{echo {} a}` prints `{} a`. `}case` and `!case` are not keywords.
- **`#` after brackets.** After the `)` of `$(...)`, `<(...)` or `$((...))`, and after `$[...]`, a `#` is part of the word. After a subshell, a command `((...))`, `f()` or a `case` pattern it starts a comment. After `a=(b)`, bash reads it as part of the word and zsh as a comment.

The fix:

- **`backtick_script`** makes a span's script in one pass from the left: it takes the backslash off `\\`, `` \` ``, `\$`, and `\"` inside double quotes, and deletes each backslash-newline.
- **`source_text`** ends an unquoted backtick span with `escaped_close`, appends its script to `spans`, and keeps the script's own `shell_source` reading in place of its text, so the commit hooks still see a commit inside it. `deploy-gate` steps over backtick spans in that text (`substitutions(..., backticks=False)`), so a script is not unescaped twice. The `backtick` flag and its branches are gone. Because both readings can now hold a `\` and newline that `backtick_script` leaves in single quotes, the agreement check in `shell_source` compares the two readings with their own backslash-newlines deleted on both sides (`flattened`).
- **The bracket stack.** `source_text` keeps a stack of open parentheses that replaces the `arithmetic` counter, and no comment opens inside arithmetic or `$[...]`. A deleted backslash-newline keeps the word-start state, so `echo a \`, newline, `# c`, newline, `ls` is read as the shells read it.
- **`brace_group_words`** splits a zsh brace group's `{` and `}` off the words `shell_tokens` returns. It keeps `{}` whole and leaves a word holding whitespace alone.
- **`keyword_position`** counts a run of `{` before `case`, in `closing_paren` and in `source_text`.

**Docs.** The `deploy_gate.py` docstring names every reason, and the `docs/backlog.md` line about it is gone. CHANGELOG and README describe the backtick, brace-group, arithmetic and `#` reading. The five Nits are fixed as Context says, with the fourth fixed through the amendment above.

No existing assertion changed. T13's blocked case at `tests/test_hooks.py:519` still blocks, now for release authorisation.

Probe sweeps on the final code:

- **Probe files.** The family, boundary, `#`-after-bracket and arithmetic files hold 224 forms. None gets past the gate. Every commit-hook miss left is inside a double-quoted substitution, the gap `docs/backlog.md` keeps for its own change.
- **Earlier corpora.** The 657 cases from 0003's earlier sweeps, compared with `28f3cbb`, give 2 misses. Both are `eval` of a variable, the README's known limit, and both miss at `28f3cbb` too. One result changed, an over-block lifted: `` echo `cat <<'E'`` ... `` ` ``, which neither shell runs, is now allowed.

**Timing** (gate and `is_git_commit`, at the fix against `28f3cbb`):

- Every existing row is within 0.1 s of base.
- New adversarial rows (100,000 `(`, 30,000 `((#`, 20,000 `$(a)#x`, 20,000 backtick spans, 30,000 `{a}`, 10,000 `((a) #x`) all finish under 0.5 s in the gate. `is_git_commit` is under 9 s, where the known `find_commit` cost dominates.
- 30,000 nested `$((` now raise `RecursionError` in `is_git_commit` as well as in the gate (as at base), through `closing_paren` and `arithmetic_close`. It starts at about 1,000 levels, and every hook blocks on it, so it fails closed.
- The T6, T7, T10, T11, T12 and T13 timing tests pass.

`claude plugin validate .` passes, with the same `.DS_Store` warnings as before.

Live check, 2026-10-31, on the final code. Headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` sessions ran one Bash call per command, with no `RELEASE_AUTHORIZED` and no marker. The first used a throwaway repo with `"gatedCommands": ["^git tag "]`:

| Command | Result |
| --- | --- |
| `` echo `bash -c 'echo a # x \\ `` / `` git tag v1'` `` | blocked: matches `^git tag ` |
| `{git tag v2}` | blocked: matches `^git tag ` |
| `(( y = ##a )); git tag v3` | blocked: matches `^git tag ` |
| `echo $(echo a)#x; git tag v4` | blocked: matches `^git tag ` |
| `` x=`: # ` `` / `bash -c 'echo a # x \` / `git tag v5'` | blocked: matches `^git tag ` |
| `echo "$({case x in x) echo ")"; git tag v6; echo "(" ;; esac})"` | blocked: "deploy-gate does not read a `case` inside a substitution ..." |
| `` x=`echo a # note`; echo "x=$x" `` | ran: `x=a` |
| `find . -name app.py -exec echo {} \;` | ran: `./app.py` |
| `echo $(( 16#ff ))` | ran: `255` |
| `echo a \` / `# c` / `echo live-ran` | ran: `a`, `live-ran` |

The second used another throwaway repo with `"feedbackCommand": "echo boom-red; exit 1"` and a modified `app.py`:

| Command | Result |
| --- | --- |
| `{git commit -am x}` | blocked: "Commit stopped: the feedback command is red." |
| `echo $(echo a)#x; git commit -am x` | blocked: "Commit stopped: the feedback command is red." |
| `` echo `bash -c 'echo a # x \\ `` / `` git commit -am x'` `` | blocked: "Commit stopped: the feedback command is red." |
| `x=$(case x in a) echo A;; esac); echo "$x"` | blocked: "Blocked: red-guard could not read this Bash call (a `case` inside a substitution) ..." |
| `` echo `echo 'a\ `` / `` b'` `` | ran: `ab` |

No tag was created and nothing was committed in either repo.

### Verifier 2026-11-01 10:24

Verdict: pass
Checks:

1. ticket integrity: ok. All frontmatter fields present, `status: in-progress`, Evidence quotes `python3 -m unittest discover -s tests` with exit 0.
2. proving test present and meaningful: ok. `DeployGateTests.test_backticks_brace_groups_and_arithmetic_are_read_as_the_shells_read_them` and the six new cases in `RedGuardTests.test_reworded_commits_are_recognised` were added on this branch (test-only commit 3766939 before the fix 8a01bec). They drive `deploy_gate.py` and `red_guard.py` as subprocesses. Run against the integration branch's hooks with this branch's test file, both fail (`0 != 2 : echo \`bash -c 'echo a # x \\` and `0 != 2 : {git commit -am x}`). Per case, 50 of the 52 release-authorisation cases and all 3 `case` cases exit 0 at the base and 2 at the head; the other two blocked as Unmodelled at base, and `((echo a) # it's` blocked at base too (the regression guard the ticket names). Spot-checked in `/bin/bash` and `/bin/zsh` with a stub `git`: `{git tag v1}` runs the tag in zsh only, `(( y = ##a )); git tag v1`, `echo $(echo a)#x; git tag v1`, the backtick `\\` form and the `` x=`: # ` `` form run it in both, and `echo a \`, newline, `#c; git tag v1` runs only `echo a` in both, matching the test's allow case.
3. proving test run: exit 0, `Ran 2 tests in 5.271s OK` (`python3 -m unittest tests.test_hooks.DeployGateTests.test_backticks_brace_groups_and_arithmetic_are_read_as_the_shells_read_them tests.test_hooks.RedGuardTests.test_reworded_commits_are_recognised`).
4. feedback command: exit 0, `Ran 88 tests in 22.210s OK`.
5. acceptance: 8 of 8 checked. Proving test passes (check 3). Other tests unchanged: the test diff is additions only, suite green. Timing cases: the `time.monotonic()` limits in `tests/test_hooks.py` pass within the suite. No `backtick` flag in `source_text` (grep finds none); an unquoted span ends at `escaped_close` and `backtick_script` unescapes and joins in one pass, as does the quoted path in `substitution_end`. `shell_tokens("{git tag v1}")` gives `{ git tag v1 }`, and `find . -exec echo {} \;` keeps `{}`. The comment branch is guarded by `not arithmetic and not brackets`, and `arithmetic_close` has no comment branch. The `deploy_gate.py` docstring names the case, comment, backslash-newline, unclosed, too-long and shells-differ reasons; the backlog line is gone. CHANGELOG and README describe the backtick, brace-group, arithmetic and `#` reading, and the five Nits are fixed (CHANGELOG clause, "zsh's" moved to `{case`, README "outside a backtick span", README case sentence true as amended, `skip_heredoc_bodies` docstring).
6. scope: ok. Every changed file is in `files` or is the ticket itself.
7. tests intact: ok. No assertion deleted, skipped or loosened.
