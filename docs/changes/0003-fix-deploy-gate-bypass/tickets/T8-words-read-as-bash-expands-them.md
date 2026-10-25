---
id: T8
title: A word is read as bash expands it, from ANSI-C quotes and braces
blocked_by: [T7]
files:
  [
    hooks/scripts/_common.py,
    hooks/scripts/deploy_gate.py,
    hooks/scripts/red_guard.py,
    tests/test_hooks.py,
    README.md,
    CHANGELOG.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_word_is_read_as_bash_expands_it: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `$''\x67it'' tag v1`, `$''\147it'' tag v2`, `{git,tag} v3`, `git {tag,v4}`, `{git,} tag v5` and `{g..g}it tag v6`, exits 2 with a message saying the call is too long to read on a word whose braces expand to more than 10000 words, and exits 0 silently on `echo ''{git,tag} v1''`, `{ echo git; }`, `gi{t,} tag v5` and `{f..h}it tag v6`, which bash runs as `git gi tag v5` and `fit git hit tag v6`; and in RedGuardTests, red_guard.py blocks with the feedback output on `$''\x67it'' commit -am x` and `git {commit,-am,x}`, and blocks with a message naming red-guard, not a traceback, on a commit whose braces expand to more than 10000 words'
status: done
executed_by: single
branch: ticket/0003-T8
---

## Context

From the third review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-25 of cd72334"): the Important at `deploy_gate.py:73` and the Decision that the reader decodes `$'...'` and expands an unquoted `{a,b}`, so a program word is read as bash sees it. Parameter expansion (`$t`, `${IFS}`) stays a stated limit and is out of scope. Execution mode is `single`, on `change/0003-fix-deploy-gate-bypass`.

`shell_tokens` takes words literally, so `$'\x67it'` stays `$\x67it` and `{git,tag}` stays one word, and bash runs `git tag` for both. Bash expands braces first, then quotes; both must be done on the shell source before shlex removes quotes, since a quoted `'{git,tag}'` and `$'{a,b}'` are not expanded:

- Decode `$'...'` as bash does (`\xHH`, `\NNN` octal, `\uHHHH`, `\n`, `\t`, `\\`, `\'`, `\"`, `\e`, `\cX` and the rest) into an equivalent single-quoted span, writing a `'` in it as `'\''`. Python's `unicode_escape` codec differs from bash on several of these; do not rely on it unchecked.
- Expand an unquoted brace expression in a word: a comma list (`{git,tag}`, `gi{t,}`, nested `{a,{b,c}}`) and a sequence of integers or single letters (`{f..h}`, `{1..3}`, with an optional step). A brace with no top-level comma or `..` is literal, as are `{ cmd; }` groups, `${...}` and a `{` after `$`. The expansion multiplies across a word, so it is bounded: past 10000 words from the call's braces, reading stops with an error. Do not raise `ValueError`, which `shell_tokens` catches to fall back.

Fail closed on that error in both hooks. `deploy-gate` already blocks on any read error; say "too long to read" for this one. `red_guard.main` returns 0 when `is_git_commit` raises, which lets a commit through when the reader cannot finish: make a reader error block there, with a message naming red-guard, while an event that is not JSON still exits 0 silently, as `test_a_fault_blocks_a_commit_readably_and_never_blocks_other_commands` pins. `secret-guard` and `ticket-sync` call `is_git_commit` too; read what they do on the error and record it in Evidence.

Seam: the hook scripts as subprocesses. Write the proving test first and commit it failing before any code change. Per `CLAUDE.md`, check each form's whole family in bash with a stub program before fixing it, and add every member that gets past the gate to the proving test before the fix.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged.
- The README's `deploy-gate` paragraph says `$'...'` and braces are read as bash expands them, and the `CHANGELOG.md` `[Unreleased]` entries for `deploy-gate` and `red-guard` say so too, and that `red-guard` blocks a commit it cannot read.

## Evidence

### Evidence 2026-10-25 17:45

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
................................................................................
----------------------------------------------------------------------
Ran 80 tests in 14.733s

OK
```

Per `CLAUDE.md`, each form's family was checked first in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` printing to stderr. Every member that got past the gate went into the proving test, committed failing before the code changed (a025845): `$'\x67it'`, `$'\147it'`, `$'git'`, `$'\U00000067it'`, `g$'\x69't`, `git $'\x74ag'`, `$'git\0xyz'` (bash ends the word at the NUL), `eval $'\x67it tag v2'`, `bash -c $'\x67it tag v2'`, `{git,tag}`, `git {tag,v4}`, `{git,}`, `{,git}`, `{g..g}it`, `{git,tag,v6}` and `{{git,tag},v6}`. Two of the cases the ticket named were not bypasses: bash runs `gi{t,} tag v5` as `git gi tag v5` and `{f..h}it tag v6` as `fit git hit tag v6`, so neither runs a tag. They are pinned as calls that pass silently, `{git,} tag v5` and `{g..g}it tag v6` took their place, and `proves` was amended in the same commit to say so.

The fix, in `_common`, so both hooks read the same words:

- `shell_source` decodes each escape in `$'...'` as bash does (`ansi_c_escape`: the letter escapes, `\nnn` octal, `\xHH`, `\uHHHH`, `\UHHHHHHHH`, `\cX`) into the plain single-quoted span T7 writes, and a NUL ends the word's text at the span's close (`ansi_c_close`).
- `shell_tokens` expands braces before shlex removes quotes (`expand_braces`): a comma list, nested lists, and `{x..y[..step]}` sequences of integers (zero-padded when an end is) or single letters. A quoted or escaped brace, `${...}`, `{ ...; }`, `{}` and any brace with no top-level comma or sequence stay literal, and the braces inside a literal one are still expanded, as bash does (`{a{b,c}}` reads `{ab} {ac}`). Each word's braces are paired once with a stack and expanded over index ranges, so a word is read in one pass however it nests: an earlier version that rescanned from every `{` would have been quadratic on a word of 290000 `{`.
- Expansion is bounded: past `BRACES` (10,000) words, or `BRACE_CHARACTERS` (1,000,000) characters, counted before each product is built, the call is `Unreadable`, now defined once in `_common` and imported by `deploy-gate`, whose too-long message names the brace limit. A brace nesting too deep for Python's recursion is read as too long as well.
- `red_guard.main` blocks a call whose reading raises, naming red-guard, instead of returning 0, but only in a project whose `toolkit.json` has a `feedbackCommand`: without one it stays silent, which `NoConfigTests.test_every_hook_is_silent_without_config` now pins for `red-guard` and for `deploy-gate` with a call past the brace limit (cases added; nothing removed). An event that is not JSON still exits 0 silently.

What the other hooks do on the error, recorded as the ticket asks: `secret-guard` and `ticket-sync` call `is_git_commit` unguarded, so a call past the brace limit crashes them with `_common.Unreadable`, exit 1, which Claude Code treats as a non-blocking error and lets the call run. Where a `feedbackCommand` is set, `red-guard` blocks that call first; without one, `secret-guard` lets an unreadable commit through. Recorded for its own ticket.

Timing through the hook, all decided within 1.3 s: 290000 `{` in one word (exit 0, 1.3 s, shlex's square cost of one long word), 2000 nested lists (exit 2), 49000 `{1..1}` (exit 2), `{1..100000000}` (exit 2 in 0.0 s, counted before it is built), a list of 12000 alternatives (exit 2), 4000 words of `a{b,c}` before a tag (exit 2), 70000 `\x41` escapes (exit 2), and a NUL followed by 200000 characters (exit 2). The T6 adversarial shapes and T7's timing shapes are unchanged. Calls that must run, run: `mkdir -p src/{a,b} && cp app.py{,.bak}`, `find . -exec rm {} \;`, `echo {01..03} {a..e..2} {3..1}`, and quoted braces. `claude plugin validate .` passes with the same warnings as before this branch.

Live check, 2026-10-25: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag "]` and `"feedbackCommand": "echo boom-red; exit 1"`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                               | Result                                                                                                    |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `$'\x67it' tag v1`                    | blocked: "Blocked: '$'\x67it' tag v1' matches gated command pattern '^git tag ' in .claude/toolkit.json." |
| `{git,tag} v2`                        | blocked: "Blocked: '{git,tag} v2' matches gated command pattern '^git tag ' in .claude/toolkit.json."     |
| `git {tag,v3}`                        | blocked: "Blocked: 'git {tag,v3}' matches gated command pattern '^git tag ' in .claude/toolkit.json."     |
| `$'\x67it' commit --allow-empty -m x` | blocked by `red-guard`: "Commit stopped: the feedback command is red."                                    |
| `mkdir -p src/{a,b} && ls src`        | ran, created `src/a` and `src/b`                                                                          |

`git for-each-ref refs/tags` afterwards listed nothing, and the log still held only the first commit.

### Verifier 2026-10-25 17:47

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `DeployGateTests.test_a_word_is_read_as_bash_expands_it` was added on this branch (a025845), and the two `RedGuardTests.test_reworded_commits_are_recognised` cases and the brace-limit block were added to it. Run against the integration branch's hooks with this branch's `tests/test_hooks.py`, both fail: `AssertionError: 0 != 2 : $'\x67it' tag v1` and `AssertionError: 0 != 2 : $'\x67it' commit -am x`.
3. proving test run: exit 0, `python3 -m unittest tests.test_hooks.DeployGateTests.test_a_word_is_read_as_bash_expands_it tests.test_hooks.RedGuardTests.test_reworded_commits_are_recognised tests.test_hooks.NoConfigTests -v`: "Ran 4 tests in 2.852s OK"
4. feedback command: exit 0, `python3 -m unittest discover -s tests`: "Ran 80 tests in 14.925s OK"
5. acceptance: 3 of 3 checked. Proving test passes (check 3). Every other test passes (check 4); the only test edits are added cases, no lines removed. README `deploy-gate` paragraph and the CHANGELOG `[Unreleased]` `deploy-gate` and `red-guard` entries read in the diff and say what the line asks, including that `red-guard` blocks a commit it cannot read.
6. scope: ok. Changed: `CHANGELOG.md`, `README.md`, `hooks/scripts/_common.py`, `hooks/scripts/deploy_gate.py`, `hooks/scripts/red_guard.py`, `tests/test_hooks.py` and the ticket, all in `files`.
7. tests intact: ok. No removed lines, skips or expected-failure markers in `git diff change/0003-fix-deploy-gate-bypass...HEAD -- tests/`.

Independent probe, from a mktemp directory, of 19 calls run in `/bin/bash` with a stub `git` and through `deploy_gate.py` with `["^git tag "]`: every call bash ran as `git tag <arg>` was blocked (`$'\x67it' tag v1`, `{git,tag} v3`, `{g..g}it tag v6`, `""{git,tag} v1`, `x=1 {git,tag} v1`, `$'\147\151\164' tag v1`, `{{git,tag},v6}`, `git {,tag} v1`, `{git,tag,} v1`). `{git,tag,}` with no further word runs a bare `git tag`, which the pattern's trailing space does not match even written literally (`git tag` exits 0 too), so it is the pattern, not the reader. Extra blocks on `{a,git} tag v1`, `{git,tag}{,} v1` and `{git,x}' 'tag v1` are the gate failing closed on unquoted words, as the README states.
