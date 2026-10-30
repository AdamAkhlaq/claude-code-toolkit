# Changelog

All notable changes to this plugin are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- `deploy-gate` matches each `gatedCommands` pattern against the whole Bash call and against a line from every unquoted word in it that could name a program, so a pattern anchored with `^` catches a gated command after `&&`, `;`, `|` or a newline, named by path, behind an assignment, a wrapper such as `sudo` or `env`, or a keyword such as `then`, after git's global options, and inside `bash -c` (whatever options come first), `eval`, `$(...)` or backticks, quoted or not, including a `$(...)` that holds a quoted `)` or a `case`, and one in the body of a heredoc whose delimiter is unquoted, where the shell runs it. A word in quotes names no program, so a mention such as `echo "git tag v1"` is not gated. Each simple command is matched whole, however long, every `^` or `\A` in a pattern anchors at each program word, so `^npm publish|^gh release ` catches `X=1 gh release create v1`, a call too long to read (over 100,000 words or 300,000 characters, or nested too deep) or one the hook fails to read is blocked rather than half read, every `eval` and shell word is read into, so `SHELL=/bin/bash eval '...'` or a wrapper's `-c` argument hides nothing, nesting counts against that budget, and the hook entry has a timeout with `"onFailure": "block"`, so the gate never fails open. The reader ends a span where bash does: `$'a\'b'` is one ANSI-C quoted word, a heredoc's delimiter is the whole word after `<<` (`<<E'OF'` ends at `EOF`, `<<E:OF` at `E:OF`), a backtick span ends at the first unescaped backtick and its nested spans are read, and a `)` in a `#` comment or a heredoc body inside `$(...)` does not end it. A `$(...)`, backtick span or `${...}` inside double quotes is read in its own quoting context, as bash and zsh read it, so a quote inside it, such as the `'` in `"$(printf "%s" "a'b")"`, cannot end the outer string and hide a later command, and a `<<` inside `$((...))` there is a shift, not a heredoc. Inside such a substitution `case` and `esac` count only where bash reads them as reserved words, so `"$(cat case.txt)"` does not open a `case`, a here-string `<<<` and a `<<` in `((...))`, `$((...))` or `$[...]` are never heredocs, and `$$` before `(` or `{` is the PID followed by text, as both shells expand it. A call whose double-quoted substitution never closes is blocked with a message saying so, rather than read as if it ran to the end of the call. A word is read as bash expands it: `$'...'` escapes are decoded, a NUL ending the word, and unquoted braces are expanded, so `$'\x67it' tag v1`, `{git,tag} v1` and `{g..g}it tag v1` are caught, while a quoted brace, `${...}` and `{ ...; }` are left alone; braces that expand past 10,000 words block the call as too long to read. A `$'...'` span ends where bash and zsh end it whatever its escapes, so `$'\c'` and `$'\c\\'` close at their last quote, a letter range's characters that are not letters, such as the backslash and backtick in `{Z..a}`, cannot open or close a quote, `<<$'EOF'` ends at a line `EOF`, and a `$'` in an unquoted heredoc body no longer hides a `$(...)` after it. A call bash and zsh read differently, `$$'` before a backslash, a heredoc delimiter `$"EOF"` or `$$'EOF'`, a `'...'` span inside a double-quoted `${...}` holding a character that changes where it ends, such as `}` or `"`, or an unbalanced `(` or `{` after `$$` in double quotes, which bash's parser takes as opening a span, is blocked with a message saying so. Before, `cd . && git tag v1` ran without release authorisation. This is change 0003.
- `_common.shell_tokens` decodes `$'...'` escapes and expands unquoted braces as bash does, so `red-guard` checks `$'\x67it' commit -am x` and `git {commit,-am,x}`, and `red-guard` blocks a Bash call it cannot read, such as one whose braces expand past 10,000 words, that bash and zsh read differently, or whose double-quoted substitution never closes, rather than letting it through; in a project without a `feedbackCommand` it stays silent. That message now starts "Blocked: red-guard could not read this Bash call", since the call may not commit at all.
- `_common.shell_tokens` reads a substitution inside double quotes in its own quoting context, so a quote inside `"$(...)"`, backticks or `"${...}"` no longer hides a later `git commit` from `red-guard`, `secret-guard` or `ticket-sync`.
- `secret-guard` and `ticket-sync` block a Bash call they cannot read, such as one whose braces expand past 10,000 words, that bash and zsh read differently, or whose double-quoted substitution never closes, rather than exiting with an error that lets a commit in it run unscanned; `ticket-sync` does so only while a change is in progress, and both stay silent without `.claude/toolkit.json`.
- `_common.find_commit` finds a shell's `-c` script after any options, so `red-guard` also checks `bash --norc -c "git commit ..."`.
- `_common.shell_tokens` keeps a newline outside quotes as a control operator, joins backslash line continuations, and leaves out `#` comments and heredoc bodies, so `red-guard` also reads a multi-line command as separate commands and no longer reads a heredoc commit message as shell. A comment keeps the newline after it, a `<<` shift inside `$((...))` is not read as a heredoc, a heredoc whose closing line never comes keeps its body, a separator joined to a redirect (`;>`, `&&>`) still separates, a backtick separates like `$(`, a command shlex cannot parse, such as `$'it\'s'`, is still split at its operators with each quoted span kept whole, a `#` after an escaped space or inside `${...}` does not start a comment, a `<<` inside `$[...]` is a shift, and a backslash-newline joins the words either side as bash does, so none of these can hide a later command from `deploy-gate` or `red-guard`.
- `_common.shell_tokens` reads `$'...'` with its escaped quotes and takes a heredoc's delimiter as the whole word after `<<`, so `red-guard` checks `echo $'a\'b'; git commit -am x` and a commit after `cat <<E'OF'`, and finding a heredoc's closing line no longer costs a scan of the whole call per heredoc.
- `_common.shell_script` finds a shell's `-c` script past any options after `-c` and a `--`, and `ksh`, `mksh`, `csh`, `tcsh` and `fish` count as shells.

## [0.5.0] - 2026-10-22

No commit lands while the feedback command is red. The rule was text the executor could miss, and once did; it is now a hook. This is change 0002.

### Added

- `red-guard` hook: before a `git commit` Claude attempts, however the command is worded, runs `feedbackCommand` in the checkout the commit lands in, worktrees included, and blocks the commit while it is red, quoting the last 40 lines of output. Only the project's own checkouts are checked; a commit in another repository never runs that repository's command. A commit that changes only workflow documents and test files skips the check when nothing else in the command can change a file first, so `fix-bug` can commit its failing regression test. A feedback command that does not finish in 570 seconds counts as red, its whole process group is killed, and the hook entry fails closed. Proven in live headless sessions, including under `bypassPermissions` and from a worktree.
- `_common.commit_checkout`: resolves the checkout a commit lands in from the event's `cwd`, a leading `cd`, and `git -C`. `_common.is_git_commit` now reads the command with a shell tokeniser, so `secret-guard` and `ticket-sync` also recognise commits written as `a;git commit`, `/usr/bin/git commit`, `bash -c "git commit"` or `eval 'git commit'`.
- Glossary terms: red, workflow document.
- A component test that every hook is linked in PHILOSOPHY's "Enforced by" column, and a test pinning `red-guard`'s hook entry.

### Changed

- `implementer`, `verify` and `fix-bug` name `red-guard` where they state the rule; `fix-bug` says why its failing-test commit passes.
- `implement` ends by pointing at `/toolkit:review` before the pull request, and `fix-bug` reports the same next step and hands an incident off to `/toolkit:postmortem`.
- `fix-bug` stops at the start when source files have uncommitted changes, which would block its failing-test commit.
- `lock-tests` takes its default test patterns from `_common.py`, shared with `red-guard`.
- `PHILOSOPHY.md` links `red-guard` under "Skills advise, hooks enforce" and `ticket-sync`, which was missing, under "Artifacts are tool-agnostic".

## [0.4.0] - 2026-10-22

Phase 3: maintain and hardening. The loop closes: findings from running software and incidents re-enter the workflow as intents, lessons become eval cases, policies become skills, and the plugin tests itself. This completes change 0001.

### Added

- `diagnose` skill: read-only diagnosis of a finding from running software, written as a new `intent.md`.
- `postmortem` skill and `templates/incident.md`: a blameless incident record under `docs/incidents/`, follow-up intents, and an eval case.
- `eval-case` skill and `templates/eval-case.md`: a prompt plus graders under `evals/` in the format `claude plugin eval` runs.
- `policy-skill` skill and `templates/policy-skill.md`: one policy as a model-invoked skill in the repo's `.claude/skills/`, with two trigger tests.
- `evals/`: the plugin's own eval suite, three cases that pass with the plugin and fail without it.
- `.github/workflows/validate.yml`: unit tests and `claude plugin validate .` on every pull request and push to main. Validation needs no credentials.
- A unit test pinning the deploy gate's block message, after the gate was exercised end to end in a real session.
- Glossary terms: incident, follow-up, eval case, grader.

### Changed

- `tests/test_components.py` checks the shape of every eval case: a named prompt, at least one grader of a known type, and at least one deterministic grader.

## [0.3.0] - 2026-10-22

Phase 2: test and deploy. Bugs are reproduced before they are fixed, reviews run as independent passes, and pull requests are swept to green. This is the first phase built through the workflow itself: four tickets under `docs/changes/0001-plugin-overhaul/tickets/`, each verified in a fresh context before merge.

### Added

- `fix-bug` skill: reproduce as reported, narrow to the fastest failing test, commit it, lock tests with `.claude/.tests-locked`, fix, verify, unlock. Leaves a change folder with the report as origin and the regression test as its one ticket.
- `reviewer` agent and `review` skill: one read-only reviewer per pass in `REVIEW.md`, findings merged into `docs/changes/<change>/review.md` and posted to the pull request, every Important finding fixed or waived by name.
- `pr-sweep` skill: works unresolved review threads and failing checks until the pull request is green, pushes only with approval, stops on design-level comments, repeated check failures and merge conflicts.
- `templates/REVIEW.md` states the finding format reviewers return.
- Glossary terms: reproduction, regression test, test lock, review pass, waiver.

### Changed

- `tests/test_components.py` states the push rule directly: a user-invoked skill either never pushes, or pushes only with approval and never by force.

### Fixed

- `toolkit-graph` reads a ticket whose `files` or `blocked_by` list a formatter wrapped over several lines, which prettier does for long lists.

## [0.2.0] - 2026-10-22

Phase 1: plan through build. The four gates and the build loop are live, so a change can go from an idea to merged tickets inside one plugin.

### Added

- User-invoked skills `guide`, `intent`, `spec`, `plan`, `tickets` and `implement`: the four gates and the graph walk.
- Model-invoked skills `grilling`, `glossary`, `verify` and `claude-md`: the discipline the gates and executors share.
- Agents `researcher`, `implementer` and `verifier`.
- `templates/adr.md` for one-way-door decisions recorded by `plan`.
- `tests/test_components.py`: structural checks that every skill and agent keeps the plugin's invocation rules and that the README and `PHILOSOPHY.md` tables stay complete.

### Changed

- Branch and commit conventions for the build: ticket branches are `ticket/<NNNN>-<Tn>`, ticket commits carry a `Ticket:` trailer, and `single` execution works in the main working tree. Recorded as an amendment to the spec of change 0001.

## [0.1.0] - 2026-10-21

Phase 0: plumbing. The plugin installs, the hooks enforce, the graph tool runs, and `setup` prepares a repo. No workflow skills yet.

### Added

- Plugin and marketplace manifests. Install as `toolkit@adamakhlaq`.
- `setup` skill: prepares a repo with `.claude/toolkit.json`, the `docs/` tree, `GLOSSARY.md` and `REVIEW.md`.
- Hooks, each a no-op until `.claude/toolkit.json` exists: `protect-paths`, `format-lint`, `secret-guard`, `lock-tests`, `ticket-sync`, `deploy-gate`.
- `bin/toolkit-graph`: `new`, `frontier`, `validate`, `status` and `render` over a change's ticket graph.
- Templates for `intent.md`, `spec.md`, `plan.md`, tickets, `REVIEW.md` and `toolkit.json`.
- `PHILOSOPHY.md`, `GLOSSARY.md`, and the repo's own first change under `docs/changes/0001-plugin-overhaul/`.

[Unreleased]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AdamAkhlaq/claude-code-toolkit/releases/tag/v0.1.0
