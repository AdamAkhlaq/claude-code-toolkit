---
id: "0003"
slug: "fix-deploy-gate-bypass"
reviewed: 19f6f8b646fd20d345bd99a1501c60f3201ab214
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

- [x] d73214a hooks/scripts/_common.py:198 `shell_source` starts a comment at a `#` after any space, including an escaped one (`echo a\ #b; git tag v1`) or one inside `${...}` (`echo ${x/ #/}; git tag v1`), and drops the rest of the line, so the gated command after it passes; `is_git_commit` misses the same forms, so `red-guard` does too. Fix: start a comment only after an unescaped word break outside `${...}`. (security)
- [x] e2b38ac hooks/scripts/deploy_gate.py:42 `substitutions` reads `shell_source`, which has dropped every heredoc body, but the shell runs `$(...)` and backticks in the body of a heredoc whose delimiter is unquoted: `cat <<EOF` with `$(git tag v1)` in its body passes. Fix: have `shell_source` keep unquoted-delimiter bodies available to the substitution scan. (bugs, security)
- [x] e2b38ac hooks/scripts/deploy_gate.py:116 `closing_paren` counts parentheses inside quotes and `case` patterns, so `echo "$(echo ")"; git tag v1)"` and `echo "$(case a in a) git tag v1;; esac)"` cut the substitution short and pass. Fix: skip quoted text and backslash pairs when counting, and stop only at a `)` outside quotes. (bugs, security)
- [x] d73214a hooks/scripts/_common.py:202 Arithmetic is recognised only from `((`, so `<<` inside the older `$[...]` form is read as a heredoc and the lines after it are dropped: `echo $[1<<EOF]`, then `git tag v1`, then `EOF` passes. Fix: count `$[` to `]` as arithmetic too. (security)
- [x] 0bb6058 hooks/scripts/deploy_gate.py:49 A line from a later program word stops after `WINDOW` words, so padding defeats a pattern that needs a later word: `env git push origin r0 ... r69 --force` passes `^git push .*--force`. Fix: keep such lines whole and bound the cost another way, or state the limit where the guarantee is stated. (security)
- [x] d73214a hooks/scripts/_common.py:296 `shell_script` takes the word straight after the `-c` cluster, but bash keeps reading options after it: `bash -c -- 'git tag v1'` and `bash -c -e 'git tag v1'` run the script and pass, and `is_git_commit("bash -c -- 'git commit -m x'")` is False. Fix: after the `c` cluster, skip further options, `--`, and the arguments of `-o` and `-O`. (bugs)
- [x] d73214a hooks/scripts/_common.py:155 A backslash-newline becomes a word break, but bash deletes the pair, so `git ta\` with `g v1` on the next line runs `git tag v1` and is read as `git ta g v1`; `red-guard` misses `git com\` and `mit` the same way. Fix: replace the pair with nothing, outside single quotes. (bugs)
- [x] 0bb6058 88c3079 hooks/scripts/deploy_gate.py:54 Each `eval` word re-reads every word after it, so the work doubles per `eval` (16 in a row: 0.8 s; the reviewer measured 20: 10.9 s). `hooks/hooks.json` sets no timeout for `deploy-gate`, and a hook that times out lets the call through, so about 22 `eval` words in front of a gated command get it past the gate. Raised from the bugs pass's Nit at merge for that reason. Fix: re-read only from the first word of a simple command, or window it like the other lines. (bugs)

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

## Review 2026-10-25 of cd72334

Three passes from `REVIEW.md` over the delta `a90e0c2...cd72334`, which holds T4, T5 and T6, each in its own context. Every Important below was re-run against the hooks at `cd72334`, and each bypass was also run in bash with a stub `git` to confirm the shell really runs the gated command. The second round's boxes above are ticked with the fix commits from T4 to T6.

### Important

- [x] d99a73e hooks/scripts/\_common.py:167 The fallback lexer added in T4 (`d73214a`) reads `'...'` in `QUOTED` as a plain single-quoted span, so the `\'` inside `$'a\'b'` ends it early and the quotes pair wrongly: `echo $'a\'b'; git tag v1; echo 'c'` passes `deploy-gate` (it blocked at `a90e0c2`), and the same shape with `git commit -am x` makes `is_git_commit` False, so `red-guard` misses it too. A regression this change introduced. Fix: put `\$'(?:\\.|[^'\\])*'` before `'[^']*'` in `QUOTED`, take `\\.` as a unit in `FALLBACK_TOKEN`'s unquoted branch, and add the case to the T4 test. (bugs)
- [x] d99a73e hooks/scripts/\_common.py:175 `HEREDOC` ends the delimiter at the first character outside `[\w.-]` or at a closing quote, but bash's delimiter is the whole word after quote removal: for `cat <<E'OF'` the hook takes `E` and bash takes `EOF`, so `cat <<E'OF'`, `EOF`, `git tag v1`, `E` drops a line bash runs, and `cat <<E:OF`, `E:OF`, `git tag v1`, `E` does the same. `red-guard` reads through the same function. Fix: read the delimiter as the whole word up to whitespace or an operator, compare it with its quotes removed, and mark it quoted if any quote or backslash appears in it. (security)
- [x] d99a73e hooks/scripts/deploy_gate.py:198 A backtick span ends at the next backtick even when it is escaped, so in ``echo `echo \`git tag v1\`` ``the gate reads `echo \` and bash runs the nested `git tag v1`. Fix: skip an escaped backtick when looking for the close, and re-read the inner text with`` \` `` turned into a backtick. (security)
- [x] d99a73e hooks/scripts/deploy_gate.py:224 `closing_paren` counts a `)` inside a `#` comment, so `x="$( : # )`, newline, `git tag v1`, newline, `)"` cuts the substitution short and passes; bash and zsh run the tag. Present at `a90e0c2` too, in the function T5 rewrote for this class. Fix: outside quotes, skip from a `#` at the start of a word to the next newline. (bugs)
- [x] b28848a hooks/scripts/deploy_gate.py:73 A program word and the word after it are taken literally, without ANSI-C quoting or brace expansion: `$'\x67it' tag v1`, `$'\147it' tag v1`, `{git,tag} v1` and `git {tag,v1}` pass, and bash runs `git tag` for each. These are what the Bash call says, which the README's guarantee covers. Fix: decode `$'...'` in the reader, and expand an unquoted `{a,b}` or fail closed on one in a program word or the word after it. (security)
- [x] 188427f README.md:76 The README's only stated limit is a script fed to an interpreter, but `t=tag; git $t v1` and `git${IFS}tag v1` pass and bash runs the tag: a variable defeats the gate and the guarantee as written is wider than the hook. Fix: name parameter expansion (`$var`, `${IFS}`) beside the interpreter case, or fail closed on an unquoted `$` in a program word or the word after `git`. (security)
- [x] amended, see Decisions. hooks/scripts/deploy_gate.py:79 Every `eval` word is now read into and charged the rest of its line, so a run of `eval` words costs more than its length and 120 of them before `git tag v1` are blocked as too long to read, against the Decision of 2026-10-24 that `eval` is re-read in linear time and T6's Context. The change was made in T6's second retry because reading only the first `eval` let `SHELL=/bin/bash eval '...'` through, and is recorded only in the ticket's Evidence. It fails closed. Fix: the maintainer amends the Decision to accept the budgeted reading, or waives. (compliance)

### Nits

- hooks/scripts/deploy_gate.py:119 The budget counts words and characters, not regex work: a pattern with no anchor after `without_anchors` is tried at every program word, so `x ` 99000 times then `&& git status` against `^.*--force` takes 7.0 s (0.2 s against `^git push .*--force`), and on a slower machine a harmless call could reach the 30 s timeout and be blocked. Fix: charge `len(starts)` per pattern to `BUDGET`, or say in the README that a pattern's own cost is not bounded.
- tests/test_hooks.py:228 The case of 40 `eval` words asserts only exit 2, which a "too long to read" block also gives, so it does not show a short chain is read. Fix: assert `release authorisation` in the message.
- docs/changes/0003-fix-deploy-gate-bypass/review.md:85 The second round's Decision sends all eight Importants to T4 and ships 0.5.1 after T4; the work became T4 to T6, as the intent's amendment records. Fix: point the Decision at the amendment, or read "T4 to T6 ... after T6".
- docs/changes/0003-fix-deploy-gate-bypass/review.md:55 The second round's boxes were open at `cd72334`. Ticked in this record with the fix commits.

0 Nits dropped.

### Out of pass

- Every reader bypass above applies to `red-guard`'s `find_commit` too, since both hooks read through `_common`; each fix wants a `RedGuardTests` case.
- T6's Evidence says `_common.find_commit`'s cost doubles per `eval` word and is "recorded for its own ticket", but no ticket or backlog entry exists under `docs/`.
- `CLAUDE.md:35` says a hook that cannot finish reading a command blocks it, but per T6's Evidence `secret-guard` and `ticket-sync` have no timeout and let a call through when they run out of time.
- No pull request exists yet, so its statement of merge danger could not be checked; the gate guards a one-way door, so it should be stated.
- `CHANGELOG.md:101` still compares `[Unreleased]` against `v0.4.0` and has no `[0.5.0]` link, as the first round noted.

### Decisions

Taken by Adam Akhlaq on 2026-10-25 at the review gate:

- The four reader bugs (`$'...'` in the fallback, heredoc delimiters, escaped backticks, a `)` in a comment) and the ANSI-C and brace forms become tickets in this change, worked test-first with a `RedGuardTests` case for each form `red-guard` shares. The reader decodes `$'...'` and expands an unquoted `{a,b}`, so a program word is read as bash sees it. At the tickets gate the work was cut as T7 (the four reader bugs) and T8 (`$'...'`, braces, and `red-guard` blocking a commit it cannot read). 0.5.1 waits for T8.
- Parameter expansion is a stated limit, beside the interpreter case: a variable's value is runtime state the call does not hold, and a hard guarantee stays a permissions deny rule.
- The Decision of 2026-10-24 that `eval` is re-read in linear time is amended: every `eval` and shell word is read, under the call's budget, and a chain past it is blocked as too long to read. Reading only the first was itself a bypass (`SHELL=/bin/bash eval '...'`), and the budget keeps the gate from failing open.

### Waivers

<none yet>

## Review 2026-10-25 of c96a43e

Three passes from `REVIEW.md` over the delta `cd72334...c96a43e`, which holds T7, T8 and the third round's doc commits, each in its own context. Every Important below was re-run against the hooks at `c96a43e` and at `cd72334`, and each bypass was run in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` that prints to stderr. The third round's boxes above are ticked with the T7 and T8 fix commits.

### Important

- [x] 5e192a2 hooks/scripts/\_common.py:450 `shell_source` reads any `$'` as the start of an ANSI-C quote, including the second `$` of `$$`, where bash reads a plain `'...'`: `echo $$'\' ; git tag v1 ; echo "'"` passes `deploy-gate`, and the commit form passes `red-guard`, while bash runs the tag. A regression from T7's rewrite of `$'...'`; `cd72334` blocked it. Fix: take `$$` as one unit before testing for `$'`. (bugs)
- [x] 5e192a2 hooks/scripts/\_common.py:179 `ANSI_C_NUMBER`'s `c(.)` takes the closing `'` of `$'\c'` as the control character, so the reader stays inside the quote that bash and zsh close: `echo $'\c'; git tag v1; echo 'x'` passes both hooks. A regression from T8. Fix: `c([^'])`. (security)
- [x] 5e192a2 hooks/scripts/\_common.py:358 `sequence` writes the characters a letter range covers straight back into source text that is parsed again, so `{W..a..5}` puts a bare `\` in front of the next quote and shifts every quote after it, while bash 3.2 and zsh leave that range as written: `echo {W..a..5}'x'; git tag v1; echo 'y'` passes both hooks. A regression from T8. Fix: expand only a letter range whose ends are both upper or both lower case, as the shells do, and quote what any range produces. (security)
- [x] 5e192a2 hooks/scripts/\_common.py:387 `heredoc_at` reads `<<$'EOF'` as delimiter `$EOF`, but bash and zsh close it at a line `EOF`, so `cat <<$'EOF'`, `EOF`, `git tag v1`, `$EOF` hides a line bash runs from both hooks. A regression from T7; `cd72334`'s regex did not match the form. Fix: drop a `$` right before a quote in the delimiter, as bash's quote removal does. (security)
- [x] 5e192a2 hooks/scripts/secret_guard.py:72 `is_git_commit` can now raise `Unreadable`, and `secret-guard` and `ticket-sync` (`ticket_sync.py:49`) call it unguarded, so a commit past the brace limit crashes them with exit 1, which Claude Code does not treat as a block: `git commit -m x; echo {a,b}...` with a staged AWS key was blocked at `cd72334` and commits unscanned at `c96a43e`. A regression from T8, against `CLAUDE.md`'s rule that a hook which cannot read a command blocks it; T8's Evidence deferred it with no ticket. Fix: catch a reader error in both hooks as `red_guard.main` does, silent without config, and block naming the hook. (bugs, security, compliance)
- [x] d5143d9 hooks/scripts/\_common.py:237 Every flat reader (`shell_source`, `expand_braces`, `unquoted_positions`, and shlex itself) keeps one quote state, so a quote inside a `$(...)` or backtick span nested in double quotes flips it: `echo "$(echo "it's")"; {git,tag} v1` keeps the braces unexpanded, and the wider family passes `deploy-gate` with no braces at all, already at `cd72334`: `x="$(printf "%s" "a'b")"; git tag v1; y="$(printf "%s" "c'd")"`, `echo "$(echo "'")"; git tag v1; echo "$(echo "'")"`, its backtick form, and `echo "$(echo "'")" ; echo ' #' ; git tag v1`, where the misread quote makes a `#` look like a comment. bash runs the tag in each. Fix: track a substitution nested in double quotes as a new quoting context in the readers, or hand its text to the substitution reader and keep only an empty `$()` in the outer source. (bugs, found widened by the family check)

### Nits

- hooks/scripts/red_guard.py:150 In a project with a `feedbackCommand`, an unreadable call that is not a commit, such as `echo {a,b}...` past the limit, is blocked as "Commit stopped", though no commit was asked for. Fix: start the message "Blocked: red-guard could not read this Bash call".
- README.md:71 The `red-guard` row says only that it blocks a commit while the feedback command is red; since T8 it also blocks a Bash call it cannot read where a `feedbackCommand` is set. Fix: add that to the row.
- docs/changes/0003-fix-deploy-gate-bypass/tickets/T7-reader-ends-spans-where-bash-does.md:68 T7 and T8 defer follow-ups "for its own ticket" (`red-guard` not reading a quoted `$(...)`, `secret-guard` and `ticket-sync` crashing on a read error), and no ticket or backlog line holds them, as the third round found for T6's `find_commit` note. Fix: give each a home under `docs/`.
- docs/changes/0003-fix-deploy-gate-bypass/review.md:99 The third round's five open boxes were not ticked after T7 and T8 closed them. Ticked in this record with the fix commits.

0 Nits dropped.

### Out of pass

- The brace budget is per `shell_tokens` call, not per hook call, so a word expanding to about 1,000,000 characters takes 2.3 s in `deploy-gate` against 0.4 s at `cd72334`: under the 30 s timeout, worth bounding per call if it grows.
- `closing_paren` reads a `<<` inside `$((...))` as a heredoc; it only reads more, never less, and no bypass came from it.
- T8's proving test covers no `$'\c'`, mixed-case range or `$`-quoted delimiter form; each fix wants its case in both hooks' tests.
- No pull request exists yet, so its statement of merge danger could not be checked.
- `CHANGELOG.md`'s `[Unreleased]` compare link still points at `v0.4.0`, as the first round noted.

### Decisions

Taken by Adam Akhlaq on 2026-10-25 at the review gate:

- The five regressions (`$$'`, `$'\c'`, letter ranges, `<<$'EOF'`, and `secret-guard` and `ticket-sync` crashing on a read error) become ticket T9, worked test-first and passed by a fresh verifier rather than fixed straight on the integration branch, since this round showed that reader fixes need an independent check.
- The nested-quote gap becomes ticket T10: a substitution nested in double quotes is read as its own quoting context, test-first with its whole family and `red-guard` cases.
- Two lines go into `CLAUDE.md`: a follow-up found while working a ticket or a review gets a home in the same change, and a reader change is probed at its own boundaries as well as along the families of what it fixes. `docs/backlog.md` is created as that home and holds every follow-up deferred so far in this change.

### Waivers

<none yet>

## Review 2026-10-30 of 74c8228

Three passes from `REVIEW.md` over the delta `c96a43e...74c8228`, which holds T9, T10 and the fourth round's doc commits, each in its own context. Every Important below was re-run against the hooks at `74c8228` and at `c96a43e`, in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` that prints to stderr. The fourth round's boxes above are ticked with the T9 and T10 fix commits. All three Importants are regressions from T10: before it, `closing_paren` only read the inside of a substitution, so a misread made `deploy-gate` read more; since T10 it decides where a double-quoted string ends for every reader, so the same misread hides the text after it.

### Important

- [x] 0594020 hooks/scripts/\_common.py:722 `closing_paren` takes the word `case` anywhere as the start of a `case` statement (`keyword_at` only checks the characters either side), so `case.txt`, `$case` or `echo case` inside `"$(...)"` makes it skip the real `)` and swallow the commands after it: `echo "$(cat case.txt)" && git commit -am x` passes `red-guard`, `secret-guard` and `ticket-sync`, and `git log --grep "$(echo case)"; git tag v1; echo "$(echo esac)"` passes `deploy-gate`. Both shells run the command; `c96a43e` blocked all of them. Fix: count `case` and `esac` only at command position, and add the forms to the T10 proving test for both hooks. (security)
- [x] 0594020 hooks/scripts/\_common.py:718 `closing_paren` reads a heredoc at any `<<` outside quotes, including inside a here-string `<<<` and a shift in `((...))` or `$((...))` after the start of the span, so it skips to a later line equal to the "delimiter": `echo "$(cat <<<EOF`, `)"; git tag v1; echo "x"`, `EOF` and `echo "$( ((1 <<EOF))`, `)" "a"; git tag v1 # "`, `EOF` pass `deploy-gate`, and the commit forms, with `echo "$( echo $((1 <<EOF)) x`, `)"; git commit -am x`, `EOF`, pass `red-guard`. Both shells run them; `c96a43e` blocked all of them. Fix: step over `<<<` as one unit and skip `((...))`, `$((...))` and `$[...]` with `arithmetic_close` before testing for a heredoc. (bugs)
- [x] 0594020 hooks/scripts/\_common.py:588 `double_quoted` and `parameter_close` (line 623) test for `$(`, `${` and a backtick one character at a time, so in `"$$(..."` or `"$${..."` the second `$` opens a substitution that zsh reads as the PID followed by a literal `(` or `{`, and the reader runs past the real closing quote: `echo "$$(" ; git tag v1 ; echo ")"`, `echo "$${x" ; git tag v1 ; echo "}"` and `echo "${x:-$$(}" ; git tag v1 ; echo ")"` pass `deploy-gate`, and their commit forms `red-guard`. zsh runs them, bash 3.2 rejects them; `c96a43e` blocked all of them, and T9 decided that the hooks fail closed where the shells disagree. Fix: take a run of `$` whole with `dollar_run` and raise `ShellsDiffer` when an even run comes before `(` or `{`. (bugs)

### Nits

- README.md:70 The `secret-guard` and `ticket-sync` rows (and their `CHANGELOG.md` line) say each blocks "a commit it cannot read", but both run on every Bash call and block any call they cannot read, as `echo {a,b}...` past the brace limit shows. Fix: say "a Bash call it cannot read", as the `red-guard` row does. (compliance)
- CHANGELOG.md:9 The entry says a `'...'` span in a double-quoted `${...}` is blocked when it holds `}` or `"`; the code also blocks a backtick, `$(`, `${` and `$[`. Fix: write "such as `}` or `"`". (compliance)
- docs/changes/0003-fix-deploy-gate-bypass/tickets/T10-substitution-in-double-quotes-is-its-own-context.md:60 A code span holding a backtick (``"${x:-'`'}"``) breaks every code span after it in the Evidence paragraph. Fix: write that span with double backticks. (compliance)
- docs/backlog.md:4 The fourth round's out-of-pass note that the brace budget is per `shell_tokens` call, not per hook call, has no line here, against the rule that every follow-up gets a home. Fix: add the line. (compliance)
- docs/changes/0003-fix-deploy-gate-bypass/review.md:142 The fourth round's six boxes were open after T9 and T10 closed them, as the fourth round found for the third. Ticked in this record with the fix commits. (compliance)

0 Nits dropped.

### Out of pass

- `closing_paren`'s cache is never cleared and is keyed on whole command strings: fine in a one-shot hook process, unbounded if `_common` is ever imported and reused.
- `double_quoted` reads `"$$$(...)"` as a substitution too; it only blocks more, and goes with the `$$` fix.
- A substitution in double quotes that runs to the end of the call hides the rest of it; raising `Unreadable` there would make any future overrun fail closed.
- `secret-guard` and `ticket-sync` still have no timeout or `"onFailure": "block"` in `hooks/hooks.json`; already in `docs/backlog.md`.
- No pull request exists yet, so its statement of merge danger could not be checked.

### Decisions

Taken by Adam Akhlaq on 2026-10-30 at the review gate:

- The three Importants become ticket T11, appended with `/toolkit:tickets 0003`, worked test-first and passed by a fresh verifier as T9 and T10 were; they stay open until T11 is done.
- The four open Nits are fixed in eb1a408, and the out-of-pass notes on an overrun failing closed and on `closing_paren`'s cache get lines in `docs/backlog.md`.
- `closing_paren` misreads were raised in the second, third and this round, so `CLAUDE.md` gets a line: a reader function whose answer starts to decide what other readers skip is probed again, branch by branch, as a bypass.

### Waivers

<none yet>

## Review 2026-10-30 of a7e72cc

Three passes from `REVIEW.md` over the delta `74c8228...a7e72cc`, which holds the fifth round's doc commits, the T11 ticket and T11, each in its own context. Every Important below was re-run against the hooks at `a7e72cc`, at `74c8228` and at `c96a43e`, in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` that prints to stderr. The fifth round's boxes above are ticked with T11's fix commit. All five Importants are in the `case` tracking T11 added to `closing_paren`: each is a `case` form it does not model, where a pattern's `)` then ends the substitution early and the text after it reads as quoted. Four are regressions from T11 (`74c8228` blocked every tag form); the fifth came in with T10.

### Important

- [x] f29ea99 hooks/scripts/\_common.py:815 Command position is bash's list of leaders, so a `case` that zsh runs at command position after `f()`, `function f {`, `repeat 1`, `coproc`, `for i (1)` or `foreach i (1)`, or after a backslash-newline (line 816 takes the `\` as a word), is not opened: `echo "$(f() case x in x) git tag v1;; esac; f)"`, `echo "$(repeat 1 case x in x) git tag v1;; esac)"` and `echo "$(echo;\`, `case x in x) git tag v1;; esac)"` pass `deploy-gate`, and `echo "$(f() case x in a) echo "'";; esac)"; git commit -am x; echo "'"` passes `red-guard`. zsh runs each; `74c8228` blocked them. Fix: in T12. (security, bugs)
- [x] f29ea99 hooks/scripts/\_common.py:861 In a pattern every `(` is skipped as the optional leading paren, but every `)` still ends the pattern, so a `$(...)` in a pattern, or a zsh glob group, moves the reader into the body early and the next `)` ends the span: `echo "$(case x in ($(echo a)) echo hi;; esac; git tag v1)"` passes `deploy-gate` and both shells run the tag, and `echo "$(case x in x(|y)) git tag v1;; esac)"` and `echo "$(case x in (x|(y))) git tag v1;; esac)"` pass while zsh runs the tag. `74c8228` blocked all of them. Fix: in T12. (bugs, security)
- [x] f29ea99 hooks/scripts/\_common.py:853 Only `;;` and `;&` return a body to its patterns, so after zsh's `;|` the next pattern's `)` ends the span: `echo "$(case x in x) echo a;| *) git tag v1;; esac)"` passes `deploy-gate` and zsh runs the tag; `74c8228` blocked it. Fix: in T12. (security)
- [x] f29ea99 hooks/scripts/\_common.py:850 The `<` or `>` of a process substitution `<(` or `>(` sets `target`, and the `(` does not clear it, so the first word inside is skipped as a redirect target and a `case` there is never opened: `echo "$(cat <(case x in a) echo hi;; esac) ; git tag v1 )"` passes `deploy-gate`; zsh runs the tag, bash 3.2 rejects the call, and T9 decided that the hooks fail closed where the shells disagree. `74c8228` blocked it. Fix: in T12. (bugs)
- [x] f29ea99 hooks/scripts/\_common.py:803 The `case x { ... }` form, which bash 3.2 and zsh both run, is read with `{` as the second head word, so the `}` never closes the `case` and the substitution's own `)` is taken as a pattern end: `echo "$(case x { x) echo a;; })"; git tag v1; echo ")"` passes `deploy-gate` and its `git commit` form passes `red-guard`, and both shells run the command. It came in with T10 (`74c8228` misses it too, `c96a43e` caught it). Fix: in T12. (security)

### Nits

- docs/changes/0003-fix-deploy-gate-bypass/review.md:184 The fifth round's three boxes were open after T11 closed them, the third round in a row this happened. Ticked in this record with `0594020`. (compliance)
- docs/changes/0003-fix-deploy-gate-bypass/tickets/T10-substitution-in-double-quotes-is-its-own-context.md:60 The code spans after the double-backtick one still run into the words around them (``EOF`got past because`closing_paren`read``). Fix: a space on each side of those spans. (compliance)
- README.md:76 The `deploy-gate` paragraph lists the "too long" and "bash and zsh read differently" blocks but not T11's block on a double-quoted substitution that never closes. Fix: add it beside the "read differently" sentence. (compliance)
- CHANGELOG.md:12 The entry for the commit hooks' unreadable-call block does not say that a double-quoted substitution that never closes is one, though `red-guard`, `secret-guard` and `ticket-sync` block it with that reason. Fix: add it to the examples. (compliance)

0 Nits dropped.

### Out of pass

- The frontmatter's `reviewed:` still names the first round's head, `d9f448e`; each later round names its head in its heading.
- In T11's live check `red-guard` blocked the `$$(` and never-closing calls before `deploy-gate` ran, so `deploy-gate`'s own two new messages were shown only in the unit tests.
- No pull request exists yet, so its statement of merge danger could not be checked.

### Decisions

Taken by Adam Akhlaq on 2026-10-30 at the review gate:

- The five Importants become ticket T12, appended with `/toolkit:tickets 0003`, worked test-first and passed by a fresh verifier as T9 to T11 were; they stay open until T12 is done. Its grilling weighs failing closed on a `case` form the reader does not model against modelling each form.
- The Nits are fixed in 71aff32, with the `red-guard` entry in `CHANGELOG.md`, which had the same gap and still said "a commit it cannot read".
- `closing_paren` misreads were raised in the second, third, fifth and this round, and this round's came from zsh's own grammar, which the family checks did not cover: `CLAUDE.md`'s family-check line now names bash and zsh and each shell's own grammar. Stale boxes were raised in the fourth, fifth and this round: `CLAUDE.md` gets a line that a ticket closing review findings ticks their boxes when it merges.

### Waivers

<none yet>

## Review 2026-10-31 of d0fb265

Three passes from `REVIEW.md` over the delta `a7e72cc...d0fb265`, which holds the sixth round's doc commits, the T12 ticket and T12, each in its own context. Every Important below was re-run against the hooks at `d0fb265` and at `a7e72cc`, in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git` that prints to stderr. The sixth round's boxes above were ticked with T12's fix commit in `d0fb265`. One Important is a regression from T12's backslash-newline reading, which joins text inside single quotes that both shells keep. The other three are in the `case` tracking: forms T12 meant to model, where the reader opens or closes a `case` that the shells do not, and the next `)` then ends the substitution early. `a7e72cc` misses those three too. The frontmatter's `reviewed:` now names this round's head.

### Important

- [x] 7bdd027 hooks/scripts/\_common.py:507 `shell_source` returns the reading of `joined(command)`, and `joined` deletes a backslash-newline inside `'...'` and `$'...'` as well, where bash and zsh keep it. Line 510 runs `joined` over the written reading too, so the comparison never sees the difference. The script handed to `eval`, `bash -c` or `zsh -c` therefore loses its backslash-newline before the inner reader sees its `#` comment or quoted heredoc. `bash -c 'echo a # x \`, newline, `git tag v1'`, the same with `$'...'`, and `eval 'cat <<"E"`, `x\`, `E`, `git tag v1`, `E'` pass `deploy-gate`, and both shells run the tag. `is_git_commit` turns False on the `git commit -am x` forms, so `red-guard`, `secret-guard` and `ticket-sync` miss them too. `a7e72cc` blocked all of them. Fix: in a ticket. Either join only outside single-quoted and ANSI-C spans, or return the written reading when the two agree. (security, bugs)
- [x] 7bdd027 hooks/scripts/\_common.py:869 In pattern position any whole word `esac` closes the `case`, including one after a pattern's `(` or `|`, where it is only a pattern word. `echo "$(case x in (x|esac) echo "'";; esac)"; git tag v1; echo "'"`, `echo "$(case x in (x|esac) git tag v1;; esac)"` and `echo "$(case esac in (esac) git tag v1;; esac)"` pass `deploy-gate`, and both shells run the tag. With `echo "$(case x in x|esac) git tag v1;; esac)"`, zsh runs it. `a7e72cc` misses these too. Fix: in a ticket. Close on `esac` only before a pattern has started. (security)
- [x] 7bdd027 hooks/scripts/\_common.py:921 After a heredoc operator and its delimiter, `command_start` stays True, so a `case` after it opens a `case`. `echo "$(<<EOF case x in a) "; git tag v1; echo " ;; esac)"` passes `deploy-gate`, and bash runs the tag because it reads `case` there as a command name. `a7e72cc` misses it too. Fix: in a ticket. End the command start at the delimiter, as the redirect-target branch at line 856 does. (bugs)
- [x] 7bdd027 hooks/scripts/\_common.py:926 Inside `[[ ... ]]`, `&&` and `||` set `command_start`, so a `case` operand opens a `case`. `echo "$([[ a || case == in ]] && echo a) "; git tag v1; echo " ;; esac)"` and its `&&` form pass `deploy-gate`, and both shells run the tag. `a7e72cc` misses them too. Fix: in a ticket. Track `[[` to `]]`, or raise `Unmodelled` on a `case` inside it. (bugs)

### Nits

- CHANGELOG.md:10 The `red-guard` entry, and the `secret-guard`/`ticket-sync` entry at line 12, list what makes a call unreadable but not T12's `Unmodelled` reasons, which `read_error` passes to all three commit hooks. In a project with a `feedbackCommand`, `red-guard` now blocks a call that does not commit, such as `echo "$(echo case)"`, and the CHANGELOG states that cost only for `deploy-gate`. Fix: add "a `case` form inside a substitution it does not read, or a backslash-newline that changes where a span ends" to both entries. (compliance)
- hooks/scripts/\_common.py:519 `comment_end` also runs on a top-level comment, so `echo a # trailing \`, newline, `ls` is blocked with a message saying "inside a substitution". Neither shell runs a tag there, and `a7e72cc` let it through. It also blocks any commit call carrying such a comment in the three commit hooks. Fix: raise only where the joined and written readings differ, or reword the message and record the over-block as an accepted cost. (bugs, security)
- hooks/scripts/deploy_gate.py:236 The `Unmodelled` message always says the gate "cannot tell where the substitution ends", though a backslash-newline in a quoted heredoc or at the end of a comment raises it with no substitution involved. Fix: "cannot tell where the call's text ends". (compliance)
- hooks/scripts/\_common.py:994 `parentheses_balance` skips a quote with a plain `find`, ignoring escapes and nested quotes, so `echo "$(echo ${x:-"\")"}; git tag v1)"` is blocked as read differently by bash and zsh, which read it the same way. It still blocks, so this opens no bypass. Fix: skip a double-quoted span with `double_quoted`. (bugs)
- hooks/scripts/\_common.py:953 After the `)` of `f()`, `command_start` is False, so the POSIX function form `echo "$(f() { case x in a) echo hi;; esac; }; f)"` is blocked, a cost not listed in T12. Fix: treat `{` after `name()` as a command leader, or list the cost. (bugs)

3 Nits dropped: the `deploy_gate.py` docstring and the `Unmodelled` docstring lag the backslash-newline block, and T12's Context line 26 still says a `case` head word raises.

### Out of pass

- T12's `proves` was not extended with the backslash-newline forms added after its reopen; the test holds them.
- No pull request exists yet, so its statement of merge danger could not be checked.

### Decisions

Taken by Adam Akhlaq on 2026-10-31 at the review gate:

- The four Importants become ticket T13, appended with `/toolkit:tickets 0003`, worked test-first and passed by a fresh verifier as T9 to T12 were; they stay open until T13 is done. Its grilling weighs blocking every `case` inside a double-quoted substitution, which ends the class, against modelling more forms.
- The five Nits fold into T13, since four of them are in the code its fix touches.
- A reader step matching or rewriting text where the shell does not was raised in the fourth (`$'` inside `$$'`), fifth (`<<` inside a here-string or arithmetic, `case` anywhere) and this round: `CLAUDE.md` gets a line that each such step is probed in every quoting and grammar context before it is handed on.

### Waivers

<none yet>

## Review 2026-10-31 of 28f3cbb

Three passes from `REVIEW.md` over the delta `d0fb265...28f3cbb`, which holds the seventh round's doc commits, the T13 ticket and T13, each in its own context. Every bypass below was re-run against the hooks at `28f3cbb` and at `d0fb265`, in `/bin/bash` 3.2 and `/bin/zsh` with a stub `git`. Two are regressions from T13's backslash-newline reading inside backticks, where an escaped pair `\\` before a newline is taken for a continuation. Three were already open at `d0fb265`: a `#` comment inside backticks that swallows the closing backtick, a `case` straight after `{`, which zsh reads as a keyword, and `##a` inside arithmetic, read as a comment. The sixth finding is a T13 acceptance line left unmet. The frontmatter's `reviewed:` now names this round's head.

### Important

- [x] 8a01bec hooks/scripts/\_common.py:599 Inside a backtick span, the branch deletes a backslash-newline in single quotes even when its backslash is the second of an escaped pair `\\`. That pair is no continuation in either shell: the backtick unescape turns it into `\` and a newline inside single quotes, which both shells keep. ``echo `bash -c 'echo a # x \\``, newline, `` git tag v1'` `` reaches the inner reader as `echo a # x \git tag v1` and passes `deploy-gate`, and both shells run the tag; `x=` and `eval` forms do the same, and `is_git_commit` turns False on the `git commit -am x` form, so `red-guard`, `secret-guard` and `ticket-sync` miss it too. `d0fb265` blocked all of them. Fix: inside a backtick in quotes, read backslashes in pairs as the escape branch does outside quotes, and drop only a lone `\` before the newline. (bugs)
- [x] 8a01bec hooks/scripts/\_common.py:855 `substitution_end` joins a double-quoted backtick span's script after unescaping it, so the `\\` and newline the unescape turns into `\` and newline is then deleted inside single quotes. ``echo "`bash -c 'echo a # x \\``, newline, ``git tag v1'`"`` gives the span `bash -c 'echo a # x git tag v1'` and passes `deploy-gate`, and both shells run the tag. `d0fb265` blocked it. Fix: join the raw text first, then unescape. (bugs)
- [x] 8a01bec hooks/scripts/\_common.py:630 Inside a backtick span, a `#` comment runs on to the newline and swallows the closing backtick, so `backtick` stays True and line 599 then deletes the backslash-newline inside a later single-quoted `bash -c` or `eval` script. Both readings make the same mistake, so the agreement check at line 517 does not see it. `` x=`: # ` ``, newline, `bash -c 'echo a # x \`, newline, `git tag v1'`, its `eval` form and `` `# ` `` at the start pass `deploy-gate`, and both shells run the tag; `is_git_commit` is False on the `git commit` form. `d0fb265` misses these too. Fix: end a comment inside a backtick span at the first unescaped backtick before the newline, where both shells close the span, or raise `Unmodelled` on a `#` comment inside one. (security)
- [x] 8a01bec hooks/scripts/\_common.py:901 The `case` check fires only when the character before `case` is a metacharacter, but zsh also reads `case` as a keyword straight after `{`. `echo "$({case x in x) echo ")"; git tag v1; echo "(" ;; esac})"` and the same inside `if true; then ...; fi` pass `deploy-gate`, and zsh runs the tag. The docstring at line 876 says any whole-word `case` in the span raises. `d0fb265` misses these too. Fix: count `{` and `}` as a word start before `case`, and probe zsh's other reserved-word positions again. (security)
- [x] 8a01bec hooks/scripts/\_common.py:630 The `#` comment branch is still taken inside `((...))`, `$((...))` and `$[...]`, where `##a` is a character code. `(( y = ##a )); git tag v1` and `for (( i = ##a; i < 0; i++ )); do :; done; git tag v1` drop the rest of the line and pass `deploy-gate`, and both shells run the tag; with `echo $(( ##a )); git tag v1` and `echo $[ ##a ]; git tag v1`, zsh runs it. `d0fb265` and `main` miss these too. Fix: do not open a comment inside arithmetic or `$[...]`. (bugs)
- [x] 8a01bec hooks/scripts/deploy_gate.py:8 The module docstring names the `case` and the backslash-newline reasons but not `COMMENT_IN_SUBSTITUTION` (`_common.py:527`, raised at `:634` and `:931`), a third reason `Unmodelled` carries. T13's Context and Acceptance require it to name every reason; the verifier's note was moved to `docs/backlog.md:8` instead. Fix: add "or a `#` comment ending in a backslash inside a substitution" to the list and delete the backlog line. (compliance)

### Nits

- CHANGELOG.md:9 The opening sentence still says the gate catches a gated command in a `$(...)` that holds "a `case`", though any `case` there now blocks, contradicting a later sentence in the same entry; and it calls `"$(f() { case ...; })"` zsh's, though `f() { ...; }` is the POSIX form bash runs too. Fix: drop "or a `case`" and "zsh's". (compliance)
- hooks/scripts/\_common.py:666 Inside a backtick span, a quoted heredoc body holding a backslash-newline raises `ShellsDiffer`, and a comment ending in a backslash raises `COMMENT_IN_SUBSTITUTION` (line 633); both messages say bash and zsh differ, but both shells join everything inside backticks, as T13's Evidence says. The over-block is not listed as a cost in the CHANGELOG or README. Fix: a reason for the backtick branch that does not claim the shells differ, and the cost named in the CHANGELOG. (compliance, bugs)
- README.md:76 It says a backslash-newline is kept "inside single quotes or `$'...'`", but inside a backtick span both shells, and the reader, delete it there too. Fix: add "outside backticks". (compliance)
- README.md:76 It says a `case` "anywhere inside a substitution" blocks, but `cat <(case x in x) echo hi;; esac)` at the top level is read, not blocked. No bypass: the text stays in the reading. Fix: scope the sentence, or raise on a `case` in a top-level `<(`/`>(` too. (bugs)
- hooks/scripts/\_common.py:1022 The `skip_heredoc_bodies` docstring's last sentence is broken: "in a body that does not to `literal`". Fix: "in a body that does not expand is appended to `literal`". (bugs)

1 Nit dropped: `tests/test_hooks.py:511` repeats a case already asserted at `:439`. Two compliance Nits on `CHANGELOG.md:9` are merged into one above.

### Out of pass

- Pre-existing over-block, also at `d0fb265`: `echo a \`, newline, `# c`, newline, `ls` raises `Unmodelled`, because the written reading does not start a word after a dropped backslash-newline (`_common.py:599-603`).
- T13's `proves` names fewer forms than its test holds (the `"$(bash -c ...)"` and backtick ones).
- No pull request exists yet, so its statement of merge danger could not be checked.

### Decisions

Taken by Adam Akhlaq on 2026-10-31 at the review gate:

- The six Importants become ticket T14, appended with `/toolkit:tickets 0003`, worked test-first and passed by a fresh verifier as T9 to T13 were; they stay open until T14 is done. The `deploy_gate.py` docstring line rides along, since T14 edits the same list of reasons.
- The five Nits fold into T14, since three are in code its fix touches and the rest are one-line wording fixes in files it updates.
- Backtick spans and an escaped `\\` were missing from the contexts the seventh round's `CLAUDE.md` line lists, and three of this round's five bypasses sit there: the line is extended in place to name backticks, an escaped `\\` and the position straight after `{`.

### Waivers

<none yet>

## Review 2026-11-01 of a6f928f

Three passes from `REVIEW.md` over the delta `28f3cbb...a6f928f`, which holds the eighth round's doc commits, the T14 ticket and T14, each in its own context. Every bypass below was re-run against the hooks at `a6f928f` and at `28f3cbb`, in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git`. One is a regression from T14: the backtick branch puts a span's own reading back into the outer text, and a reading that ends inside an open quote pairs with a later quote. The rest were already open at `28f3cbb`, four of them in the families T14 worked on: a quote inside zsh arithmetic, a `)` inside `${...}` or `$'...'` that `arithmetic_at` counts, and zsh's glob group `x(N)` before a `#`. The fifth is zsh's `=git`. The sixth is a T14 acceptance line left unmet. The frontmatter's `reviewed:` now names this round's head.

### Important

- [x] 71bd6e2 hooks/scripts/\_common.py:765 The backtick branch writes the span's own reading back into the outer text, and that reading can end inside an open quote, which `shell_tokens` then pairs with a quote later in the call, so the text between becomes one quoted word. `` echo `: "`; git tag v1; echo "x" ``, its `x=`, leading-span and newline forms, and `` echo `echo "a`; git tag v1; echo `echo b"` `` pass `deploy-gate`, and bash runs the tag; `28f3cbb` blocked all of them as `Unclosed`. The `'` forms (`` echo `: '`; git tag v1; echo 'x' ``, and the nested `` echo `echo \`echo 'a\``; git tag v1; echo `echo b'` ``, which zsh runs too) were already open at `28f3cbb`. `is_git_commit` is False on every commit form. Fix: raise `Unclosed` when a backtick span's script, or its reading, ends inside a quote; the reading must stay in the text, since the commit hooks read it from the tokens. (bugs, security)
- [x] 71bd6e2 hooks/scripts/\_common.py:1069 Inside arithmetic, `arithmetic_at` and `source_text` (line 687) read `'` and `"` as quotes, but zsh reads them as characters there, as in the character code `##'`. The scan finds no close, so the `((` is taken for two subshells and the `#` after it for a comment that hides the line. `(( y = ##' )); git tag v1 # '`, `(( 1 ' )); git tag v1 # '`, `(( y = ##" )); git tag v1 # "`, `echo $(( ##' )); git tag v1 # '`, `echo $[ ##' ]; git tag v1 # '` and the `for ((` form pass `deploy-gate`, and zsh runs the tag. `28f3cbb` misses them too. Fix: a `'` or `"` inside `((...))`, `$((...))` or `$[...]` raises ShellsDiffer, since bash reads a quote there and zsh a character. (security)
- [x] 71bd6e2 hooks/scripts/\_common.py:1055 `arithmetic_at` counts a `)` inside `${...}` or `$'...'`, so it takes `((` for two subshells and `##a` for a comment, and the eighth review's `##a` finding stays open for these forms. `(( ${x/)/} + ##a )); git tag v1` and `(( ${x:-)} + ##a )); git tag v1` pass `deploy-gate`, and zsh runs the tag; `(( $'\')' + ##a )); git tag v1` passes, and bash runs it. `28f3cbb` misses them too. Fix: step over `${...}` with `parameter_close` and `$'...'` with `ansi_c_span` in `arithmetic_at` (and `arithmetic_close`), as `source_text` does. (bugs)
- [x] 71bd6e2 hooks/scripts/\_common.py:727 After any `(` of kind `""`, including one in the middle of a word, which zsh reads as a glob group, a `)` starts a word, so a `#` straight after it is read as a comment. `setopt nonomatch; echo x(N)#y; git tag v1` passes `deploy-gate`, and zsh runs the tag; bash rejects `x(` as a syntax error. `28f3cbb` misses it too. Fix: give a `(` after a non-metacharacter the `ARRAY` kind, so a `#` after its `)` raises ShellsDiffer. (bugs)
- [x] 71bd6e2 hooks/scripts/deploy_gate.py:76 zsh's `EQUALS` expansion turns `=git` into the path of `git`, so `=git tag v1` and `{=git tag v1}` pass `deploy-gate`, and zsh runs the tag; the basename check does not know `=git`. `28f3cbb` and `main` miss it too. Fix: read a word starting with `=` also as the word without it, wherever a program name is tested, in `deploy-gate` and `find_commit`. (bugs, out of pass)
- [x] 71bd6e2 hooks/scripts/deploy_gate.py:10 The module docstring names the three `Unmodelled` reasons but the `ShellsDiffer` ones only through "one bash and zsh read differently", leaving `LITERAL_BODY_IN_SUBSTITUTION` and T14's `HASH_AFTER_ARRAY` unnamed, though T14's Acceptance says it names every reason both carry. The `docs/backlog.md` line T14 deleted tracked the first of them. Fix: name each `ShellsDiffer` reason in the list. (compliance)

### Nits

- README.md:76 The README says a `case`, a `#` comment ending in a backslash, and a quoted heredoc body holding a backslash-newline block the call "inside a substitution", and `CHANGELOG.md:9` and the `deploy_gate.py` docstring say the same, but inside a backtick span none of them blocks now: `` echo `case x in x) echo hi;; esac` `` exits 0. No bypass, since the span ends at its backtick either way. Fix: say "a `$(...)`, `<(...)` or `>(...)` span" in all three places. (compliance)
- README.md:76 "A word in quotes names no program" no longer holds for a quoted brace: `brace_group_words` splits after quote removal, so `echo "{git" tag v1` is blocked. `CHANGELOG.md:9` does not list the cost either. Fix: name the quoted-brace over-block beside the brace-group sentence in both. (compliance)
- CHANGELOG.md:9 The entry does not record the two blocks T14 lifts: a `#` comment ending in a backslash, and a quoted heredoc body holding a backslash-newline, inside a backtick span. Fix: one clause saying both are now read. (compliance)
- docs/changes/0003-fix-deploy-gate-bypass/intent.md:77 The fourteenth-ticket amendment does not mention the new blocks T14 added: a `case` inside an unquoted substitution in every hook, and a `#` straight after an array's `)`. Fix: one clause. (compliance)

0 Nits dropped.

### Out of pass

- `brace_group_words` changes the tokens of a brace-wrapped argument such as `-m {fix}` for every commit hook. Checked: `red-guard`'s `only_bookkeeping` then reads `{` as a program and runs the full check, `secret-guard` and `ticket-sync` read only `is_git_commit` and `commits_all_tracked`, which splits on whitespace, so it opens nothing.
- No test covers a quote inside arithmetic or an unclosed quote inside a backtick span.
- No pull request exists yet, so its statement of merge danger could not be checked.

### Decisions

- The six Importants go to a new ticket, T15, appended with `/toolkit:tickets`; each finding stays open until T15 is done. (maintainer, "New ticket T15")
- The four Nits are folded into T15, which touches the same README and CHANGELOG paragraphs. (maintainer, "Fold into T15")
- Three findings come from a scan deciding where a span ends without stepping over what the shells step over there, the same kind raised in earlier rounds of this review (the `parentheses_balance` quote finding, `closing_paren`'s heredoc finding). `CLAUDE.md` gains a line: a scan that decides where a span ends steps over exactly the constructs each shell steps over there, probed with each one holding the closing character, in bash and zsh. (maintainer, "Add the line")

### Waivers

<none yet>

## Review 2026-11-01 of 19f6f8b

Three passes from `REVIEW.md` over the delta `a6f928f...19f6f8b`, which holds the ninth round's doc commits, the T15 ticket and T15, each in its own context. Every bypass below was re-run against the hooks at `19f6f8b` and at `a6f928f`, in `/bin/bash` 3.2 and `/bin/zsh` 5.9 with a stub `git`. One is a regression from T15: the `((` arithmetic branch now needs a word start, so a `((` glued to a reserved word or to zsh's `{` is no longer read as arithmetic, and a `<<` inside it is read as a heredoc that hides the lines after it. Two more were already open at `a6f928f`, in the families T15 worked on: a `]` inside a `$(...)` nested in `$[...]`, and a `(` at the start of an argument word, which zsh reads as a glob group. The fourth is a T15 acceptance line left unmet. The frontmatter's `reviewed:` now names this round's head.

### Important

- [x] 6351cf1 hooks/scripts/\_common.py:715 The `((` branch runs only when `starts_word` holds, so a `((` straight after a reserved word, as in `if((`, `while((`, `until((`, `for((` and `!((`, or after zsh's word-starting `{`, falls through to the glob-group kind. A `<<` inside it is then read as a heredoc, and a quote inside it pairs with a later one. `if((x=1<<E));then :;fi`, newline, `git tag v1`, newline, `E`, and its `while((`, `for((` and `!((` forms pass `deploy-gate`, and bash runs the tag; `a6f928f` blocked all four. `{((x=1<<E))}` in the same shape passes, and zsh runs it, also blocked at `a6f928f`. `{(( 1 ' )); git tag v1; } # '`, its `"`, `{{((`, `{(( 1 ' ))};`, `repeat 1 {((` and `f(){((` forms pass, and zsh runs the tag; those were open at `a6f928f` too. `is_git_commit` is False on every commit form. Fix: take a `((` as a candidate for arithmetic wherever bash or zsh can open one, after a word start, a reserved word or a run of `{`, and test the forms in both shells. (bugs, security)
- [x] 6351cf1 hooks/scripts/\_common.py:748 `brackets` is a bare counter, so a `]` inside a `$(...)` nested in `$[...]` closes the `$[`, and the `#` of `##a` after it is read as a comment. `echo $[ $(: ]; echo 1) + ##a ]; git tag v1` passes `deploy-gate`, and zsh runs the tag; `a6f928f` misses it too. `arithmetic_end(command, index + 1, "[]")` at line 743 finds the right `]` and drops it. Fix: push `$[` onto `parens` as arithmetic, so only its own `]` pops it, or keep the index `arithmetic_end` returns. (bugs)
- [x] 6351cf1 hooks/scripts/\_common.py:728 A `(` that starts an argument word, or a word inside `[[ ]]`, is a glob group to zsh, but it gets kind `""`, so its `)` starts a word and a `#` after it, or after `|` inside it, is read as a comment. `[[ a == (a)#y ]]; git tag v1` and `[[ a == (a|#b) ]]; git tag v1` (no option needed), `setopt nonomatch; echo (a|#b); git tag v1`, `echo ((a)|b)#y; ...`, `print -r -- (N)#y; ...` and `setopt extendedglob nonomatch; echo (#i)x; ...` pass `deploy-gate`, and zsh runs the tag; `a6f928f` misses them too. `is_git_commit` is False on the commit forms. Fix: give a word-start `(` outside command position, after a word of the same simple command or inside `[[ ]]`, the glob kind, so a `#` inside it or straight after its `)` raises ShellsDiffer. (security)
- [x] 6351cf1 hooks/scripts/deploy_gate.py:11 The docstring's "a `'...'` span or an unbalanced bracket after `$$` inside double quotes" ties the `'...'` reason to `$$`, but `_common.py:952` raises it for a `'...'` span inside a double-quoted `${...}`: `echo "${x:-'}'}"` blocks with no `$$`, and `echo "$$'a}'"` passes. T15's Acceptance asked the docstring to name every reason. Fix: "a `'...'` span inside a double-quoted `${...}` holding a character that changes where it ends, an unbalanced bracket after `$$` inside double quotes", as `CHANGELOG.md:9` puts it. (compliance)

### Nits

- hooks/scripts/\_common.py:672 Since `brackets` ignores nesting, the new quote check fires on a quote inside a `$(...)` nested in `$[...]`: `echo $[ $(echo "1") + 1 ]`, which both shells accept, is blocked by every hook, an over-block the tickets gate did not accept. Fix: the stack fix for line 748, so the check sees the nested `$(...)`. (bugs)
- hooks/scripts/red_guard.py:78 `only_bookkeeping` still uses `os.path.basename`, so `=git status` is not bookkeeping and red-guard runs the full check. Safe, but it contradicts the claim that `program_name` is used wherever a program name is tested. Fix: `program_name(words[0])`. (bugs, compliance)
- hooks/scripts/\_common.py:984 The `CASE_IN_SUBSTITUTION` message says "inside a substitution", while the README and CHANGELOG now say "a `$(...)`, `<(...)` or `>(...)` span". Accurate, worded apart. Fix: say the same in the message. (compliance)

0 Nits dropped.

### Out of pass

- No test covers a `((` straight after a reserved word or `{`, which is how the regression passed 89 green tests.
- `=git${x} tag v1` passes, and zsh runs it. It falls under the documented limit on a word built from a variable, as `git${x}` does.
- No pull request exists yet, so its statement of merge danger could not be checked.

### Decisions

- The four Importants go to a new ticket, T16, appended with `/toolkit:tickets`; each finding stays open until T16 is done. (maintainer, "New ticket T16")
- The three Nits are folded into T16, which works the same code paths. (maintainer, "Fold into T16")
- The regression came from tightening a match without probing it glued to a reserved word or in argument position, a position slip of the kind earlier rounds found after `{`. `CLAUDE.md`'s reader-step line now also names straight after a reserved word with no space between (`if((`, `!((`) and both command and argument position. (maintainer, "Extend the line")

### Waivers

<none yet>
