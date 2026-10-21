---
id: "{{TICKET_ID}}"
title: "{{TITLE}}"
blocked_by: []
files: []
proves: ""
status: todo
---

<!-- Frontmatter rules, checked by `toolkit-graph validate`:
     id         T1, T2, ... and the file is named <id>-<slug>.md
     blocked_by ids this ticket waits for; [] when it can start immediately
     files      every path this ticket will touch; tickets with no ordering between them must not share a file
     proves     the one behaviour this ticket makes true, phrased as the test that will show it
     status     todo | in-progress | done | reopened
     serial     optional, true when a human must watch this ticket run (one-way door)
     executor   optional, overrides plan.md's execution mode for this ticket
     On completion the executor adds: executed_by, branch, and an Evidence section. -->

## Context

<!-- What a fresh agent needs to work this ticket without the conversation: the relevant spec.md requirement numbers, the seam from plan.md, and any gotcha already known. -->

## Acceptance

<!-- Bullet list. Each line is checkable. The first is always the `proves` test passing. -->

## Evidence

<!-- Left empty until done. The executor pastes the feedback command's output here, then the verifier records its verdict beneath it. -->
