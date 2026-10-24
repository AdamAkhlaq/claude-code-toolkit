---
id: T4
title: The shell reader splits words where bash does
blocked_by: [T3]
files: [hooks/scripts/_common.py, tests/test_hooks.py, CHANGELOG.md]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_shell_reader_splits_words_where_bash_does: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `echo a\ #b; git tag v1`, `x="a b"; echo ${x/ #/}; git tag v2`, `echo $[1<<EOF]` with `git tag v3` and `EOF` on the next two lines, `git ta\` with `g v4` on the next line, `bash -c -- ''git tag v5''`, `bash -c -e ''git tag v6''` and `ksh -c ''git tag v7''`, and exits 0 silently on `echo "a git tag v1" $''\''''`, a quoted mention in a call shlex cannot parse'
status: todo
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
