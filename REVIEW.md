# Review

How this repository's changes are reviewed. The `review` skill runs each pass below in its own context and merges the findings. This repo is a Claude Code plugin: skills and agents are Markdown the model reads, hooks and the graph tool are standard-library Python that runs on every matching tool call in a consuming repo. Keep the nit cap.

## Passes

### 1. Bugs and logic

Does the change do what the code claims, on the happy path and at the edges? For hooks and `bin/toolkit-graph`: exit codes (0 lets the call through, 2 blocks it, an `ask` payload asks the user), a silent exit 0 when `.claude/toolkit.json` is absent, exceptions that would block an unrelated tool call, subprocesses without a timeout, shell strings parsed by splitting on whitespace, paths resolved against the wrong checkout, and tests that pass without exercising the change. For skills and agents: steps that contradict each other or another component, a stop condition with no route out, and instructions a fresh agent could not follow without the conversation.

### 2. Security

Does the change move trust boundaries? Hooks run commands from the consuming repo's `toolkit.json` and see every Bash command and edited path. Look for a path or command string reaching a shell unquoted, a hook that prints a secret it matched, a block that can be bypassed by rephrasing the command in a form the threat model below counts as plausible, broadened agent tool allowlists, new network calls, and any dependency beyond the Python standard library and `git`.

### 3. Compliance with the spec and plan

Read `spec.md` and `plan.md` for this change. Does the diff implement every requirement, and nothing beyond scope? Are tests at the seams the plan agreed? Is each ticket's `proves` test present and meaningful? Does the pull request state its merge danger honestly? Then the repo's own rules: `PHILOSOPHY.md`'s "Enforced by" column, the README component tables and `CHANGELOG.md` match what shipped; user-invoked skills carry `disable-model-invocation: true` and no skill calls one; no em dash and no hard-wrapped Markdown prose.

## Threat model

The Bash hooks guard against an agent's ordinary mistakes, not against a caller set on hiding a command from them. A bypass is plausible when an agent could write that form while doing ordinary work: a gated or committing command after `&&`, `;`, `|` or a newline, named by path, behind a wrapper, an assignment or a keyword, inside `bash -c`, `eval`, a substitution or a heredoc, or quoted, escaped or split the way a script commonly is. A form that exists only to defeat the reader is contrived, such as a case separator with no `case` (`echo $(:;;)#; git tag v1`), a glob group as a redirection's target (`> (a|#b)`), or a `#` glued to an operator inside a substitution (`$(echo a;#b)`). The hard guarantee against a deliberate bypass lies outside the hooks, as the README says: a permissions deny rule, server-side protection such as a tag ruleset, or release credentials kept out of the session.

## Severity

**Important**: introduced by the delta under review, and breaks behaviour, leaks data, breaches a policy, or diverges from the spec. A hook bypass is Important only in a form the threat model counts as plausible; a contrived one is a Nit. A defect counts as introduced when the delta adds it, or makes an older one reachable by a form that did not reach it before. Every Important finding must be fixed or explicitly waived by the code owner before merge.

**Out of pass**: a defect already present at the base of the delta, checked by running the finding against the base commit. It does not block the merge. The reviewer lists it under Out of pass, and the review gives it a line in `docs/backlog.md` in the same change, so it is kept without starting another round.

**Nit**: everything else. At most five nits per review, chosen by value. Skip anything a formatter, linter or CI check already enforces, and skip generated paths.

## Finding format

Each reviewer returns findings as one line each: `[Important|Nit] <path>:<line> <what is wrong>. <why it matters>. Fix: <the smallest change that resolves it>.` A finding without a path and line is not a finding. The `review` skill merges the passes into `docs/changes/<change>/review.md`, where every Important finding is a checkbox closed by a fix commit or a named waiver.

## Not reviewed

- `evals/results/`, which runs write and git ignores.
- Markdown and JSON formatting, which prettier owns.
- Anything `tests/` or `claude plugin validate .` already fails on in CI.

## Feedback loop

A flag raised in two separate reviews is a pattern. Add a line to `CLAUDE.md` so it stops recurring, and consider an eval case.
