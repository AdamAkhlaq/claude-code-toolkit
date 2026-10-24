---
id: T5
title: A substitution the shell runs is read whole, in a heredoc too
blocked_by: [T4]
files:
  [
    hooks/scripts/deploy_gate.py,
    hooks/scripts/_common.py,
    tests/test_hooks.py,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_substitution_the_shell_runs_is_read_whole: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `cat <<EOF` with `$(git tag v1)` as its body, the same with a backticked `git tag v2`, `echo "$(echo ")"; git tag v3)"` and `echo "$(case a in a) git tag v4;; esac)"`, and exits 0 silently on `cat <<''EOF''` with `$(git tag v1)` as its body'
status: in-progress
executed_by: single
branch: ticket/0003-T5
---

## Context

From the second review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-24 of a90e0c2"): Importants at `deploy_gate.py:42` (unquoted heredoc bodies) and `deploy_gate.py:116` (`closing_paren`). Execution mode is `single`.

`deploy_gate.substitutions` scans `shell_source(command)`, which drops every heredoc body. Bash runs `$(...)` and backticks in the body of a heredoc whose delimiter is unquoted (`<<EOF`), and leaves the body literal when the delimiter is quoted (`<<'EOF'`, `<<"EOF"`, `<<\EOF`). Keep the bodies of unquoted-delimiter heredocs available to the substitution scan, for example by having `_common` return them beside the shell source, and scan them as double-quoted text. They must still not be read as commands themselves: a body line that only says `git tag v1` stays silent, as T1's heredoc case pins.

`closing_paren` counts every `(` and `)`, so a `)` inside quotes, or a `case` pattern's `)`, ends the substitution early and the command after it is lost. Skip quoted text and backslash pairs when counting, and treat a `case ... esac` inside the span as balanced, or, simpler and fail-closed, when the count cannot be trusted, read to the end of the enclosing quoted word.

Seam: the hook script as a subprocess. Write the proving test first and commit it failing before any code change. Confirm each case in bash with a stub `git` function first; macOS's bash 3.2 cannot parse a `case` inside `$(...)`, which bash 4 and later do, so check that case with a newer bash or zsh if one is installed and say which in Evidence.

## Acceptance

- The proving test passes.
- T1's, T2's and T3's proving tests and every other test in `tests/` pass unchanged.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry says a substitution in an unquoted heredoc is read.

## Evidence
