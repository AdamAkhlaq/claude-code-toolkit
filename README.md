# claude-code-toolkit

A personal collection of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) extensions — skills, agents, commands, and hooks — packaged so they can be installed on any machine with one command, or borrowed piece by piece.

## What this is

Claude Code can be extended with reusable building blocks:

- **Skills** — reusable workflows and knowledge that Claude applies automatically when relevant, or that you trigger by name.
- **Agents** — specialised sub-assistants that run in their own context and handle a focused job.
- **Commands** — explicit slash-command shortcuts.
- **Hooks** — scripts that run automatically on Claude Code events.

Normally these live scattered across your `~/.claude/` directory and have to be rebuilt by hand every time you set up a new machine. This repo packages them as a **Claude Code plugin**, distributed through a **marketplace** (which is just this Git repo). That means the whole set can be added in one step, kept up to date with a single command, and shared with anyone who wants to use it.

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) installed.

## Using it as a plugin (recommended)

This is the cleanest way: components install into a managed cache, stay versioned, and can be updated or removed cleanly.

Inside a Claude Code session, add this repo as a marketplace:

```
/plugin marketplace add adamakhlaq/claude-code-toolkit
```

Then browse and install what's on offer:

```
/plugin
```

Or install something directly by name:

```
/plugin install <name>@claude-code-toolkit
```

Once installed, the skills and agents become available automatically — Claude applies them when a task matches their description, and you can also invoke any skill or command explicitly as `/claude-code-toolkit:<name>` (plugin components are namespaced with the marketplace name to avoid clashes).

To update later, after new changes are pushed here:

```
/plugin marketplace update claude-code-toolkit
```

The same operations work from your terminal without opening a session, e.g.:

```
claude plugin marketplace add adamakhlaq/claude-code-toolkit
claude plugin install <name>@claude-code-toolkit
```

## Using it locally

There are two reasons you might prefer the local route: you want to try or modify things before installing, or you only want one piece rather than the whole set.

**Install from a local clone.** Clone the repo and add it as a marketplace by path — useful for offline use or when you want to tweak something first:

```
git clone https://github.com/adamakhlaq/claude-code-toolkit.git
```

```
/plugin marketplace add ./claude-code-toolkit
```

From there, install as above. Because it's a local checkout, your edits are picked up directly.

**Cherry-pick individual pieces.** If you just want a single skill or agent and not the whole plugin, copy it straight into your own Claude Code directory — a skill folder into `~/.claude/skills/`, or an agent file into `~/.claude/agents/` — and it'll load like any of your own. No plugin or marketplace involved.

## A note on scope

This is a personal toolkit that I maintain for my own use, shared in case any of it is useful to you. You're welcome to install it, fork it, or lift individual pieces. It evolves as my own workflow does, so expect it to change.
