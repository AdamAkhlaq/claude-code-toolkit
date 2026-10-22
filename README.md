# claude-code-toolkit

An opinionated engineering workflow for [Claude Code](https://docs.claude.com/en/docs/claude-code/overview), packaged as the `toolkit` plugin. It takes a piece of work from an idea to merged code through human-gated artifacts, runs the build as a ticket graph, and uses hooks to enforce the rules that must always hold.

Every component serves a principle in [PHILOSOPHY.md](./PHILOSOPHY.md). Read that first. [GLOSSARY.md](./GLOSSARY.md) defines the words used throughout.

## Install

```bash
claude plugin marketplace add AdamAkhlaq/claude-code-toolkit
claude plugin install toolkit@adamakhlaq
```

Then, once per repository:

```
/toolkit:setup
```

It inspects the repo, confirms a few values with you, and writes `.claude/toolkit.json` plus the `docs/` tree, `GLOSSARY.md` and `REVIEW.md`. Nothing in the plugin acts on a repo until that file exists.

To pick up a new version: `claude plugin update toolkit@adamakhlaq`.

Requirements in the consuming repo: `python3` and `git` on the path. Nothing else.

## The workflow

```
intent  ──▶  spec  ──▶  plan  ──▶  tickets  ──▶  implement  ──▶  review  ──▶  pr-sweep
 gate         gate       gate        gate        ticket graph     3 passes     green PR
```

Each stage commits an artifact under `docs/changes/<NNNN>-<slug>/`. The build stage decomposes the plan into a graph of tracer-bullet tickets and hands each ready ticket to an executor, which works it in its own worktree, proves it with a test, and merges after an independent verifier passes.

## Status

This is version 0.4.0: every skill, agent and hook in the design is live. A change goes from an idea to a green pull request, bugs are reproduced before they are fixed, findings and incidents re-enter as intents, and the plugin's own eval suite checks that the skills do what they say.

| Skill          | Invocation | Status | What it does                                                           |
| -------------- | ---------- | ------ | ---------------------------------------------------------------------- |
| `setup`        | user       | 0.1.0  | Prepares a repo: config, docs tree, glossary, review passes            |
| `guide`        | user       | 0.2.0  | Tells you which skill fits your situation                              |
| `intent`       | user       | 0.2.0  | Turns any input into a committed `intent.md`                           |
| `spec`         | user       | 0.2.0  | Writes `spec.md` from the intent, flags policy conflicts               |
| `plan`         | user       | 0.2.0  | Plan mode with interrogation, records seams and the execution decision |
| `tickets`      | user       | 0.2.0  | Decomposes the plan into a validated ticket graph                      |
| `implement`    | user       | 0.2.0  | Walks the frontier, dispatches executors, merges verified tickets      |
| `fix-bug`      | user       | 0.3.0  | Reproduces as reported, locks tests, fixes                             |
| `review`       | user       | 0.3.0  | Three review passes from `REVIEW.md`                                   |
| `pr-sweep`     | user       | 0.3.0  | Resolves comments and failing checks until green                       |
| `diagnose`     | user       | 0.4.0  | Read-only diagnosis of a finding, written as a new intent              |
| `postmortem`   | user       | 0.4.0  | Incident record, follow-up intent, eval case                           |
| `eval-case`    | user       | 0.4.0  | Turns a task or incident into an eval                                  |
| `policy-skill` | user       | 0.4.0  | Encodes one policy as a skill                                          |
| `grilling`     | model      | 0.2.0  | Numbered question rounds with recommended answers                      |
| `glossary`     | model      | 0.2.0  | Coins and challenges terms in `GLOSSARY.md`                            |
| `verify`       | model      | 0.2.0  | Runs the feedback command and records evidence                         |
| `claude-md`    | model      | 0.2.0  | Creates or trims `CLAUDE.md`, captures repeated corrections            |

Agents: `researcher` (read-only facts with citations), `implementer` (one ticket in one branch) and `verifier` (fresh-context pass or reopen) and `reviewer` (one `REVIEW.md` pass per context).

## Hooks

All hooks read `.claude/toolkit.json` in the consuming repo and do nothing when it is absent.

| Hook            | Fires on            | Config key              | Effect                                                                                              |
| --------------- | ------------------- | ----------------------- | --------------------------------------------------------------------------------------------------- |
| `protect-paths` | before Edit, Write  | `protectedPaths`        | Blocks the edit and explains the route                                                              |
| `lock-tests`    | before Edit, Write  | `testGlobs`             | Blocks test edits while `.claude/.tests-locked` exists                                              |
| `secret-guard`  | before `git commit` | `secretAllowlist`       | Blocks a commit that adds a credential-looking line                                                 |
| `ticket-sync`   | before `git commit` | none                    | Asks when source is staged but the in-progress change's folder is not                               |
| `deploy-gate`   | before Bash         | `gatedCommands`         | Blocks matching commands unless `RELEASE_AUTHORIZED` is set or `.claude/.release-authorized` exists |
| `format-lint`   | after Edit, Write   | `formatters`, `linters` | Runs matching commands on the changed file, surfaces failures                                       |

A gated command is a one-way door. When `deploy-gate` blocks one, the agent prepares everything up to that step and stops; a human then authorises the release for the session with `export RELEASE_AUTHORIZED=1`, or for the checkout by creating `.claude/.release-authorized`, and the same command goes through. Both routes are named in the block message, and the hook fires inside a real session with the plugin loaded, not only in the unit tests.

## Configuration

`.claude/toolkit.json`, written by `setup`:

```json
{
  "protectedPaths": ["db/migrations/", "generated/", ".env"],
  "formatters": { "*.{ts,tsx,js,json,md}": "npx prettier --write {file}" },
  "linters": { "*.{ts,tsx}": "npx eslint {file}" },
  "testGlobs": ["*.test.ts", "tests/"],
  "feedbackCommand": "npm test",
  "gatedCommands": ["^(npm|pnpm) run deploy", "terraform apply"],
  "secretAllowlist": ["tests/fixtures/"],
  "concurrency": 3,
  "tracker": "local"
}
```

Path patterns are globs. A pattern ending in `/` matches everything beneath that directory. A pattern with no `/` also matches by file name anywhere in the tree.

## The graph tool

`bin/toolkit-graph` is a dependency-free Python script the skills call. It is also useful by hand:

```bash
python3 "$PLUGIN/bin/toolkit-graph" new rate-limit          # docs/changes/0007-rate-limit/
python3 "$PLUGIN/bin/toolkit-graph" validate 0007           # cycles, unresolved edges, file overlap
python3 "$PLUGIN/bin/toolkit-graph" frontier 0007           # tickets ready to start
python3 "$PLUGIN/bin/toolkit-graph" status 0007
python3 "$PLUGIN/bin/toolkit-graph" render 0007             # Mermaid
```

where `$PLUGIN` is the installed plugin's root. From inside a skill or hook that is `${CLAUDE_PLUGIN_ROOT}`.

## Development

```bash
python3 -m unittest discover -s tests -v      # hooks, graph tool, component and eval suite shape
claude plugin validate .                       # manifests
claude --plugin-dir /path/to/this/repo         # load the working tree in another project
claude plugin eval . --runs 1 --no-publish --scaffold   # the eval suite under evals/, costs tokens
```

The GitHub Action in `.github/workflows/validate.yml` runs the unit tests and `claude plugin validate .` on every pull request and push to main. The eval suite is not run in CI: it costs money and needs credentials, so run it by hand before a release. Each case under `evals/` is a `prompt.md` plus graders, the format `claude plugin eval` reads; `evals/results/` is ignored.

Changes to behaviour go through the workflow itself: see `docs/changes/`. Main accepts pull requests only. Releases bump `.claude-plugin/plugin.json`, update `CHANGELOG.md`, and tag.

## License

MIT.
