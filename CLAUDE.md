# claude-code-toolkit

This repo is the `toolkit` Claude Code plugin, served from its own marketplace `adamakhlaq`. Read `PHILOSOPHY.md` before changing any skill, agent or hook: every component exists to enforce one of its principles, and the "Enforced by" column there must stay accurate.

## Layout

- `.claude-plugin/`: `plugin.json` (name, version) and `marketplace.json` (one entry, source `./`). Names must match across both.
- `skills/<name>/SKILL.md`: user-invoked skills carry `disable-model-invocation: true` and a human-facing description. Model-invoked skills carry a trigger-rich description. No skill ever calls a user-invoked skill.
- `agents/<name>.md`: subagents with a tool allowlist.
- `hooks/hooks.json` and `hooks/scripts/*.py`: every hook reads `.claude/toolkit.json` from the consuming project and exits 0 with no output when it is absent. Python standard library only.
- `bin/toolkit-graph`: the deterministic graph tool. Python standard library only.
- `templates/`: files the skills copy into a consuming repo.
- `docs/changes/`, `docs/adr/`, `docs/incidents/`: this repo's own artifacts. `GLOSSARY.md` holds the workflow's vocabulary.
- `tests/`: unit tests for the hooks and the graph tool.

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Validate the plugin: `~/.nvm/versions/node/v25.3.0/bin/claude plugin validate .` (the `claude` on PATH is a work wrapper; use this binary)
- Run the eval suite: `~/.nvm/versions/node/v25.3.0/bin/claude plugin eval . --runs 1 --no-publish --scaffold` from a clone, before a release. It costs tokens. Do not pass `--allow-tools Bash`: the runner refuses the Bash grant on this machine because of credential files it cannot sandbox.
- Try it live: `~/.nvm/versions/node/v25.3.0/bin/claude --plugin-dir .` from any other repo

## Workflow for this repo

- Behaviour changes (a new or changed skill, hook, agent, template or graph command) go through a change under `docs/changes/` with intent, spec and plan. Typos, wording and README fixes go straight to a branch.
- Main accepts pull requests only. Branch as `change/<NNNN>-<slug>`.
- Every release bumps `version` in `.claude-plugin/plugin.json`, moves the `[Unreleased]` entries in `CHANGELOG.md` under the new version, and tags `v<version>` after merge.
- When a skill, hook or agent is added, renamed or removed: update the README's component tables, the spec of the change that introduced it, and the "Enforced by" column in `PHILOSOPHY.md`.

## Never

- Never use an em dash. Never hard-wrap Markdown prose; one paragraph per line.
- Never add a dependency to a hook or the graph tool. Standard library only, so consumers need nothing but `python3` and `git`.
- Never make a hook act on a project without `.claude/toolkit.json`.
- Never put per-project configuration in the plugin. It belongs in the consuming repo's `toolkit.json`.
- Never commit or tag without the maintainer's explicit go-ahead.
