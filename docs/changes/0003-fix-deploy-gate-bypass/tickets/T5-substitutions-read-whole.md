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

### Evidence 2026-10-24 16:16

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 8.721s

OK
```

Each case was first run with `git` stubbed as a shell function, in macOS's bash 3.2.57 and in zsh: both shells ran `git tag` for the two unquoted heredocs and the quoted `)` case; the `case` inside `$(...)` ran in zsh, while bash 3.2 cannot parse it (bash 4 and later can); none of the three silent cases ran anything. The gate at `01a4aab` let all four through. The proving test was committed failing (`AssertionError: 0 != 2 : cat <<EOF⏎$(git tag v1)⏎EOF`), before any code change; I ran it in the same call as an earlier commit attempt, so `red-guard` checked and blocked that attempt, and the test was then committed on its own. After the fix the probe gave gated for all four and silent for the three. Edge cases checked: a nested `$(echo $(git tag v1))` in double quotes, a `case` with a `(a)` pattern, an escaped `\)`, a `<<-` heredoc, and `$(showcase ) ; git tag v3)`, where the substitution really ends at the first `)` and the rest is literal, so it stays silent.

The test case list holds two silent cases beyond the ticket's `proves` (`<<"EOF"` with a backtick body, and an unquoted heredoc whose body is a bare `git tag v1` line), which pin that a body is never read as commands itself.

Live check, 2026-10-24: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                               | Result                                                                                                                      |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `cat <<EOF`, `$(git tag v1)`, `EOF`                   | blocked: "Blocked: 'cat <<EOF⏎$(git tag v1)⏎EOF' matches gated command pattern '^git tag ' in .claude/toolkit.json."        |
| `echo "$(echo ")"; git tag v3)"`                      | blocked: "Blocked: 'echo \"$(echo \")\"; git tag v3)\"' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| `cat > literal.md <<'EOF'`, `$(git tag v9)`, `EOF`    | ran, `literal.md` holds the literal `$(git tag v9)`                                                                         |
| `cat > notes.md <<EOF`, `built on $(date +%Y)`, `EOF` | ran, `notes.md` holds `built on 2026`                                                                                       |

`git for-each-ref refs/tags` in the repo afterwards listed nothing.
