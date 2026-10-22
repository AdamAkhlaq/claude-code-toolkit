---
name: guide
description: Tells you which toolkit skill fits your situation and where the current change stands. Describe what you want to do, or run it bare to see the state of the repo's changes.
disable-model-invocation: true
argument-hint: "[what you want to do]"
---

# Guide

Route the user to the right skill. Read the repo's state first, then answer in a few lines. Write nothing.

The user said: $ARGUMENTS

## Read the state

1. Does `.claude/toolkit.json` exist? If not, every answer is `/toolkit:setup` first.
2. List `docs/changes/*/`. For each change read the frontmatter `status` of `intent.md`, `spec.md` and `plan.md` where they exist, and run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" status <change>` when a `tickets/` folder exists. A change is live when its intent is `accepted` or `building`.
3. Note `git branch --show-current` and whether the tree is clean.

## Route

Match the user's words, or the state when they said nothing, to the first row that fits:

| Situation                                                                  | Skill                                                             | Produces                                                                                   |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| No `.claude/toolkit.json`                                                  | `/toolkit:setup`                                                  | the config, the docs tree, `GLOSSARY.md`, `REVIEW.md`                                      |
| An idea, a request, a pasted ticket, an alert, "something is wrong with X" | `/toolkit:intent`                                                 | a committed `intent.md`: origin, problem, outcome, open questions                          |
| A bug with steps to reproduce, or a failing test                           | `/toolkit:fix-bug`                                                | a reproduction, a locked failing test, the fix                                             |
| A live change whose intent is accepted and has no `spec.md`                | `/toolkit:spec <change>`                                          | `spec.md`: testable outcome, scope, numbered requirements, policy conflicts, a go or no-go |
| A spec with `go_no_go: go` and no `plan.md`                                | `/toolkit:plan <change>`                                          | `plan.md`: approach, seams, execution decision, interrogation, rejected alternatives       |
| A plan with `status: accepted` and no tickets                              | `/toolkit:tickets <change>`                                       | `tickets/*.md`: a validated graph of tracer bullets                                        |
| Tickets exist and the frontier is not empty                                | `/toolkit:implement <change>`                                     | verified ticket branches merged into the integration branch                                |
| Every ticket is done                                                       | open the pull request; `/toolkit:review` arrives in 0.3.0         | a green pull request                                                                       |
| The user wants to know what a term means                                   | point at `GLOSSARY.md`, no skill needed                           |                                                                                            |
| The user wants a rule remembered                                           | say it will go in `CLAUDE.md`; the `claude-md` discipline applies | a line in `CLAUDE.md`                                                                      |

When a change is mid-flight but an artifact has gone stale, say which artifact needs an amendment and which skill writes it. When more than one change is live, list them and ask which one.

## Answer

At most eight lines: the state in one or two lines, the skill to run with its argument, and what that skill will produce. If the user's words do not fit any row, say what the workflow does not cover and what to do by hand. Do not describe the whole workflow unless asked; the README does that.
