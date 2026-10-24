---
id: "0003"
slug: "fix-deploy-gate-bypass"
reviewed: d9f448e6a7201f73a8b5c346933d338a08d74f81
created: "2026-10-24"
---

# Review: a gated command is caught anywhere in the line

Three passes from `REVIEW.md` over `main...d9f448e`, each in its own context. Every Important finding below was re-run against the hook code at `d9f448e` before it was recorded. No spec or plan: this is a `fix-bug` change, so the passes checked the diff against `intent.md` and the ticket.

## Important

- [x] dfdfe5b hooks/scripts/_common.py:157 `HEREDOC` matches `<<` used as a shift inside arithmetic, and `<<EOF` inside a `#` comment, and `without_heredoc_bodies` then drops every later line when no closing delimiter appears. `echo $((1<<2))` followed by `git tag v1` gives no simple command for the tag, and `is_git_commit` on the same shape with `git commit -am x` is True on main and False here, so this branch opens a red-guard bypass main did not have. Fix: skip `<<` inside `$((`...`))` and `((`...`))`, drop comments before looking for heredocs, and keep the body when its closing delimiter is never found. (bugs, security)
- [x] dfdfe5b hooks/scripts/_common.py:148 shlex's default `#` commenter reads to the end of the line and swallows the newline, so `true # note` followed by `git tag v1` comes out as the one simple command `true git tag v1` and is let through, against the README and CHANGELOG claim that a `git tag` on the next line is caught. Fix: set `lexer.commenters = ""` and drop `#` comments in the quote-aware pre-scan, keeping the newline. (bugs, security)
- [x] dfdfe5b hooks/scripts/deploy_gate.py:38 shlex merges a separator with a following redirect into one token (`;>`, `&&>`, `\n>`), which the splitter reads only as a redirect, so `true;>out git tag v1` becomes `true git tag v1` and is let through. Fix: close the current simple command when a token holds any of `;|&\n` before treating it as a redirect. (bugs)
- [x] 447e2d3 hooks/scripts/deploy_gate.py:48 `expand` takes only the first word as the program, so a gated command behind an assignment, a wrapper or a reserved word gets through: `X=1 git tag v1`, `env git tag v1`, `command git tag v1`, `sudo git tag v1`, `time git tag v1`, `! git tag v1`, `{ git tag v1; }`, `if true; then git tag v1; fi`, `for x in 1; do git tag v1; done`, and `git -C . tag v1`. The intent's outcome is a block "wherever it sits in a Bash call". Fix: match each pattern from every word that could name a program, by basename, and also after git's global options. (bugs, security, compliance)
- [x] dfdfe5b 447e2d3 hooks/scripts/deploy_gate.py:33 Command substitution inside double quotes or backticks stays inside one word: `echo "$(git tag v1)"` and `` echo `git tag v1` `` run the tag and are let through. These are executions, not the mentions the intent exempts. Fix: recurse into each `$(`...`)` and backtick span inside a word, and make the backtick an operator. (bugs, security)
- [x] dfdfe5b hooks/scripts/_common.py:154 On a quoting error shlex rejects (`echo $'it\'s'; git tag v1`, which bash accepts) the tokeniser falls back to `command.split()`, which drops every control operator, so the whole call becomes one simple command. Fix: fall back to a split that keeps operators as tokens. (security)
- [x] waived, see Waivers. tests/test_hooks.py:164 The fix commit `d43dd67` adds test cases after the failing-test commit `c72ed2b` and after the lock was lifted: the quoted `<<EOF` and here-string cases in `DeployGateTests` and two cases in `RedGuardTests`, with the ticket's `proves` rewritten to match. `fix-bug`'s rule is that the regression test is committed before the fix. Fix: split the cases into their own `test(hooks):` commit, or waive with the reason recorded. (compliance)

## Nits

- hooks/scripts/deploy_gate.py:54 The `-c` search stops at the first long option or option argument, so `bash --norc -c 'git tag v1'` and `bash -o pipefail -c 'git tag v1'` are let through; `_common.find_commit` has the same gap. Fix: take the word after the first short flag containing `c` among the shell's arguments.
- tests/test_hooks.py:157 The proving test has no pipe or `eval` case, though `intent.md` promises the pipe and `CHANGELOG.md` claims both; both block today. Fix: add `git status | git tag v11` and `eval "git tag v12"` to the blocked cases.
- docs/changes/0003-fix-deploy-gate-bypass/intent.md:43 "Affected users and systems" names only `deploy_gate.py`, but the `shell_tokens` change also changes how `red-guard` reads commands. Fix: name `red-guard` and `hooks/scripts/_common.py` there.

0 Nits dropped.

## Out of pass

- A script piped or redirected into a shell (`echo 'git tag v1' | bash`, `bash <<< 'git tag v1'`, `bash script.sh`) is not caught, and no text match can catch every such route; nothing in the intent records where the gate's guarantee ends.
- The block message echoes up to 120 characters of the command, as before this change.
- `CHANGELOG.md:99` still compares `[Unreleased]` from `v0.4.0` and has no `[0.5.0]` link.
- No pull request exists yet, so its statement of merge danger could not be checked.

## Waivers

- tests/test_hooks.py:164, cases added after the lock in the fix commit `d43dd67`. Waived by Adam Akhlaq on 2026-10-24: "Waive, record why". The reason: each added case was shown failing before the code that makes it pass was written, quoted in the session (the quoted `<<EOF` case failed with `AssertionError: 0 != 2 : echo "a <<EOF"` before the quote-aware scan; the two red-guard cases failed against the stashed pre-fix tokeniser), and splitting the commit now would record an order that never happened. T2 follows the rule strictly.

## Decisions

Taken by Adam Akhlaq on 2026-10-24 at the review gate:

- Importants 1 to 6 and the first two Nits become ticket T2 in this change; 0003 does not ship until T2 is done.
- T2 matches each pattern from every unquoted word that could name a program, by basename, and after git's global options, rather than stripping a fixed list of wrappers. It fails closed: an unquoted `echo git tag v1` is blocked too.
- The README states where the gate's guarantee ends: a gated command written anywhere in a Bash call is caught, a script fed to an interpreter is not, and a hard guarantee needs a permissions deny rule or withheld credentials.

## Review 2026-10-24 of a90e0c2

Three passes from `REVIEW.md` over the delta `d9f448e...a90e0c2`, which holds T2 and T3, each in its own context. Every Important below was re-run against the hooks at `a90e0c2`, and each command was also run in bash with a stub `git` function to confirm the shell really runs the gated command.

### Important

- [ ] hooks/scripts/_common.py:198 `shell_source` starts a comment at a `#` after any space, including an escaped one (`echo a\ #b; git tag v1`) or one inside `${...}` (`echo ${x/ #/}; git tag v1`), and drops the rest of the line, so the gated command after it passes; `is_git_commit` misses the same forms, so `red-guard` does too. Fix: start a comment only after an unescaped word break outside `${...}`. (security)
- [ ] hooks/scripts/deploy_gate.py:42 `substitutions` reads `shell_source`, which has dropped every heredoc body, but the shell runs `$(...)` and backticks in the body of a heredoc whose delimiter is unquoted: `cat <<EOF` with `$(git tag v1)` in its body passes. Fix: have `shell_source` keep unquoted-delimiter bodies available to the substitution scan. (bugs, security)
- [ ] hooks/scripts/deploy_gate.py:116 `closing_paren` counts parentheses inside quotes and `case` patterns, so `echo "$(echo ")"; git tag v1)"` and `echo "$(case a in a) git tag v1;; esac)"` cut the substitution short and pass. Fix: skip quoted text and backslash pairs when counting, and stop only at a `)` outside quotes. (bugs, security)
- [ ] hooks/scripts/_common.py:202 Arithmetic is recognised only from `((`, so `<<` inside the older `$[...]` form is read as a heredoc and the lines after it are dropped: `echo $[1<<EOF]`, then `git tag v1`, then `EOF` passes. Fix: count `$[` to `]` as arithmetic too. (security)
- [ ] hooks/scripts/deploy_gate.py:49 A line from a later program word stops after `WINDOW` words, so padding defeats a pattern that needs a later word: `env git push origin r0 ... r69 --force` passes `^git push .*--force`. Fix: keep such lines whole and bound the cost another way, or state the limit where the guarantee is stated. (security)
- [ ] hooks/scripts/_common.py:296 `shell_script` takes the word straight after the `-c` cluster, but bash keeps reading options after it: `bash -c -- 'git tag v1'` and `bash -c -e 'git tag v1'` run the script and pass, and `is_git_commit("bash -c -- 'git commit -m x'")` is False. Fix: after the `c` cluster, skip further options, `--`, and the arguments of `-o` and `-O`. (bugs)
- [ ] hooks/scripts/_common.py:155 A backslash-newline becomes a word break, but bash deletes the pair, so `git ta\` with `g v1` on the next line runs `git tag v1` and is read as `git ta g v1`; `red-guard` misses `git com\` and `mit` the same way. Fix: replace the pair with nothing, outside single quotes. (bugs)
- [ ] hooks/scripts/deploy_gate.py:54 Each `eval` word re-reads every word after it, so the work doubles per `eval` (16 in a row: 0.8 s; the reviewer measured 20: 10.9 s). `hooks/hooks.json` sets no timeout for `deploy-gate`, and a hook that times out lets the call through, so about 22 `eval` words in front of a gated command get it past the gate. Raised from the bugs pass's Nit at merge for that reason. Fix: re-read only from the first word of a simple command, or window it like the other lines. (bugs)

### Nits

- hooks/scripts/\_common.py:137 `SHELLS` holds `sh bash zsh dash`, but macOS ships `ksh`, `csh` and `tcsh`, so `ksh -c 'git tag v1'` passes. Fix: add `ksh`, `mksh`, `csh`, `tcsh` and `fish`.
- hooks/scripts/\_common.py:162 The fallback after a quoting error keeps quote characters and splits inside quotes, so a quoted mention in a call that also fails to parse is gated, against the README's statement that quoted mentions are left alone. It fails closed. Fix: keep a quoted span as one token in the fallback.
- docs/changes/0003-fix-deploy-gate-bypass/intent.md:37 The outcome says a command that "only mentions it in an argument" is not gated, but an unquoted mention is, by decision. Fix: "in a quoted argument", with a clause that unquoted mentions are blocked on purpose.
- docs/changes/0003-fix-deploy-gate-bypass/intent.md:41 "this intent and its one ticket are the change" predates T2 and T3. Fix: "its tickets".
- docs/changes/0003-fix-deploy-gate-bypass/review.md:14 The first round's boxes were left open after T2 and T3 closed them. Ticked in this record with the fix commits.

1 Nit dropped (the first round's Decisions name T2 for work that T3 shipped).

### Out of pass

- `echo v1 | xargs git tag` passes `^git tag ` because the trailing space in the pattern expects an argument after `tag`; that is how patterns are written, and the README or the setup skill could warn about it.
- `bash <<< "git tag v1"` is a script fed to an interpreter, outside the stated guarantee, and no test pins it either way.
- `CLAUDE.md:35`, added in the first round, says to "match each simple command"; `deploy-gate` now matches from every program word.
- No pull request exists yet, so its statement of merge danger could not be checked; the gate guards a one-way door, so it should be stated.

### Decisions

Taken by Adam Akhlaq on 2026-10-24 at the review gate:

- All eight Importants become ticket T4 in this change, worked test-first. After T4, 0.5.1 ships; a later finding of a further exotic form is triaged against the stated limit of the gate rather than holding the release.
- The `WINDOW` goes: every line stays whole, and the cost is bounded by a total budget instead. A call whose lines would pass the budget is blocked as unreadable, so an absurd call fails closed rather than being cut short.
- `eval` is re-read in linear time, `deploy-gate` gets an explicit timeout in `hooks/hooks.json`, and the hook blocks on its own budget well before that timeout, so it never fails open.

### Waivers

<none yet>
