---
id: 0001
slug: plugin-overhaul
status: accepted
originator: Adam Akhlaq
accepted_by: Adam Akhlaq
created: 2026-10-21
---

# Intent: an opinionated Claude Code plugin for engineering work

## Origin

From the conversation that produced this document, in the originator's words:

> I want a more opinionated AI engineering process, as a plugin.

> I want it based on Claude Code best practices from Anthropic. I found the AI-native SDLC playbook.

> I prefer the ticket graph flow, but want to keep the best practices from Anthropic's AI SDLC.

> I would like to define some rules and guidelines that my engineering philosophy should enforce when using this flow.

## Problem

Working with a coding agent without a defined process produces the same failures every time: the agent builds the wrong thing because the problem was never pinned down, the code does not work because there was no feedback loop, decisions are lost because nothing was written down, and the same mistakes repeat because nothing was learned. Fixing this by hand in each project means the fix drifts between projects and never improves in one place.

## Proposed outcome

A single Claude Code plugin, `toolkit`, served from this repo's own marketplace, `adamakhlaq`, that encodes one engineering workflow and installs the same way in every project. The workflow runs the stages of Anthropic's [AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook) as human-gated artifacts, and executes the build stage as a ticket graph with pluggable executors. Every skill, agent and hook in the plugin serves a principle in `PHILOSOPHY.md`.

## Affected users and systems

- The originator, who will install the plugin at user scope and use it in every project.
- Anyone who adds the marketplace and installs the plugin.
- This repo, which is the first consumer of its own workflow.
- Target repos, which gain a `.claude/toolkit.json`, a `docs/changes/` tree, `GLOSSARY.md` and `REVIEW.md` through the `setup` skill.

## Constraints

- Claude Code only. No other harness is supported.
- A plugin cannot ship permissions or a `CLAUDE.md`. Per-project context stays per project.
- Manual versioning: bump `plugin.json` by hand, maintain `CHANGELOG.md`, tag releases.
- No em dashes in prose. Markdown prose is not hard-wrapped. Code width is the formatter's decision.
- Nothing is committed without the originator's explicit approval.

## Open questions

- Decision, open: does `claude plugin validate --strict` reject a `CLAUDE.md` at the plugin root? Resolve in phase 0 by running it. If it does, run validate without strict and treat that one warning as expected.
- Decision, open: should "composition over configuration" get a validation script, or stay enforced by review? Defer until the skill set is stable.
- Decision, open: GitHub issues as a ticket mirror. Deferred to after phase 3. Local ticket files are the only store until then.
- Fact, resolved: plugins can bundle skills, agents, hooks, commands, MCP and LSP servers, and `bin/` executables. Confirmed against the plugin docs on 2026-10-21.
- Fact, resolved: auto-update is off by default for marketplaces other than the official one. Users run `claude plugin update toolkit@adamakhlaq`.

## Amendment 2026-10-21: validate and the root CLAUDE.md

Resolved: `claude plugin validate .` passes with one warning, that a `CLAUDE.md` at the plugin root is not loaded into consumers' sessions. `--strict` fails on it. The maintainer `CLAUDE.md` stays, and validation runs without `--strict`.
