# claude-code-toolkit

A browsable catalog of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview)
building blocks — project context, permissions, hooks, agents, and skills — that
you copy into your own project and make your own.

No plugin to install, no marketplace to add. The repo is shaped like a real
`.claude/` folder, so **the path of a file here is the path it goes in your
project.** Copy what you want, drop it in the same place, personalise, done.

## Quick start

Grab a piece straight into your project:

```bash
# from your project root — grab the CLAUDE.md template
curl -o CLAUDE.md \
  https://raw.githubusercontent.com/AdamAkhlaq/claude-code-toolkit/main/CLAUDE.md
```

Or browse the tree on GitHub and copy the files you want into the same relative
path. Then, for any template, tell Claude Code:

> Personalise the files I just copied to this repo: inspect the codebase, then
> replace the {{TOKENS}} and act on the guidance comments using real values —
> confirming any commands actually exist. Once each file is filled in, delete the
> guidance comments and show me a diff without committing.

It reads the in-file instructions, fills them in from your codebase, and strips
the guidance out.

## How the pieces work

Every file is one of three types. The type tells you how much work it needs
before it's yours:

| Type               | Meaning                                                                                                                                         |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Template**       | Structure + fill-in guidance. Carries `{{TOKENS}}` and `<!-- guidance -->` comments. Copy, then let Claude personalise and remove the guidance. |
| **Copy-and-tweak** | Working content with one marked block to edit — a formatter, a list of protected paths.                                                         |
| **Ready-to-use**   | Works verbatim. Copy and go.                                                                                                                    |

## What's inside

| Path                    | Type         | What it's about                                                                                                                               |
| ----------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `CLAUDE.md`             | Template     | Standing context loaded every session — stack, commands, conventions, and a "Never" list. Lives at your repo **root**, not inside `.claude/`. |
| `.claude/settings.json` | Template     | Permission allow/deny lists plus registration for the hooks.                                                                                  |
| `.claude/hooks/`        | Mixed        | Deterministic scripts that fire on tool events — guard edits to protected paths, format on save, act at end of turn.                          |
| `.claude/agents/`       | Ready-to-use | Focused reviewers that run in their own context and return strict pass/fail verdicts on your changes.                                         |
| `.claude/skills/`       | Ready-to-use | Reusable doc-writing workflows Claude applies when relevant, plus a template for authoring your own.                                          |

## Personalising a template

1. Copy the file to the same path in your repo.
2. Ask Claude Code to personalise it (see quick start). It fills `{{TOKENS}}` from
   your project and deletes the `<!-- guidance -->` comments.
3. Review and commit. For `CLAUDE.md`, keep it lean — say only what Claude can't
   infer from the code.

## Taking a hook? Take its registration too

A hook script does nothing on its own — Claude Code only runs it if it's
registered in `settings.json`. If you copy a hook, also copy its entry from the
`hooks` block in `.claude/settings.json`, or the hook will sit there inert.

## Repo layout

```
claude-code-toolkit/
├── CLAUDE.md            # project context template — copy to your repo root
└── .claude/
    ├── settings.json    # permissions + hook registration
    ├── hooks/           # scripts that run on tool events
    ├── agents/          # focused reviewers, run in their own context
    └── skills/          # reusable doc-writing workflows (+ a template)
```

## Scope

A personal toolkit I maintain for my own use, shared in case it's useful. Lift a
single file or the whole `.claude/` — it's yours once you copy it. It changes as
my workflow does.
