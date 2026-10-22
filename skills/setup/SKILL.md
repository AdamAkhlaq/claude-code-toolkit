---
name: setup
description: Prepare this repository for the toolkit workflow. Run once per repo, before any other toolkit skill.
disable-model-invocation: true
---

# Setup

Prepare the current repository so the toolkit's hooks, graph tool and workflow skills have what they need. Everything you create is reviewed by the user before it is committed. Never commit.

The plugin's templates live at `${CLAUDE_PLUGIN_ROOT}/templates/`. The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`.

## Steps

1. **Check for an existing setup.** If `.claude/toolkit.json` already exists, read it, tell the user what is configured, and ask whether they want to re-run setup or stop. Do not overwrite a config silently.

2. **Learn the repository.** Find out, by looking rather than asking:
   - The language, package manager and build tool.
   - The single command that runs the tests and exits non-zero on failure. This becomes `feedbackCommand`. Run it once to confirm it works and note what healthy output looks like.
   - The formatter and linter, and the file types each applies to.
   - Where tests live and how test files are named.
   - Generated, vendored or frozen paths that should never be edited by an agent. Look for `generated/`, `vendor/`, lockfiles, migrations that have already run, and anything a `CODEOWNERS` or contributing guide calls out.
   - Commands that deploy, publish, or touch production. These become `gatedCommands`.
   - Any existing `GLOSSARY.md`, `REVIEW.md`, `docs/adr/`, or `docs/changes/` so you extend rather than replace.

3. **Confirm the config with the user.** Present the values you inferred as one numbered list and ask them to confirm or correct in a single round. Recommend an answer for each. Then write `.claude/toolkit.json` from `${CLAUDE_PLUGIN_ROOT}/templates/toolkit.json` with the confirmed values. Keys:
   - `protectedPaths`: globs or directory prefixes ending in `/`. Edits to these are blocked.
   - `formatters`, `linters`: maps from a glob to a command with a `{file}` placeholder, run after every edit to a matching file.
   - `testGlobs`: patterns that identify test files, used by the test lock during bug fixes. Leave empty to use the built-in defaults.
   - `feedbackCommand`: the test command from step 2.
   - `gatedCommands`: regular expressions matched against shell commands. A match is blocked until a human authorises a release.
   - `secretAllowlist`: paths where credential-looking strings are expected, such as fixtures.
   - `concurrency`: how many tickets may run at once. Default 3.
   - `tracker`: `local`. Tickets live in the repo.

4. **Create the docs tree.** `docs/changes/`, `docs/adr/` and `docs/incidents/`, each with a `.gitkeep` if empty. Do not create `evals/` until there is an eval to put in it.

5. **Create `GLOSSARY.md` at the repo root** if it does not exist. Seed it with five to ten terms that the codebase already uses with a specific meaning. Find them in the code and the docs rather than inventing them. Each entry is one line: the term in bold, then its definition in the project's own words.

6. **Create `REVIEW.md` at the repo root** from `${CLAUDE_PLUGIN_ROOT}/templates/REVIEW.md` if it does not exist. Adjust the passes to anything project-specific you learned, such as a compliance rule or a protected data type. Keep the nit cap.

7. **Add the definition of done to `CLAUDE.md`.** If the repo has a `CLAUDE.md`, propose a short section stating: the feedback command, what its healthy output looks like, and that a change is done only when that command's output is quoted as evidence. Show the proposed text and add it only when the user agrees. If there is no `CLAUDE.md`, say so and suggest running `/init` first; do not create one here.

8. **Propose a permissions allowlist.** List the read-only and inner-loop commands the repo runs constantly (the feedback command, the formatter, `git status`, `git diff`, the package manager's install) as `Bash(...)` entries for `.claude/settings.json`. Show the list; do not write it. Permissions are the user's to set.

9. **Verify.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" new --dry-run setup-check` and confirm it prints `docs/changes/0001-setup-check` (or the next id if changes already exist). Then confirm the hooks are live by stating which ones now apply: protected paths and the test lock on edits, secret scanning and ticket sync on commits, the deploy gate on gated commands, and formatting and linting after edits.

10. **Report.** One short summary: the files created or changed, the config values, and the first thing to do next, which is `/toolkit:intent` for the first piece of work.

## Rules

- Infer first, ask second. Only ask about what you could not find.
- One round of questions, numbered, each with a recommended answer.
- Never overwrite an existing `GLOSSARY.md`, `REVIEW.md` or `CLAUDE.md` section. Extend them.
- Never commit. Leave the changes staged or unstaged as the user prefers, and say which.
