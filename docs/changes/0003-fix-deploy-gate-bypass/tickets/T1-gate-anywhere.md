---
id: T1
title: A gated command is caught anywhere in the line
blocked_by: []
files:
  [hooks/scripts/deploy_gate.py, hooks/scripts/_common.py, tests/test_hooks.py]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_gated_command_is_caught_anywhere_in_the_line: with gatedCommands ["^git tag ", "^gh release "], deploy_gate.py exits 2 on `cd . && git tag v2`, `true; git tag v3`, `/usr/bin/git tag v4`, `bash -c "git tag v5"`, `git fetch -q && gh release create v6`, `git tag v7` on the line after `git fetch -q` and `git tag v8` on the line after a heredoc ends, and exits 0 silently on `echo "git tag v1"`, `git log --grep ''git tag ''`, an `echo` whose quoted argument has `git tag v1` on its second line, and a heredoc whose body mentions `git tag v1` and `/usr/bin/git tag v2`'
status: in-progress
---

## Context

A bug fix through `/toolkit:fix-bug`; the reproduction is in `intent.md`. No spec or plan.

`deploy_gate.py` matches each `gatedCommands` regex against the raw command, so a pattern anchored with `^` only sees the first simple command. Match each pattern against each simple command in the call instead: split with `_common.shell_tokens` at control operators, name the program by basename, and search the script of `bash -c` and `eval` too, as `_common.find_commit` does for commits. Keep matching the raw command as well, so a pattern that is not anchored behaves as before.

Seam: the hook script as a subprocess, as the other `DeployGateTests` do.

## Acceptance

- The proving test passes.
- The existing `DeployGateTests` pass unchanged.
- `python3 -m unittest discover -s tests` passes.
- Re-running the reproduction in `intent.md` blocks all four commands and creates no tag.

## Evidence
