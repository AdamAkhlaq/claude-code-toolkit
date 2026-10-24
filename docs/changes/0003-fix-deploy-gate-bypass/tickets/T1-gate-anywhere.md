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
    docs/changes/0003-fix-deploy-gate-bypass/intent.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_gated_command_is_caught_anywhere_in_the_line: with gatedCommands ["^git tag ", "^gh release "], deploy_gate.py exits 2 on `cd . && git tag v2`, `true; git tag v3`, `/usr/bin/git tag v4`, `bash -c "git tag v5"`, `git fetch -q && gh release create v6`, `git tag v7` on the line after `git fetch -q`, `git tag v8` on the line after a heredoc ends, and `git tag v9` and `git tag v10` on the line after a quoted `<<EOF` and a here-string, and exits 0 silently on `echo "git tag v1"`, `git log --grep ''git tag ''`, an `echo` whose quoted argument has `git tag v1` on its second line, and a heredoc whose body mentions `git tag v1` and `/usr/bin/git tag v2`'
status: in-progress
executed_by: single
branch: change/0003-fix-deploy-gate-bypass
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

### Evidence 2026-10-24 13:20

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
......................................................................
----------------------------------------------------------------------
Ran 70 tests in 14.344s

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

### Verifier 2026-10-24 13:19

Verdict: reopen
Checks:

1. ticket integrity: frontmatter has no `executed_by` and no `branch`; `id`, `title`, `blocked_by`, `files`, `proves`, `status: in-progress` and a quoted feedback command run are present.
2. proving test present and meaningful: ok. `DeployGateTests.test_a_gated_command_is_caught_anywhere_in_the_line` was added on this branch in c72ed2b, drives `deploy_gate.py` as a subprocess (the seam the ticket names), and asserts exit 2 on each gated case and `(0, "", "")` on each mention. Run against main's `hooks/scripts` with the branch's tests in a scratch copy it fails with `AssertionError: 0 != 2 : cd . && git tag v2`, and the added red-guard case fails with `AssertionError: 0 != 2 : git status`.
3. proving test run: exit 0, `Ran 1 test in 0.330s OK` (`python3 -m unittest tests.test_hooks.DeployGateTests.test_a_gated_command_is_caught_anywhere_in_the_line`).
4. feedback command: exit 0, `Ran 70 tests in 7.402s OK` (`python3 -m unittest discover -s tests`).
5. acceptance: 3 of 4 checked, all 3 pass; 1 unchecked.
   - The proving test passes: checked by check 3, pass.
   - The existing `DeployGateTests` pass unchanged: `git diff main...HEAD -- tests/` adds one method to `DeployGateTests` and touches none of the other three; `python3 -m unittest tests.test_hooks.DeployGateTests` ran 4 tests, OK.
   - `python3 -m unittest discover -s tests` passes: checked by check 4, pass.
   - Re-running the reproduction in `intent.md` blocks all four commands and creates no tag: unchecked the reporter's way. Launching a headless `claude --plugin-dir . -p --permission-mode bypassPermissions` session was refused by the verifier's permissions, so the executor's session table above is not reproduced. Partial check only: the four commands fed as PreToolUse events to `hooks/scripts/deploy_gate.py` with `CLAUDE_PROJECT_DIR` at a throwaway project (`gatedCommands` `["^git tag ", "^gh release "]`, no `RELEASE_AUTHORIZED`, no marker) each exited 2 with "Blocked: '<command>' matches gated command pattern '^git tag ' in .claude/toolkit.json."; the commands were not executed, so "creates no tag" was not observed.
6. scope: `docs/changes/0003-fix-deploy-gate-bypass/intent.md` is changed on the branch and not in `files`. Every other changed file (`CHANGELOG.md`, `README.md`, `hooks/scripts/_common.py`, `hooks/scripts/deploy_gate.py`, `skills/setup/SKILL.md`, `tests/test_hooks.py`) is in the list.
7. tests intact: ok. `tests/test_hooks.py` is +21 -2; the two removed lines are red-guard tuples re-added with one extra case each; no assertion removed, no skip or expected-failure marker, no expected value loosened.

Reopen reason: add `executed_by` and `branch` to the ticket frontmatter and `intent.md` to `files`, then have the headless-session reproduction re-run by someone permitted to launch it, since this verifier could not reproduce it.
