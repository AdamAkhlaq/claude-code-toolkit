---
id: T1
title: A gated command is caught anywhere in the line
blocked_by: []
files:
  [
    hooks/scripts/deploy_gate.py,
    hooks/scripts/_common.py,
    tests/test_hooks.py,
    README.md,
    CHANGELOG.md,
    skills/setup/SKILL.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_gated_command_is_caught_anywhere_in_the_line: with gatedCommands ["^git tag ", "^gh release "], deploy_gate.py exits 2 on `cd . && git tag v2`, `true; git tag v3`, `/usr/bin/git tag v4`, `bash -c "git tag v5"`, `git fetch -q && gh release create v6`, `git tag v7` on the line after `git fetch -q` `git tag v8` on the line after a heredoc ends, and `git tag v9` and `git tag v10` on the line after a quoted `<<EOF` and a here-string, and exits 0 silently on `echo "git tag v1"`, `git log --grep ''git tag ''`, an `echo` whose quoted argument has `git tag v1` on its second line, and a heredoc whose body mentions `git tag v1` and `/usr/bin/git tag v2`'
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

### Evidence 2026-10-24 13:13

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
......................................................................
----------------------------------------------------------------------
Ran 70 tests in 14.202s

OK
```

The tokeniser change also reaches `red-guard`, pinned by two cases added after the fix to `RedGuardTests.test_a_command_that_can_change_files_before_its_commit_always_runs_the_check`: `git status`, `sed -i '' s/0/1/ app.py` and `git commit -am x` on three lines runs the check (without the fix it failed with `AssertionError: 0 != 2`), and a `git commit -F - <<'EOF'` whose message has parentheses passes.

Reproduction from `intent.md`, re-run the reported way on 2026-10-24: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag ", "^gh release "]`, no `RELEASE_AUTHORIZED` and no marker, asked to run each command in its own Bash call.

| Command                                                                                | Result                                                                                                                       |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `git tag v1`                                                                           | blocked: "Blocked: 'git tag v1' matches gated command pattern '^git tag ' in .claude/toolkit.json."                          |
| `cd . && git tag v2`                                                                   | blocked: "Blocked: 'cd . && git tag v2' matches gated command pattern '^git tag ' in .claude/toolkit.json."                  |
| `true; git tag v3`                                                                     | blocked: "Blocked: 'true; git tag v3' matches gated command pattern '^git tag ' in .claude/toolkit.json."                    |
| `/usr/bin/git tag v4`                                                                  | blocked: "Blocked: '/usr/bin/git tag v4' matches gated command pattern '^git tag ' in .claude/toolkit.json."                 |
| `git fetch -q 2>/dev/null`, then `git tag v7` on the next line                         | blocked: "Blocked: 'git fetch -q 2>/dev/null⏎git tag v7' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| `cat > notes.md <<'EOF'` with a body mentioning `git tag v1` and `/usr/bin/git tag v2` | ran, `notes.md` written with the body                                                                                        |
| `echo "a <<EOF"`, then `git tag v9` on the next line                                   | blocked: "Blocked: 'echo \"a <<EOF\"⏎git tag v9' matches gated command pattern '^git tag ' in .claude/toolkit.json."         |

`git for-each-ref refs/tags` in the repo afterwards listed nothing.
