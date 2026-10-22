---
id: "{{ID}}"
slug: "{{SLUG}}"
status: proposed
execution: single
concurrency: 1
created: "{{DATE}}"
---

# Plan: {{TITLE}}

## Approach

<!-- Required. How the outcome in spec.md will be reached, in a few paragraphs. Name the modules touched and the order of work. -->

## Execution

<!-- Required. Which executor runs the tickets and why: `single` (one agent, in this session), `subagents` (parallel agents in this session, file-disjoint tickets), `team` (an agent team, tickets that coordinate or a large graph), or `headless` (unattended runs, nobody at the keyboard). State the reason in a sentence or two. Set `execution` and `concurrency` in the frontmatter to match. -->

## Seams

<!-- Required. The public boundaries tests are written at, one per line, each with what it catches and what it misses. No test is written at a seam not listed here. -->

## Interrogation

<!-- Required. Answer each in a sentence or two: What could break? Which step is riskiest, and what contains it? Could someone who never saw the conversation implement this from the plan and the tickets alone? -->

## Rejected alternatives

<!-- Required, may be "None considered" for a trivial change. Each alternative with the reason it lost. A one-way-door decision here also gets an ADR under docs/adr/. -->
