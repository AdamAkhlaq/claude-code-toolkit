# claude-code-toolkit

This repo is the `toolkit` Claude Code plugin, served from its own marketplace `adamakhlaq`. Read `PHILOSOPHY.md` before changing any skill, agent or hook: every component exists to enforce one of its principles, and the "Enforced by" column there must stay accurate.

## Layout

- `.claude-plugin/`: `plugin.json` (name, version) and `marketplace.json` (one entry, source `./`). Names must match across both.
- `skills/<name>/SKILL.md`: user-invoked skills carry `disable-model-invocation: true` and a human-facing description. Model-invoked skills carry a trigger-rich description. No skill ever calls a user-invoked skill.
- `agents/<name>.md`: subagents with a tool allowlist.
- `hooks/hooks.json` and `hooks/scripts/*.py`: every hook reads `.claude/toolkit.json` from the consuming project and exits 0 with no output when it is absent. Python standard library only.
- `bin/toolkit-graph`: the deterministic graph tool. Python standard library only.
- `templates/`: files the skills copy into a consuming repo.
- `docs/changes/`, `docs/adr/`, `docs/incidents/`: this repo's own artifacts. `docs/backlog.md` holds follow-ups not yet taken into a change. `GLOSSARY.md` holds the workflow's vocabulary.
- `tests/`: unit tests for the hooks and the graph tool.

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Set up once: `npm ci`, which installs the pinned Prettier that `format-lint` runs on Markdown and JSON through `npx --no-install prettier`. Node is development tooling only; consumers of the plugin need nothing but `python3` and `git`.
- Validate the plugin: `~/.nvm/current/bin/claude plugin validate .` (the `claude` on PATH is a work wrapper; use this binary, which `~/.nvm/current` keeps pointing at nvm's active Node)
- Run the eval suite: `~/.nvm/current/bin/claude plugin eval . --runs 1 --no-publish --scaffold` from a clone, before a release. It costs tokens. Do not pass `--allow-tools Bash`: the runner refuses the Bash grant on this machine because of credential files it cannot sandbox.
- Try it live: `cc --plugin-dir .` from this repo or any other. `cc` is the maintainer's shell function for their personal Claude Code account and passes arguments through. Work on this repo itself runs this way, so the toolkit's skills, agents and hooks are live. `~/.nvm/current/bin/claude --plugin-dir .` also works.

## Workflow for this repo

- Behaviour changes (a new or changed skill, hook, agent, template or graph command) go through a change under `docs/changes/` with intent, spec and plan. Typos, wording and README fixes go straight to a branch.
- Main accepts pull requests only. Branch as `change/<NNNN>-<slug>`.
- Every release bumps `version` in `.claude-plugin/plugin.json`, moves the `[Unreleased]` entries in `CHANGELOG.md` under the new version, and tags `v<version>` after merge.
- When a skill, hook or agent is added, renamed or removed: update the README's component tables, the spec of the change that introduced it, and the "Enforced by" column in `PHILOSOPHY.md`.
- When a review finds a shell form a hook's reader misses, check its whole family in bash and zsh with a stub program (quoting, expansion, heredoc delimiters, nested substitutions, comments, and each shell's own grammar, such as zsh's `repeat`, `coproc`, `foreach`, `function f {`, `case x {`, `;|` and glob groups) before fixing, not only the reported case, and probe the new code's own boundaries (each new branch's trigger characters, ranges and escapes) against bash before handing it on.
- When a reader function gains a caller whose answer decides what other readers skip, probe every branch of it again as a bypass: a misread that used to make a hook read more now hides text.
- A reader step that rewrites or matches the text (joining lines, a keyword, an operator, a comment) applies only where the shell applies it: probe each one inside single quotes, `$'...'`, double quotes, backticks, heredoc bodies, comments, `[[ ]]`, arithmetic and `case` patterns, with an escaped `\\` before it, straight after `{` or a reserved word with no space between (`if((`, `!((`), and in both command and argument position, before handing it on.
- A scan that decides where a span ends (a parenthesis, a backtick, arithmetic) steps over exactly the constructs each shell steps over there - quotes, `${...}`, `$'...'`, backticks, `$(...)`, heredocs: probe it with each one holding the closing character, in bash and zsh.
- A reader state that a token switches on, such as a `case` pattern on `;;`, `[[ ]]` or a redirection's target, holds only while the construct that opens it is open at that depth: probe each switching token where its opener is absent, inside a `$(...)` that holds none, and across each bracket the reader pushes and pops, and run everyday forms that hold the state, such as function and `case` bodies, through the hooks before handing it on.
- A decision taken outside a gate that widens or reshapes a change, such as a scope widening or a process rule committed on its branch, is recorded as a dated amendment in the change's intent in the same commit.
- When a ticket that closes review findings merges, tick their boxes in `review.md` with its fix commit in the same run.
- A follow-up found while working a ticket or a review gets a home in the same change: a ticket in the graph or a line in `docs/backlog.md`, never only a mention in Evidence.

## Never

- Never use an em dash. Never hard-wrap Markdown prose; one paragraph per line.
- Never add a dependency to a hook or the graph tool. Standard library only, so consumers need nothing but `python3` and `git`.
- Never make a hook act on a project without `.claude/toolkit.json`.
- Never recognise a shell command in a hook by matching the raw Bash string. Read it with `_common.shell_tokens` and test every word that could name a program, so rewording (`cd . &&`, a newline, `sudo`, `bash -c`, `$(...)`) cannot hide it. A hook that cannot finish reading a command blocks it rather than letting it through.
- Never put per-project configuration in the plugin. It belongs in the consuming repo's `toolkit.json`.
- Never commit or tag without the maintainer's explicit go-ahead.
