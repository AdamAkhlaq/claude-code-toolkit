---
id: T6
title: Add the postmortem skill and the incident template
blocked_by: [T5]
files:
  [
    skills/postmortem/SKILL.md,
    templates/incident.md,
    README.md,
    PHILOSOPHY.md,
    GLOSSARY.md,
    skills/guide/SKILL.md,
  ]
proves: "tests/test_components.py passes with the README skill table listing postmortem as shipped in 0.4.0"
status: in-progress
executed_by: single
branch: ticket/0001-T6
---

## Context

Spec component table, row `postmortem`: "Incident record in `docs/incidents/`, follow-up intent, eval case". Philosophy "Mistakes become memory" and "The loop closes". The skill writes `docs/incidents/YYYY-MM-DD-<slug>.md` from `templates/incident.md` (timeline, impact, root cause, contributing factors, what went well, follow-ups), blameless in tone, with facts cited from logs, commits and the conversation. Each follow-up that is work becomes an intent through the same steps `intent` uses, and the class of failure becomes an eval case through the `eval-case` discipline once that skill exists (T7); until then the skill records the eval case as a follow-up line. Grilling is used for the timeline gaps only a human can fill.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/postmortem/SKILL.md` is user-invoked and takes the incident description or link as its argument.
- `templates/incident.md` has frontmatter (`date`, `slug`, `severity`, `status`, `owner`) and the sections above as comments.
- PHILOSOPHY "Mistakes become memory" and "The loop closes" link the skill. `GLOSSARY.md` defines incident and follow-up. The guide routes an incident to it.

## Evidence
