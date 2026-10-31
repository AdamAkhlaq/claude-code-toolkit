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

The regression test passes and the reported route behaves as expected: a gated command is blocked without authorisation wherever it sits in a Bash call, after `&&`, `;` or `|`, named by path, or inside `bash -c`, and a command that only mentions it in a quoted argument, such as `echo "git tag v1"`, is not. An unquoted mention, such as `echo git tag v1`, is blocked on purpose: a word outside quotes might name a program, and the gate fails closed.

The guarantee ends at what the Bash call says: a script fed to an interpreter, such as `echo 'git tag v1' | bash` or `bash release.sh`, is not read, nor is a word built from a variable, such as `git $t v1`, and a hard guarantee needs a permissions deny rule or withheld credentials.

A bug fix needs no spec or plan; this intent and its tickets are the change.

## Affected users and systems

Every consuming repo with `gatedCommands`, and every repo with a `feedbackCommand`: `red-guard` reads commands through the same shell tokeniser, so its view of which commands a Bash call runs changes too. Code: `hooks/scripts/deploy_gate.py` and the shell tokeniser in `hooks/scripts/_common.py`, which `red-guard` added in 0.5.0.

## Amendment 2026-10-24: building

The review of T1 found the fix opened new bypasses and left rewordings the outcome promises, so two tickets were appended: T2 (the shell reader keeps every command boundary) and T3 (a gated command is caught behind any prefix or inside a quoted substitution), three tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.

## Amendment 2026-10-24: three more tickets

The second review, of `a90e0c2`, found eight more ways past the gate, so T4 (the shell reader splits words where bash does), T5 (a substitution the shell runs is read whole, in a heredoc too) and T6 (the gate never fails open on a long or nested call) were appended: six tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.

## Amendment 2026-10-25: two more tickets

The third review, of `cd72334`, found five more ways past the gate, so T7 (the shell reader ends quotes, heredocs and substitutions where bash does) and T8 (a word is read as bash expands it, from ANSI-C quotes and braces, and `red-guard` blocks a commit it cannot read) were appended: eight tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.

## Amendment 2026-10-25: two more tickets, again

The fourth review, of `c96a43e`, found five regressions from T7 and T8 and one older gap, so T9 (the reader's own edges match bash, and every commit hook blocks a call it cannot read) and T10 (a substitution inside double quotes is read in its own quoting context) were appended: ten tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.

## Amendment 2026-10-30: one more ticket

The fifth review, of `74c8228`, found three regressions from T10, where `closing_paren` and `double_quoted` now decide where a double-quoted string ends and a misread hides the text after it, so T11 (a substitution inside double quotes ends where bash and zsh end it, or the call is blocked) was appended, taking the backlog line on an overrun failing closed: eleven tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.

## Amendment 2026-10-30: a twelfth ticket

The sixth review, of `a7e72cc`, found five `case` forms that T11's tracking in `closing_paren` does not model, four of them regressions from T11, and a `${...}` holding `)` was found while cutting the ticket, so T12 (a case or parameter form the reader does not model inside a substitution blocks the call) was appended: twelve tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.

## Amendment 2026-10-31: a thirteenth ticket

The seventh review, of `d0fb265`, found a regression from T12, where a backslash-newline inside single quotes was deleted before a `bash -c` or `eval` script was read, and three more `case` forms that the tracking in `closing_paren` opened or closed where the shells do not. T13 was appended to fix them. Under T13, any `case` inside a substitution blocks the call and the tracking is deleted, and a backslash-newline is deleted only where the shells delete it. The change now has thirteen tickets in one chain, executed `single` on `change/0003-fix-deploy-gate-bypass`.
