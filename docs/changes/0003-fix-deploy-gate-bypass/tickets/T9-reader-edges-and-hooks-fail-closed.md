---
id: T9
title: The reader's own edges match bash, and every commit hook blocks a call it cannot read
blocked_by: [T8]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    hooks/scripts/red_guard.py,
    hooks/scripts/secret_guard.py,
    hooks/scripts/ticket_sync.py,
    tests/test_hooks.py,
    README.md,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_reader_reads_its_own_edges_as_bash_does: with gatedCommands ["^git tag "], deploy_gate.py exits 2 as a gated command on `echo $''\c''; git tag v2; echo ''x''`, `echo {W..a..5}''x''; git tag v3; echo ''y''` and on `cat <<$''EOF''`, `EOF`, `git tag v4` and `$EOF` on four lines, exits 2 with a message saying bash and zsh read the call differently on `echo $$''\'' ; git tag v1 ; echo "''"` and on `cat <<$"EOF"`, `EOF`, `git tag v4` and `$EOF` on four lines, and exits 0 silently on `echo $$''git tag v5''` and on `cat <<$''EOF''`, `git tag v6` and `EOF` on three lines; in RedGuardTests.test_reworded_commits_are_recognised, red_guard.py blocks with the feedback output on the `$''\c''`, range and heredoc shapes with `git commit -am x` in place of the tag, and blocks with a message starting "Blocked: red-guard could not read" on the `$$''\''` shape and on a call past the brace limit that commits nothing; and in SecretGuardTests.test_a_commit_it_cannot_read_is_blocked and TicketSyncTests.test_a_commit_it_cannot_read_is_blocked, secret_guard.py with an AWS key staged and ticket_sync.py with a change in progress each exit 2 on `git commit -m x; echo ` followed by 14 `{a,b}` groups, with a message naming the hook and no traceback'
status: in-progress
executed_by: single
branch: ticket/0003-T9
---

## Context

From the fourth review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-25 of c96a43e"): the Importants at `_common.py:450`, `_common.py:179`, `_common.py:358`, `_common.py:387` and `secret_guard.py:72`, the Nits at `red_guard.py:150` and `README.md:71`, and the Decisions taken at that review. Every one is a regression from T7 or T8: at `cd72334` each bypass below was blocked and secret-guard scanned the commit. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

Four places where the new reader code misreads its own edges, so a quote or a heredoc ends somewhere bash does not, and one place where the hooks fail open:

- `shell_source` reads any `$'` as an ANSI-C quote, including the second `$` of `$$` (the shell's PID), after which bash reads a plain `'...'`. Take `$$` as one unit before testing for `$'`.
- `ANSI_C_NUMBER`'s `c(.)` takes the closing `'` of `$'\c'` as the control character, so the reader stays inside a quote bash has closed. `\c` never takes the closing quote.
- `sequence` writes the characters a letter range covers straight back into source text that is read again, so `{W..a..5}` puts a bare `` ` ``, `\` and the like into it and shifts every quote after it. `/bin/bash` 3.2 and `/bin/zsh` leave a range whose ends differ in case as written. Expand a letter range only when both ends are the same case, and quote every character any range produces, so no expansion can open or close a quote. Check what each shell does with a step on a letter range before deciding to expand one.
- `heredoc_at` reads `<<$'EOF'` as delimiter `$EOF`, but bash and zsh close it at a line `EOF`, so lines after that close are hidden as body. Apply bash's quote removal to the delimiter: a `$` right before a `'` or `"` goes, as for `$"EOF"`. The delimiter stays quoted, so its body is literal.
- `is_git_commit` can raise `Unreadable` since T8, and `secret_guard.main` (line 72) and `ticket_sync.main` (line 49) call it unguarded, so a call past the brace limit crashes them with exit 1, which Claude Code treats as a non-blocking error: a commit with a staged secret runs unscanned. Catch any reader error there as `red_guard.main` does and block with a message naming the hook and no traceback. Both stay silent without `.claude/toolkit.json`, as `NoConfigTests` pins; ticket-sync, which acts on nothing when no change is in progress, stays silent then too. An event that is not JSON still exits 0.
- `red_guard.main` says "Commit stopped" when it cannot read a call, though the call may commit nothing. Start that message "Blocked: red-guard could not read this Bash call".

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check each form's whole family in `/bin/bash` and `/bin/zsh` with a stub `git` printing to stderr before fixing it (other `$`-prefixed quotes such as `$$"`, `$"..."` and `$$$'`; every `\c` and numeric escape at the end of a `$'...'`; ranges whose ends or step produce quote, backslash, backtick, `$`, brace or operator characters; `<<$"EOF"`, `<<-$'EOF'` and a `$` inside the delimiter word), and probe each fix's own boundaries the same way before handing it on. Add every member that gets past a hook to the proving test before the fix.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged, apart from cases added to them.
- `NoConfigTests.test_every_hook_is_silent_without_config` has cases for `secret-guard` and `ticket-sync` with a call past the brace limit.
- The README's `red-guard` row says it also blocks a Bash call it cannot read where a `feedbackCommand` is set, and its `secret-guard` and `ticket-sync` rows say they block a commit they cannot read.
- `CHANGELOG.md`'s `[Unreleased]` entries say that `secret-guard` and `ticket-sync` block a commit they cannot read.

## Evidence

### Evidence 2026-10-25 22:10

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
...................................................................................
----------------------------------------------------------------------
Ran 83 tests in 13.958s

OK
```

Per `CLAUDE.md`, each form's family was checked first in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` printing to stderr, and every member that got past a hook went into the proving test, committed failing before the code changed (ac21c50). The check changed two of the ticket's instructions:

- bash and zsh read `$$'` differently: bash takes `$$` as the PID and a plain quote after it, zsh a `$'...'` quote. Following bash alone, as the ticket said, would have let `echo $$'\'' ; git tag v1` through in zsh, which runs it, and it was blocked before. The same split holds for heredoc delimiters: bash ends `<<$"EOF"` at a line `EOF` and zsh at `$EOF`, and `<<$$'EOF'` at `$$EOF` and `$EOF`. The maintainer decided at this ticket that the hooks fail closed exactly where the two shells disagree, and `proves` was amended in the test commit to say so.
- Both shells do expand a letter range whose ends differ in case: `{W..a}` gives `W`, `X`, `Y`, `Z`, then `[`, a backslash, `]`, `^`, `_`, a backtick, and `a`. What kept `{W..a..5}` literal was the step, which bash 3.2 never takes and zsh takes only on numbers. Not expanding mixed case would itself miss a word the shells build, so instead every character a range produces that is not a letter or digit is escaped.

Family members added to the test beyond the ticket's cases: `$'a\c'`, `$'\c\\'` and `$'\c\''` (both shells pair every backslash when they look for the closing quote, so `$'\c\\'` closes at its last quote too), `{Z..a}` with either kind of quote after it, `{a..W}` and `{A..z..1}`, `<<-$'EOF'`, `<<E$'OF'` and `<<$'E\x4fF'` (both shells decode the span), and an unquoted heredoc body holding `$'$(git tag v4)'`, `` $'x' `git tag v4` `` or `$$'$(git tag v4)'`. That last group was the `$'` branch in `deploy_gate.substitutions`, which read a quote in a heredoc body, where quotes are literal; with every real `$'...'` already decoded by `shell_source`, the branch is gone, and `deploy_gate.py` was added to `files`. Blocked as read differently: `$$'\'`, `$$$$'\'`, `a$$'\'`, `x=$$'\'`, `$$'\''`, `<<$"EOF"` both ways round, and `<<$$'EOF'`.

The fix, in `_common`:

- `shell_source` finds a `$'...'` span's closing quote first, pairing each backslash with the character after it as both shells do, and only then decodes the text between (`ansi_c_text`), so no escape can take the closing quote. A run of `$` before a quote is read whole (`dollar_run`): an odd run ends in a `$'...'` span; after an even run the quote is plain in bash, and where a backslash comes before its close, so that zsh would end it elsewhere, the call raises `ShellsDiffer`, a kind of `Unreadable`.
- `heredoc_at` decodes a `$'...'` span in a delimiter and raises `ShellsDiffer` for `$"` or a run of `$` before a quote. `shell_source` writes a quoted delimiter back as one plain single-quoted word, so the readers after it never meet the `$'` again.
- `sequence` escapes each character it produces that is not a letter or digit.
- `secret-guard` and `ticket-sync` catch a reader error around `is_git_commit` and block, naming the hook, with the reason when the shells differ; `ticket-sync` stays silent when no change is in progress, and both stay silent without `toolkit.json` (cases added to `NoConfigTests`). `red-guard`'s message now starts "Blocked: red-guard could not read this Bash call". `deploy-gate` says "bash and zsh read ... differently" for `ShellsDiffer` and keeps its too-long message for the rest.

Boundaries of the new code, probed the same way, all blocked or silent as bash and zsh run them: `"$$'"`, `${#}$'\''`, `$((1))$'\x41\''`, `$$${x}`, an unclosed `$'` over three lines, `$'\0'`, `$'a\0b\'c'`, `<<$'E'\''F'`, `<<$'EOF'x`, `<<x$'E\'F'`, `<<$'E OF'`, an unclosed `<<$'EOF`, a `$(...)` after a decoded or quoted delimiter on the same line, `{Z..a}{a..c}`, `{1..-1}`, a quoted `"{Z..a}"`, `$'\x27'`, `$'\047'` and `$$$'\x27'`. The forms from T7, T8 and the fourth review that still get past are the nested-quote family, which is T10, and commits inside a substitution that `red-guard` does not read, recorded in `docs/backlog.md`.

Timing through `deploy-gate`, all under 1.1 s: 290,000 `$` with no quote after them (an early draft rescanned the run from every `$`, which is quadratic, so a run is now taken once), the same before a quote, the same as a heredoc delimiter, 70,000 `$'a'`, 55,000 `$$'a'` and 900 `{Z..a}'x'`. `claude plugin validate .` passes with the same warnings as before this branch.

Live check, 2026-10-25: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]`, an AWS key staged, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                   | Result                                                                                            |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `echo $'\c'; git tag v1; echo 'x'`        | blocked: "Blocked: 'echo $'\c'; git tag v1; echo 'x'' matches gated command pattern '^git tag '"  |
| `echo {W..a..5}'x'; git tag v2; echo 'y'` | blocked: "Blocked: 'echo {W..a..5}'x'; git tag v2; echo 'y'' matches gated command pattern '^git" |
| `echo $$'\'' ; git tag v3`                | blocked: "Blocked: bash and zsh read $$'\' differently: bash as a plain quote after $$, zsh as a" |
| `git commit -m x; echo ` and 14 `{a,b}`   | blocked by `deploy-gate` as too long to read                                                      |
| `mkdir -p src/{a,b} && ls src`            | ran, printed `a` and `b`                                                                          |

The same commit in a second repo whose `toolkit.json` has no `gatedCommands` was blocked by `secret-guard`: "Blocked: secret-guard could not read this Bash call (Unreadable), so it cannot tell whether it commits a secret. Split or rephrase it." `git for-each-ref refs/tags` listed nothing in the first repo, and neither log held more than its first commit.
