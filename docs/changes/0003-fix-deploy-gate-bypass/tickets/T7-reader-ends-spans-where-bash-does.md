---
id: T7
title: The shell reader ends quotes, heredocs and substitutions where bash does
blocked_by: [T6]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    tests/test_hooks.py,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_reader_ends_quotes_heredocs_and_substitutions_where_bash_does: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `echo $''a\''b''; git tag v1; echo ''c''`, on `cat <<E''OF''`, `EOF`, `git tag v2` and `E` on four lines, on `cat <<E:OF`, `E:OF`, `git tag v3` and `E` on four lines, on ``echo `echo \`git tag v4\`` ``, and on `x="$( : # )`, `git tag v5` and `)"` on three lines, and exits 0 silently on `cat <<E''OF''`, `git tag v6` and `EOF` on three lines; and in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py blocks with the feedback output on `echo $''a\''b''; git commit -am x; echo ''c''` and on `cat <<E''OF''`, `EOF`, `git commit -am x` and `E` on four lines'
status: in-progress
executed_by: single
branch: ticket/0003-T7
---

## Context

From the third review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-25 of cd72334"): the Importants at `_common.py:167`, `_common.py:175`, `deploy_gate.py:198` and `deploy_gate.py:224`, and the Decisions taken at that review. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

Four places where the reader ends a span somewhere bash does not, so text bash runs is read as part of a quote, a heredoc body or the wrong substitution:

- `_common.QUOTED`, used by the fallback after shlex fails, reads `$'a\'b'` as the plain single-quoted `'a\'` and pairs every later quote wrongly. T4 (`d73214a`) introduced it: at `a90e0c2` the first case blocked. Read `$'...'` with backslash escapes before the plain `'...'` alternative, and take a backslash pair as one unit in `FALLBACK_TOKEN`'s unquoted branch.
- `_common.HEREDOC` ends the delimiter at the first character outside `[\w.-]` or at a closing quote. Bash's delimiter is the whole word after `<<`, up to whitespace or an operator, with its quotes removed, and it is quoted when any quote or backslash appears anywhere in it: `<<E'OF'` ends at a line `EOF` and its body is literal, and `<<E:OF` ends at `E:OF`.
- `deploy_gate.substitutions` ends a backtick span at the next backtick even when it is escaped. Inside backticks, `` \` `` is a nested backtick: skip it when looking for the close, and read the inner text with each `` \` `` turned into a backtick, so the nested substitution is found by the recursion.
- `deploy_gate.closing_paren` counts a `)` inside a `#` comment. Outside quotes, a `#` at the start of a word starts a comment that runs to the newline; skip it.

`red-guard` reads through the same `_common` functions, so the first two forms are pinned for it as well.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check each form's whole family in bash with a stub program before fixing it, not only the reported case: other characters in a delimiter (`<<"E"OF`, `<<\EOF`, `<<E\OF`, `<<-E'OF'`), other escapes inside `$'...'`, deeper backtick nesting, a `#` comment in a `$(...)` outside double quotes. Add every family member that gets past the gate to the proving test before the fix. A stub `git` function writes into `$x` when it runs inside `x="$(...)"`, so have it print to stderr.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry names the four forms.

## Evidence

### Evidence 2026-10-25 17:35

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
...............................................................................
----------------------------------------------------------------------
Ran 79 tests in 11.121s

OK
```

Per `CLAUDE.md`, each form's family was checked first in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` that prints to stderr (no newer bash is installed). Every member that got past the gate went into the proving test, committed failing before the code changed (08f06aa): four `$'...'` shapes (`echo $'a\'b'; ...`, `echo $'\''; ...`, one after a double-quoted `\"`, `x=$'\'' git tag v1`), seven delimiters (`<<E'OF'`, `<<"E"OF`, `<<E\OF`, `<<-E'OF'`, `<<E:OF`, `<<E+OF`, `<<E$OF`), backticks nested two and three deep, unquoted and in double quotes, a `)` in a `#` comment inside `"$(...)"`, and a heredoc body holding `)` inside `"$(...)"` (zsh runs it; bash 3.2 cannot parse it). Against the hook from 955777b every one of them exited 0, while bash or zsh ran the tag. Three calls that must stay silent are pinned too: `<<E'OF'` and `<<E:OF` with `git tag` in the body, which the old delimiter reading wrongly blocked, and a top-level escaped `` \`git tag v6\` ``, which bash prints.

While timing the new paths, 20000 unclosed `cat <<E` lines inside `"$(...)"` took 21.9 s; the same at the top level took 42 s on `change/0003-fix-deploy-gate-bypass` too, past the 30 s timeout, because each heredoc whose closing line never comes was searched for to the end of the call. That went into the proving test as a second failing commit (21446fb) before `skip_heredoc_bodies` changed: now 0.1 s, 0.1 s and 0.1 s for the three shapes.

The fix:

- `shell_source` writes a `$'...'` span as a plain single-quoted one, with `\'` as `'\''`, so neither shlex nor the fallback can pair its quotes wrongly. The fallback also takes a backslash pair as one unit outside quotes. `QUOTED` was left as it was: no `$'` reaches it any more.
- `heredoc_at` replaces the `HEREDOC` regex: the delimiter is the whole word after `<<`, up to whitespace or an operator, with its quotes removed, quoted when any quote or backslash appears in it.
- `substitutions` ends a backtick span at the first unescaped backtick and reads its inner text with `` \` ``, `\$` and `\\` unescaped, so the recursion finds the nested span.
- `closing_paren` skips a `#` comment that starts a word and the body of a heredoc inside the span.
- `skip_heredoc_bodies` finds a closing line through `line_starts`, an index of the call's lines built once per command, instead of scanning.

Further family members probed after the fix, all blocked where bash runs the tag and silent where it does not: `<<E"O"F`, `<<\E\O\F`, `<< E'OF'`, `<<E\ OF`, `<<E'OF'; git tag v1` on the heredoc's own line, two heredocs on one line, `<<"E\"OF"`, `<<''` with an empty closing line, `$'it\'s'`, `$'a\\\'b'`, `$'\x27'`, `"$'a'"` in double quotes, a comment holding `)` or `'` inside `"$(...)"`, `;#` inside `"$(...)"`, backticks around `$(...)` around escaped backticks, `echo "a # b)"`, `echo "$(echo '#)')"`, and `$(git tag v1)` in the body of `<<E'OF'` (silent, literal) and of `<<E:OF` (blocked, expands). The T6 adversarial shapes are unchanged: the slowest is 1.3 s.

Found outside this ticket's scope: `red-guard` does not read a substitution in double quotes at all (`echo "$(git commit -am x)"` passes it, on `change/0003-fix-deploy-gate-bypass` too), nor nested escaped backticks or a substitution in an expanding heredoc body, since `_common.find_commit` reads tokens and only an unquoted `$(` or backtick splits them. `deploy-gate` catches all of these. Recorded for its own ticket.

Live check, 2026-10-25: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                               | Result                                                                                                     |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `echo $'a\'b'; git tag v1; echo 'c'`                  | blocked by `deploy-gate`, per the session's summary; the quoted message fell outside the captured tail     |
| `cat <<E'OF'`, `EOF`, `git tag v2`, `E` on four lines | blocked: "Blocked: 'cat <<E'OF' ... E' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| ``echo `echo \`git tag v3\`` ``                       | blocked, same message                                                                                      |
| `x="$( : # )`, `git tag v4`, `)"` on three lines      | blocked, same message                                                                                      |

`git for-each-ref refs/tags` in the repo afterwards listed nothing.
