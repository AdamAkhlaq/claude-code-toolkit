---
id: T6
title: The gate never fails open on a long or nested call
blocked_by: [T5]
files:
  [
    hooks/scripts/deploy_gate.py,
    hooks/hooks.json,
    tests/test_hooks.py,
    README.md,
    CHANGELOG.md,
    docs/changes/0003-fix-deploy-gate-bypass/intent.md,
  ]
proves: 'in tests/test_hooks.py, DeployGateTests.test_the_gate_never_fails_open_on_a_long_or_nested_call: with gatedCommands ["^git tag ", "^git push .*--force"], deploy_gate.py exits 2 on `env git push origin` followed by 70 refs and `--force`, exits 2 within 5 seconds on 40 `eval` words before `git tag v1`, exits 2 with a message saying the call is too long to read on a call of 200000 words, and exits 0 silently within 5 seconds on `env git add` followed by 5000 paths; and the `deploy_gate.py` entry in hooks/hooks.json has a timeout and `"onFailure": "block"`'
status: in-progress
executed_by: single
branch: ticket/0003-T6
---

## Context

From the second review of 0003 (`docs/changes/0003-fix-deploy-gate-bypass/review.md`, section "Review 2026-10-24 of a90e0c2"): Importants at `deploy_gate.py:49` (`WINDOW`) and `deploy_gate.py:54` (`eval` cost), the Decisions taken at that review, and the two `intent.md` wording Nits. Execution mode is `single`.

The decisions: the `WINDOW` goes, every line is matched whole, and the cost is bounded by a total budget, past which the call is blocked as unreadable; `eval` is re-read in linear time; `deploy-gate` gets an explicit timeout in `hooks/hooks.json` with `"onFailure": "block"`, as `red-guard` has, and the hook blocks on its own budget well before that timeout, so it never fails open.

Building a whole line from every program word is quadratic in the words of a simple command (5000 paths after `git add`: 361 MB). A linear way to keep every line whole: join each simple command once, with each program word's basename in place, record the offset where each program word starts, and for a pattern that starts with `^`, strip the `^` and use the compiled pattern's `match(line, offset)` at each offset, which anchors there; a pattern without a leading `^` is searched over the whole line and the raw command, as now. The budget is then a count of work, not time, so it is deterministic and testable: count the words read across all simple commands and every recursion into `eval`, `-c` scripts and substitutions, and block once it passes a limit well above any real call (200000 words is past it; 5000 paths after `git add` is not). For `eval`, re-read the words after the first `eval` in a simple command once and let that recursion handle any further `eval`, instead of recursing from every `eval` word.

The README's `deploy-gate` paragraph says a call too long to read is blocked. `intent.md`'s outcome says a quoted mention is not gated and an unquoted one is, on purpose, and its "this intent and its one ticket" becomes "its tickets".

Seam: the hook script as a subprocess, plus a test that reads `hooks/hooks.json`, as `RedGuardTests` pins `red-guard`'s entry. Write the proving test first and commit it failing before any code change.

## Acceptance

- The proving test passes.
- Every other test in `tests/` passes unchanged.
- The README's `deploy-gate` paragraph and `intent.md` say what the ticket's Context says.
- `CHANGELOG.md`'s `[Unreleased]` `deploy-gate` entry says it blocks a call too long to read and never fails open on a timeout.

## Evidence

### Evidence 2026-10-24 16:21

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
..............................................................................
----------------------------------------------------------------------
Ran 78 tests in 9.904s

OK
```

The proving test was committed failing before any code change. Run case by case against the hook at `c3bfdb2`: the padded force push behind `env` exited 0, 40 `eval` words were still running after 10 s, 200000 words exited 0 in 0.7 s, and `env git add` with 5000 paths exited 0 in 0.1 s, the one case that must stay as it was; `hooks/hooks.json` had no timeout for `deploy-gate`. After the fix: exit 2 in 0.0 s, exit 2 in 0.0 s, exit 2 in 0.4 s with "too long to read", and exit 0 in 0.2 s. `claude plugin validate .` passes.

Design as the ticket set it: one line per simple command, kept whole; a pattern anchored with `^` is matched with the `^` stripped at each program word's basename offset, so a path argument is never rewritten; `BUDGET` is 100000 words read, recursion included, and past it the call is `Unreadable` and blocked; the first `eval` or shell in a simple command is read into once. `hooks/hooks.json` gives `deploy-gate` `"timeout": 30` and `"onFailure": "block"`.

Live check, 2026-10-24: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^git tag ", "^git push .*--force"]`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                          | Result                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 40 `eval` words, then `git tag v1`               | blocked, but by `red-guard`, which timed out at its 600 s limit and blocked on `onFailure`: "PreToolUse:Bash hook error: [python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/red_guard.py\"]: timed out; blocking because onFailure is \"block\"". `deploy-gate` itself blocks this call in 0.0 s, as the probe above shows. |
| `env git push origin r0 ... r69 --force`         | blocked: "Blocked: 'env git push origin r0 r1 r2 ...' matches gated command pattern '^git push .*--force' in .claude/toolkit.json."                                                                                                                                                                                     |
| `touch` 300 files, then `env git add` of all 300 | ran, exit 0, 300 files staged                                                                                                                                                                                                                                                                                           |

`git for-each-ref refs/tags` in the repo afterwards listed nothing.

Found in the live check, outside this ticket's files: `_common.find_commit` recurses into the rest of the tokens from every `eval`, so a call with no commit in it costs twice as much per `eval` word (`is_git_commit` on 18 `eval` words before `git status`: 3.4 s). `red-guard`, `secret-guard` and `ticket-sync` all call it; `red-guard` blocks the call when its 600 s timeout runs out, the other two have no timeout and let it through, which is harmless as there is no commit to check. A call with a commit in it returns early and is fast, so it is not a bypass. Recorded for its own ticket.

### Verifier 2026-10-24 16:36

Verdict: reopen
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. Added on this branch (8c4f8f9), exercises the hook as a subprocess and reads `hooks/hooks.json`. Run against the hook and `hooks.json` from `change/0003-fix-deploy-gate-bypass` in a scratch copy, it fails at once: `AssertionError: 0 != 2` on the padded `env git push ... --force`.
3. proving test run: exit 0, `Ran 1 test in 0.637s OK` (`python3 -m unittest tests.test_hooks.DeployGateTests.test_the_gate_never_fails_open_on_a_long_or_nested_call`)
4. feedback command: exit 0, `Ran 78 tests in 9.224s OK` (`python3 -m unittest discover -s tests`)
5. acceptance: 4 of 4 checked, none failed on its wording. Proving test passes (check 3); every other test passes and the test diff only adds the new test; README and `intent.md` say what the Context says (read in the diff); the CHANGELOG `[Unreleased]` entry says a call too long to read is blocked and the hook has a timeout with `"onFailure": "block"`. The README's "each pattern is matched ... against a line from each word in it that could name a program" is no longer true for the pattern below.
6. scope: ok (CHANGELOG.md, README.md, intent.md, hooks/hooks.json, hooks/scripts/deploy_gate.py, tests/test_hooks.py, plus the ticket)
7. tests intact: ok (no deleted lines, no skip or expected-failure markers)

Regression found by probing the hook at this branch against the hook at `change/0003-fix-deploy-gate-bypass`: stripping one leading `^` and calling `match(line, offset)` leaves every other `^` in the pattern anchored to the start of the line, not the offset. With `gatedCommands: ["^git tag |^gh release "]`, `X=1 gh release create v1` and `sudo /usr/bin/gh release create v1` exit 0 on this branch and exit 2 on the integration branch. `^(git tag|gh release) ` and single-alternative patterns still block. A pattern that anchors with `\A` or puts `^` after an inline flag such as `(?i)` is not stripped at all, so it only ever matches at line start.

Also found, present before this branch too, so not a regression: `echo` followed by 2000 nested `$(` around `git tag v1` crashes the hook with `RecursionError`, exit 1, on both branches; whether `"onFailure": "block"` covers exit 1 as well as a timeout was not checked. A single 5 MB word followed by `&& git tag v1` runs past 60 s, because the budget counts words, not characters; the 30 s timeout with `"onFailure": "block"` turns that into a block, but the hook does not block on its own budget first, as the Context asks.

Reopen reason: a gated pattern with `^` on more than one alternative, such as `^git tag |^gh release `, now fails open behind an assignment, a wrapper or a path (`X=1 gh release create v1` exits 0, and exited 2 before this branch); anchor every `^` at the program word, or fall back to matching that pattern against a line that starts at the word, and add that case to the proving test.

### Evidence 2026-10-24 17:20 (retry)

Command: `python3 -m unittest discover -s tests`
Exit code: 0

```
..............................................................................
----------------------------------------------------------------------
Ran 78 tests in 12.448s

OK
```

The reopen's cases were added to the proving test and committed failing before the code changed (fda616c, 9e780b6, 919b934). Probed one at a time against the hook from 0bb6058, then after the fix:

| Case                                                       | Before                      | After                               |
| ---------------------------------------------------------- | --------------------------- | ----------------------------------- |
| `^npm publish\|^gh release ` on `X=1 gh release create v1` | exit 0                      | exit 2 in 0.0 s                     |
| `\Agh release ` on `sudo /usr/bin/gh release create v1`    | exit 0                      | exit 2                              |
| `echo` and 2000 nested `$(` around `git tag v1`            | exit 1, `RecursionError`    | exit 2 in 0.6 s, "too long to read" |
| one 5 MB word, then `&& git tag v1`                        | still running after 15 s    | exit 2 in 0.1 s, "too long to read" |
| 99000 words, then `&& git status`                          | exit 0 in 7.8 s (quadratic) | exit 0 in 0.3 s                     |

`(?i)^gh release ` and `^(?:npm publish|gh release )` already blocked and still do.

The fix: `without_anchors` takes out every `^` and `\A` outside a character class and not escaped, and the result is matched at each program word, so each alternative anchors there; taking an anchor out only widens where a pattern may start, so the gate errs toward blocking. Each call is charged its characters before it is parsed, against a budget of 1,000,000 alongside the 100,000 words, so a huge word or deep nesting stops before `shell_source`, `shlex` or the regexes run over it. A `RecursionError` is read as too long to read, and any other error while reading blocks with its type named, so the hook never exits 1, which would let the call through. The words after a program word are copied only for `git`, `eval` or a shell, which made a long simple command linear. README and CHANGELOG name the character budget, nesting and the anchoring of every alternative. `claude plugin validate .` passes, with the three warnings it gave before this branch (CLAUDE.md at the root, no icon, an untracked `.DS_Store`).

Adversarial shapes, all exit 2 within 1.3 s unless noted: 400000 nested `$(`, 990000 characters of `$(`, 200000 backticks, 500000 quote characters, 49000 words on one line, 450000 paths after `git add` (over the character budget, blocked as too long). 30000 lines of `cat <<E` before `git tag v1` exits 0, correctly, since the `git tag` is heredoc body text; `bash -c` repeated 30000 times before `'git tag v1'` exits 0 in 0.3 s, correctly, since `-c` gets the script `bash`.

Live check, 2026-10-24: a headless `claude --plugin-dir <this checkout> -p --permission-mode bypassPermissions` session in a throwaway repo with `"gatedCommands": ["^npm publish|^git tag ", "\\Agit push .*--force"]`, no `RELEASE_AUTHORIZED` and no marker, one Bash call per command.

| Command                                                               | Result                                                                                                                 |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `X=1 git tag v1`                                                      | blocked: "Blocked: 'X=1 git tag v1' matches gated command pattern '^npm publish\|^git tag ' in .claude/toolkit.json."  |
| `sudo -n true 2>/dev/null; env /usr/bin/git push origin main --force` | blocked: "... matches gated command pattern '\Agit push .*--force' in .claude/toolkit.json."                           |
| `echo` and 2000 nested `$(` around `git tag v3`                       | never reached the hook: the session's safety classifier stopped the tool call first. Covered by the proving test only. |
| `git status --short`                                                  | ran                                                                                                                    |

`git tag` in the repo afterwards listed nothing.

### Verifier 2026-10-24 16:52

Verdict: reopen
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. Added on this branch (8c4f8f9, extended in fda616c, 9e780b6, 919b934). It runs the hook as a subprocess and reads `hooks/hooks.json`. In scratch worktrees with this branch's `tests/test_hooks.py`, it fails against the hook from `change/0003-fix-deploy-gate-bypass` and against the hook from 0bb6058, both with `AssertionError: 0 != 2`.
3. proving test run: exit 0, `Ran 1 test in 1.610s OK` (`python3 -m unittest tests.test_hooks.DeployGateTests.test_the_gate_never_fails_open_on_a_long_or_nested_call`)
4. feedback command: exit 0, `Ran 78 tests in 10.883s OK` (`python3 -m unittest discover -s tests`)
5. acceptance: 4 of 4 checked, none failed on its wording. The proving test passes (check 3). Every other test passes, and the test diff only adds lines. The README and `intent.md` say what the Context says (read in the diff). The CHANGELOG `[Unreleased]` entry says a call too long to read is blocked and that the hook entry has a timeout with `"onFailure": "block"`.
6. scope: ok (CHANGELOG.md, README.md, intent.md, hooks/hooks.json, hooks/scripts/deploy_gate.py, tests/test_hooks.py, plus the ticket)
7. tests intact: ok (no deleted lines, no skip or expected-failure markers)

I probed this branch's hook and the hook from `change/0003-fix-deploy-gate-bypass` with `gatedCommands: ["^git tag "]` and found a regression. `readings` keeps a single `read_into` flag for both `eval` and shells, and it sets that flag on any word whose basename is a shell, even when `shell_script` returns None. An assignment whose value is a shell path uses up the flag, so the `eval` after it is never read. These cases exit 0 on this branch and 2 on the integration branch:

- `SHELL=/bin/bash eval 'git tag v1'`
- `PAGER=/bin/sh eval "git tag v1"`
- `SHELL=/bin/bash command eval 'git tag v1'`

bash runs the quoted script in each of these. `sudo -u sh eval '...'` and `env -u bash eval '...'` also exit 0, though there `eval` is not a binary, so nothing runs. Unquoted `SHELL=/bin/bash eval git tag v1` and `SHELL=/bin/zsh bash -c '...'` still block.

The rest of the probe found no other regressions. The cases checked include multi-alternative and `\A` anchors, `(?m)`, `[^...]`, wrappers, keywords, subshells, substitutions, quoted mentions, 5000 nested `eval` (0.5 s, exit 2; the integration hook crashed with exit 1 after 18.9 s), and large heredoc file writes, which were not falsely blocked. One limit, the same on both branches: a single word just under the character budget takes about 8.5 s here (250k characters 1.0 s, 500k 2.7 s, 999k 8.6 s), which grows faster than linearly. That is under the 30 s timeout, and the timeout blocks anyway, but on a slower machine it leaves less room than "well before that timeout".

Reopen reason: a shell-named word earlier in a simple command now hides a later quoted `eval` (`SHELL=/bin/bash eval 'git tag v1'` exits 0 on this branch and exited 2 before it). Set the read-into flag only when a script was actually read, or keep separate flags for `eval` and for shells, and add this case to the proving test.
