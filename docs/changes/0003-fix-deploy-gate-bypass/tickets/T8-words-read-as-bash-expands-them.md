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
proves: 'in tests/test_hooks.py, DeployGateTests.test_a_word_is_read_as_bash_expands_it: with gatedCommands ["^git tag "], deploy_gate.py exits 2 on `$''\x67it'' tag v1`, `$''\147it'' tag v2`, `{git,tag} v3`, `git {tag,v4}`, `gi{t,} tag v5` and `{f..h}it tag v6`, exits 2 with a message saying the call is too long to read on a word whose braces expand to more than 10000 words, and exits 0 silently on `echo ''{git,tag} v1''` and `{ echo git; }`; and in RedGuardTests, red_guard.py blocks with the feedback output on `$''\x67it'' commit -am x` and `git {commit,-am,x}`, and blocks with a message naming red-guard, not a traceback, on a commit whose braces expand to more than 10000 words'
status: in-progress
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
