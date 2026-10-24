---
id: T3
title: A gated command is caught behind any prefix or inside a quoted substitution
blocked_by: [T2]
files:
  [
    hooks/scripts/deploy_gate.py,
    hooks/scripts/_common.py,
    tests/test_hooks.py,
    README.md,
    CHANGELOG.md,
    skills/setup/SKILL.md,
    docs/changes/0003-fix-deploy-gate-bypass/intent.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_gated_command_is_caught_behind_a_prefix: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `X=1 git tag v1`, `env git tag v2`, `sudo -u ci git tag v3`, `time git tag v4`, `! git tag v5`, `{ git tag v6; }`, `if true; then git tag v7; fi`, `git -C . tag v8`, `echo "$(git tag v9)"`, `bash --norc -c "git tag v10"`, `bash -o pipefail -c "git tag v11"`, `git status | git tag v12` and `eval "git tag v13"`, and exits 0 silently on `echo "git tag v1"`, `git log --grep "git tag "` and `git commit -m "add git tag support"`'
status: todo
---

## Context

From the review of T1 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`), Important 4, the quoted-substitution half of 5, and the first two Nits. The review's Decisions section, taken by the maintainer, is the requirement. Execution mode is `single`, in the main working tree on `change/0003-fix-deploy-gate-bypass`.

`deploy_gate.expand` takes only the first word of a simple command as its program, so an assignment, a wrapper or a reserved word in front of a gated command hides it. The decision: match each pattern from every unquoted word that could name a program, by basename, rather than stripping a fixed list of wrappers that a missing entry would bypass. A word that contains whitespace came from quotes and is never a program, which keeps `echo "git tag v1"` and `git log --grep "git tag "` silent. The gate fails closed: an unquoted `echo git tag v1` is blocked, which is intended. For `git`, also match the line with its global options skipped (`_common.git_options`), so `git -C . tag` reads as `git tag`. Recurse into each `$(`...`)` and backtick span inside a word, so a substitution in double quotes is read as the command it runs. Find a shell's `-c` script after any options, long ones and option arguments included, with one helper in `_common.py` that `find_commit` uses too, so `bash --norc -c "git commit -m x"` reaches `red-guard`'s check.

Seam: the hook script as a subprocess, as the other `DeployGateTests` do. Write the proving test first and commit it failing, before any code change.

The README states where the gate's guarantee ends, as the maintainer decided at the review: a gated command written anywhere in a Bash call is caught; a script fed to an interpreter (`echo 'git tag v1' | bash`, `bash release.sh`, a `python -c` subprocess) is not, and a hard guarantee needs a permissions deny rule or withheld credentials. Say the same in one line of `intent.md`.

## Acceptance

- The proving test passes.
- `RedGuardTests` gains a case: `bash --norc -c "git commit -m x"` with a red feedback command is blocked. It is committed failing with the proving test.
- T1's and T2's proving tests and every other test in `tests/` pass unchanged.
- An unquoted `echo git tag v1` exits 2, recorded in Evidence as the intended fail-closed behaviour.
- The README's `deploy-gate` paragraph says how patterns are matched and where the guarantee ends; `intent.md` says where it ends; `skills/setup/SKILL.md` describes `gatedCommands` matching the same way.
- `CHANGELOG.md`'s `[Unreleased]` entry for `deploy-gate` describes matching from every program word.

## Evidence
