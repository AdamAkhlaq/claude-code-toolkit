---
id: T2
title: The shell reader keeps every command boundary
blocked_by: [T1]
files:
  [
    hooks/scripts/_common.py,
    tests/test_hooks.py,
    CHANGELOG.md,
    docs/changes/0003-fix-deploy-gate-bypass/intent.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_shell_reader_keeps_every_command_boundary: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `git tag v1` to `git tag v4` on the line after, in turn, `true # note`, `echo $((1<<2))`, `# see <<EOF` and a `cat <<EOF` whose closing `EOF` never comes, and on `true;>out git tag v5`, `true&&>/dev/null git tag v6`, `` echo `git tag v7` `` and `echo $''it\''s''; git tag v8`'
status: in-progress
executed_by: single
branch: ticket/0003-T2
---

## Context

From the review of T1 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`), Importants 1, 2, 3 and 6 and the backtick half of 5. This is a `fix-bug` change, so there is no spec or plan; the review's findings and its Decisions section are the requirements. Execution mode is `single`, in the main working tree on `change/0003-fix-deploy-gate-bypass`.

T1 made `_common.shell_tokens` keep a newline as a control operator and drop heredoc bodies. Three of those changes let a later line hide: a `#` comment read by shlex's default commenter swallows the newline after it; `<<` as an arithmetic shift (`$((1<<2))`) or inside a comment is read as a heredoc whose closing line never comes, and every line after it is dropped; and shlex merges a separator with a following redirect into one token (`;>`, `&&>`), which `deploy_gate.simple_commands` reads only as a redirect. Separately, a backtick is a word character to shlex, and on a quoting error shlex rejects (`$'it\'s'`, which bash accepts) the tokeniser falls back to `command.split()`, which loses every operator.

Fix them in the shared reader, not in `deploy_gate.py`: turn shlex's commenter off and drop `#` comments (a `#` that starts a word, outside quotes) in the quote-aware pre-scan, keeping the newline; ignore `<<` inside `$((`...`))` and `((`...`))`; keep a heredoc's body when its closing delimiter never comes; split a token that holds both a separator (`;|&` or a newline) and a redirect character so the separator survives; make the backtick an operator; and fall back on a quoting error to a split that keeps operators as tokens. The same reader feeds `red-guard` through `is_git_commit` and `only_bookkeeping`, and on this branch `is_git_commit("echo $((1<<2))\ngit commit -am x")` is False where main says True.

Seam: each hook script as a subprocess, as the other `DeployGateTests` and `RedGuardTests` do. Write the proving test first and commit it failing, before any code change. `CLAUDE.md` now says never to recognise a shell command in a hook from the raw string.

## Acceptance

- The proving test passes.
- `RedGuardTests` gains a case: with a red feedback command and a changed source file, `git commit -am x` on the line after `echo $((1<<2))` is blocked. It is committed failing with the proving test.
- T1's proving test and every other test in `tests/` pass unchanged.
- `intent.md`'s "Affected users and systems" names `red-guard` and `hooks/scripts/_common.py`.
- `CHANGELOG.md`'s `[Unreleased]` entry for the tokeniser describes comments, arithmetic, unterminated heredocs, merged separators, backticks and the fallback.

## Evidence

### Evidence 2026-10-24 15:38

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
........................................................................
----------------------------------------------------------------------
Ran 72 tests in 8.317s

OK
```

The proving test and `RedGuardTests.test_a_shift_in_arithmetic_does_not_hide_the_commit_after_it` were committed failing in `310cb8e`, before any code change: every one of the eight `deploy_gate.py` cases exited 0, and the red-guard case failed with `AssertionError: 0 != 2`.

Live check, 2026-10-24: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                              | Result                                                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `true # note`, then `git tag v1` on the next line    | blocked: "Blocked: 'true # note⏎git tag v1' matches gated command pattern '^git tag ' in .claude/toolkit.json."    |
| `echo $((1<<2))`, then `git tag v2` on the next line | blocked: "Blocked: 'echo $((1<<2))⏎git tag v2' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| `true;>out git tag v5`                               | blocked: "Blocked: 'true;>out git tag v5' matches gated command pattern '^git tag ' in .claude/toolkit.json."      |
| `` echo `git tag v7` ``                              | blocked: "Blocked: 'echo \`git tag v7\`' matches gated command pattern '^git tag ' in .claude/toolkit.json."       |
| `echo "#" > note.txt`                                | ran, `note.txt` written                                                                                            |

`git for-each-ref refs/tags` in the repo afterwards listed nothing.
