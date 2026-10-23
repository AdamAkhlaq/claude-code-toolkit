---
id: "0002"
slug: "block-red-commits"
reviewed: 82106a2b54bc059bff59b6d7f9412ed8e1a6b4c7
created: 2026-10-23
---

# Review: no commit lands while the feedback command is red

Range `main...82106a2`, three passes from `REVIEW.md` (bugs and logic, security, compliance with the spec and plan), each run by a `toolkit:reviewer` in its own context. No pull request exists yet, so nothing was posted; the findings live here until one is opened.

## Important

- [x] bb6907e hooks/scripts/red_guard.py:121 `guard` loads `.claude/toolkit.json` from whatever checkout `commit_checkout` resolves (event `cwd`, a leading `cd <dir> &&`, `git -C <dir>`) and runs its `feedbackCommand` with `shell=True`, so a `git commit` in any repository Claude has moved into, such as a cloned third-party repo, runs that repository's command. Before this change hooks read config only from `CLAUDE_PROJECT_DIR`, and this PreToolUse hook runs before the permission prompt, so the foreign command runs even if the user would have denied the commit. Fix: continue only when the resolved checkout's `git rev-parse --git-common-dir` matches the project's, so the main checkout and its worktrees count; otherwise exit 0.
- [x] bb6907e hooks/scripts/_common.py:127 `is_git_commit` splits on whitespace and compares each token to the literal `git`, so reworded commits are not recognised and land on red: `git add -A;git commit -m x`, `cd a&&git commit -m x`, `(git commit -m x)`, `/usr/bin/git commit -m x`, `bash -c "git commit -m x"` all return False. The spec's outcome is that red-guard stops any `git commit` Claude attempts, and a blocked agent can get past it by rewording. Fix: tokenise with `shlex.shlex(command, posix=True, punctuation_chars=True)` so `;`, `&&` and `(` split off, match `os.path.basename(token) == "git"`, and use the same tokeniser in `commit_checkout` (`_common.py:151`); scan the argument of `sh|bash|zsh -c` too, or record it as a known gap.
- [x] bb6907e hooks/scripts/red_guard.py:128 With empty `testGlobs`, red-guard treats no file as a test (`config.get("testGlobs") or []`), while `lock_tests.py:36` falls back to `DEFAULT_TEST_GLOBS` and `skills/setup/SKILL.md:29` tells users to leave the key empty to get those defaults. Reproduced: empty `testGlobs`, only `tests/test_bug.py` untracked, a red feedback command, and the hook exits 2, so fix-bug step 7's failing-test commit is blocked in a project set up as recommended. Diverges from spec requirement 5 ("the same glob rules as the other hooks"). Fix: move `DEFAULT_TEST_GLOBS` into `_common.py`, use `config.get("testGlobs") or DEFAULT_TEST_GLOBS` in both hooks, and add a test for a test-only commit with empty `testGlobs`.

Found in the live check that verified the fixes above, in headless sessions with the plugin loaded from a copy of the working tree, under `bypassPermissions`, against a throwaway repo whose feedback command was red:

- [x] bb6907e hooks/scripts/red_guard.py:51 A command that creates its own source change before committing lands on red: in `echo 1 >> app.py && git commit -am f1` the hook reads `git status` before the `echo` runs, sees no pending change, and skips the check as if only workflow documents and tests had changed. All six commit forms tried, the plain one included, landed. Fix: skip only when every other simple command in the call is a `cd`, a git `add`, `rm`, `mv`, `status`, `diff`, `log` or `show`, or a read-only filter, with no output redirected into a file, and when the pending set is not empty.
- [x] bb6907e hooks/hooks.json:27 `"if": "Bash(git *)"` kept the hook from running at all for `/usr/bin/git commit`, `bash -c "git commit"` and `eval 'git commit'`, though the script blocks all three when run directly; the spec's design note assumed `if` errs towards running the hook. Fix: drop the `if`; the script exits 0 at once on anything that is not a commit.

## Nits

- hooks/scripts/_common.py:171 When the directory taken from the command is not a git checkout, `commit_checkout` returns it anyway instead of falling back to the event's `cwd`; `shlex` leaves `$PWD` unexpanded, so `cd "$PWD" && git commit -am t` resolves to a missing directory, `load_config` returns None, and a red source commit lands (reproduced). Fix: when `rev-parse` fails for the parsed directory, retry with the event's `cwd`, then `CLAUDE_PROJECT_DIR`.
- hooks/scripts/red_guard.py:131 No test drives `guard` through the `code is None` branch, so requirement 9's block is covered only through `run_feedback` and `timeout_reason` called directly, and dropping the branch stays green. Fix: call `red_guard.guard` with `run_feedback` patched to return `(None, "")` and assert exit 2 and "570 seconds".
- skills/fix-bug/SKILL.md:18 Step 1 only notes whether the tree is clean, but step 7 is now blocked while any source file in the working tree is changed, so a tree that started with unrelated source edits hits a block with no route out. Fix: in step 1, stop when the tree has uncommitted source changes and ask the user to commit or stash them.
- skills/fix-bug/SKILL.md:42 "or `/toolkit:review` once it exists" survived `455befc`, which set out to drop such notes, and review has shipped. Fix: "or `/toolkit:review <NNNN>`".
- CHANGELOG.md:18 The 0.5.0 "Changed" section omits `455befc`'s skill edits (`implement` step 5 routes to `/toolkit:review`, `fix-bug` step 11 hands off to `/toolkit:postmortem`), and `[Unreleased]` is empty. Fix: one line each under 0.5.0 "Changed".

Two further nits dropped by the cap: `quoted_tail` prints "Last 0 lines of output:" and a blank line when the feedback command prints nothing; `spec.md:79` still marks two settled policy conflicts as open. Both were fixed with the findings above, as were `cd <dir>; git commit`, the `implement` step 5 contradiction, and a hang found by an earlier stand-in review: `run_feedback` waited for the output pipe, so a green command that left a background child running was held to the 570-second limit and then blocked. The spec and plan carry an amendment of 2026-10-23 for the behaviour that changed.

## Out of pass

- `spec.md:43` requirement 2 reads as a precedence order (`git -C`, then `cd`, then `cwd`), but `commit_checkout` composes them as the shell does, so `cd A && git -C B commit` lands in `A/B`; the code matches git and the spec wording no longer describes what shipped.
- `commit_checkout` honours only a leading `cd <dir> &&`; `cd <dir>; git commit` resolves to the directory before the `cd` (`_common.py:154`).
- `skills/implement/SKILL.md:55` says the user pushes and opens the pull request, then that `/toolkit:review` comes before it is opened; `skills/guide/SKILL.md:33` says review comments on the pull request, which needs it to exist.
- The `docs/` skip (`red_guard.py:51`) lets code under `docs/` (a docs site) commit on red; the glossary draws the line there on purpose, so this is a scope question.
- No pull request exists, so whether it states its merge danger honestly is unchecked.
- `claude plugin validate .` warns that the root `CLAUDE.md` is not loaded as plugin context; this predates the change.

## Waivers

<none yet>
