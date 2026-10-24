---
id: "0003"
slug: "fix-deploy-gate-bypass"
status: building
originator: "Adam Akhlaq"
accepted_by: "Adam Akhlaq"
created: "2026-10-23"
---

# Intent: a gated command is caught anywhere in the line

## Origin

Found while tagging v0.5.0, when the deploy gate blocked a read-only `git tag -l` that started the line. The report, as it was handed to `/toolkit:fix-bug`:

> deploy-gate matches gatedCommands regexes against the raw Bash command, so a gated command that is not at the start of the line gets past it: with gatedCommands ["^git tag ", "^gh release "], a command like `cd . && git tag v1` is expected to run without release authorisation. Found while tagging v0.5.0 on 2026-10-23; not yet reproduced.

The maintainer's words: "fix the deploy-gate gap with /toolkit:fix-bug".

## Problem

`deploy-gate` runs each pattern in `gatedCommands` with `re.search` against the whole Bash command (`hooks/scripts/deploy_gate.py:36`). Patterns are written to match the start of a command, as `^git tag ` and `^gh release ` are in this repo and as the README's examples are, so a gated command that is not the first thing on the line, or that names its program by path, runs without release authorisation. The gate is the one-way-door guard, and an agent that was blocked can get past it by rewording.

Reproduced on 2026-10-23 in a headless Claude Code session (`claude --plugin-dir <copy of main> -p --permission-mode bypassPermissions`) against a throwaway repo with `"gatedCommands": ["^git tag ", "^gh release "]`, no `RELEASE_AUTHORIZED` and no marker:

| Command               | Result                                                                                              |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| `git tag v1`          | blocked: "Blocked: 'git tag v1' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| `cd . && git tag v2`  | ran, printed nothing                                                                                |
| `true; git tag v3`    | ran, printed nothing                                                                                |
| `/usr/bin/git tag v4` | ran, printed nothing                                                                                |

`git tag -l` in the repo afterwards listed `v2`, `v3`, `v4`.

## Proposed outcome

The regression test passes and the reported route behaves as expected: a gated command is blocked without authorisation wherever it sits in a Bash call, after `&&`, `;` or `|`, named by path, or inside `bash -c`, and a command that only mentions it in an argument, such as `echo "git tag v1"`, is not.

The guarantee ends at what the Bash call says: a script fed to an interpreter, such as `echo 'git tag v1' | bash` or `bash release.sh`, is not read, and a hard guarantee needs a permissions deny rule or withheld credentials.

A bug fix needs no spec or plan; this intent and its one ticket are the change.

## Affected users and systems

Every consuming repo with `gatedCommands`, and every repo with a `feedbackCommand`: `red-guard` reads commands through the same shell tokeniser, so its view of which commands a Bash call runs changes too. Code: `hooks/scripts/deploy_gate.py` and the shell tokeniser in `hooks/scripts/_common.py`, which `red-guard` added in 0.5.0.

## Amendment 2026-10-24: building

The review of T1 found the fix opened new bypasses and left rewordings the outcome promises, so two tickets were appended: T2 (the shell reader keeps every command boundary) and T3 (a gated command is caught behind any prefix or inside a quoted substitution), three tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.
