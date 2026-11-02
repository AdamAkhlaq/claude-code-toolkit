---
id: T4
title: The shell reader splits words where bash does
blocked_by: [T3]
files: [hooks/scripts/_common.py, tests/test_hooks.py, CHANGELOG.md]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_shell_reader_splits_words_where_bash_does: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `echo a\ #b; git tag v1`, `x="a b"; echo ${x/ #/}; git tag v2`, `echo $[1<<EOF]` with `git tag v3` and `EOF` on the next two lines, `git ta\` with `g v4` on the next line, `bash -c -- ''git tag v5''`, `bash -c -e ''git tag v6''` and `ksh -c ''git tag v7''`, and exits 0 silently on `echo "a git tag v1" $''\''''`, a quoted mention in a call shlex cannot parse'
status: done
executed_by: single
branch: ticket/0003-T4
---

## Context

From the second review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-24 of a90e0c2"): Importants at `_common.py:198` (comment start), `_common.py:202` (`$[...]`), `_common.py:155` (backslash-newline) and `_common.py:296` (`-c` options), and the Nits at `_common.py:137` (more shells) and `_common.py:162` (fallback keeps quoted spans). This is a `fix-bug` change, so there is no spec or plan; the review's findings and Decisions are the requirements. Execution mode is `single`.

Each is a place where `_common.shell_tokens` or `shell_source` reads a command differently from bash, and in each the shell runs a gated command that the reader drops or misjoins:

- `shell_source` starts a comment at a `#` after any space, but a space escaped with a backslash is part of a word, and a `#` inside `${...}` is a pattern, so neither starts a comment. Start a comment only after an unescaped word break outside `${...}`.
- Arithmetic is recognised only from `((`; the older `$[...]` form holds a `<<` shift too. Count `$[` to `]` as arithmetic.
- A backslash-newline is deleted by bash, joining the words either side; `shell_tokens` turns it into a space. Replace the pair with nothing, outside single quotes.
- `shell_script` takes the word straight after the `-c` cluster, but bash reads further options after it (`bash -c -- 'script'`, `bash -c -e 'script'`). After the cluster, skip options, `--`, and the arguments of `-o` and `-O`.
- `SHELLS` misses `ksh`, `mksh`, `csh`, `tcsh` and `fish`, which macOS ships or users install.
- After a quoting error, the fallback split keeps quote characters and splits inside quotes, so a quoted mention is gated. Keep each quoted span as one token in the fallback.

The same reader feeds `red-guard` through `find_commit` and `only_bookkeeping`. Seam: each hook script as a subprocess, as the other `DeployGateTests` and `RedGuardTests` do. Write the proving test and the red-guard case first and commit them failing before any code change. Confirm each case in bash with a stub `git` function before writing it into the test, so the test asserts what the shell really does.

## Acceptance

- The proving test passes.
- `RedGuardTests` gains a case: with a red feedback command and a changed source file, `bash -c -- 'git commit -am x'` is blocked. It is committed failing with the proving test.
- Every other test in `tests/` passes unchanged.
- `CHANGELOG.md`'s `[Unreleased]` tokeniser entry covers the escaped and `${...}` `#`, `$[...]`, backslash-newline, options after `-c`, the added shells and the fallback.

## Evidence

### Evidence 2026-10-24 16:12

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
............................................................................
----------------------------------------------------------------------
Ran 76 tests in 8.982s

OK
```

Each case was first run in bash with `git` and `ksh` stubbed as shell functions: bash ran `git tag` for all seven gated cases and not for the quoted mention, and the gate at `2d03902` let all seven through and blocked the mention. The proving test and `RedGuardTests.test_an_option_after_c_does_not_hide_the_commit` were committed failing in `79c6229`, before any code change (`AssertionError: 0 != 2 : echo a\ #b; git tag v1` and `AssertionError: 0 != 2`). After the fix the same probe gave gated for all seven and silent for the mention. Edge cases checked to still read as bash does: `# note` on its own line and `echo a # note <<EOF` still start a comment, `${#x}` and `a#b` do not, an escaped backslash before a newline is not a continuation, and a heredoc after `$[2<<1]` still closes.

Live check, 2026-10-24: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                        | Result                                                                                                                        |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `echo a\ #b; git tag v1`                       | blocked: "Blocked: 'echo a\ #b; git tag v1' matches gated command pattern '^git tag ' in .claude/toolkit.json."               |
| `x="a b"; echo ${x/ #/}; git tag v2`           | blocked: "Blocked: 'x=\"a b\"; echo ${x/ #/}; git tag v2' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| `git ta\`, then `g v4` on the next line        | blocked: "Blocked: 'git ta\⏎g v4' matches gated command pattern '^git tag ' in .claude/toolkit.json."                         |
| `bash -c -- 'git tag v5'`                      | blocked: "Blocked: 'bash -c -- 'git tag v5'' matches gated command pattern '^git tag ' in .claude/toolkit.json."              |
| `echo hello # a comment mentioning git tag v9` | ran, printed `hello`                                                                                                          |

`git for-each-ref refs/tags` in the repo afterwards listed nothing.

### Verifier 2026-10-24 16:14

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok - `DeployGateTests.test_the_shell_reader_splits_words_where_bash_does` and `RedGuardTests.test_an_option_after_c_does_not_hide_the_commit` were added on this branch and run the hook scripts as subprocesses. At `79c6229` (tests only) both fail (`AssertionError: 0 != 2 : echo a\ #b; git tag v1`, `AssertionError: 0 != 2`). Each of the eight cases, run on its own through `deploy_gate.py`, gives the opposite exit code on `change/0003-fix-deploy-gate-bypass` (0 for the seven gated cases, 2 for the mention), so each case would catch a regression on its own. In bash with a stub `git` function, all seven gated cases ran `git tag` and the mention did not.
3. proving test run: 0, `Ran 2 tests in 0.357s OK`
4. feedback command: 0, `Ran 76 tests in 8.806s OK`
5. acceptance: 4 of 4 checked, none failed - the proving test passes (check 3). The red-guard case for `bash -c -- 'git commit -am x'` is present, was red at `79c6229` with the proving test, and passes now. The full suite passes, and the test diff only adds lines. The `[Unreleased]` entry covers the escaped and `${...}` `#`, `$[...]`, backslash-newline, options after `-c`, the added shells and the fallback.
6. scope: ok - `CHANGELOG.md`, `hooks/scripts/_common.py`, `tests/test_hooks.py`, plus the ticket file
7. tests intact: ok - `tests/test_hooks.py` 25 added, 0 removed, no skip or expected-failure markers
