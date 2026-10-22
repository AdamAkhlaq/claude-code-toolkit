---
id: T8
title: Add the policy-skill skill
blocked_by: [T7]
files:
  [
    skills/policy-skill/SKILL.md,
    templates/policy-skill.md,
    README.md,
    GLOSSARY.md,
    skills/guide/SKILL.md,
  ]
proves: "tests/test_components.py passes with the README skill table listing policy-skill as shipped in 0.4.0"
status: in-progress
executed_by: single
branch: ticket/0001-T8
---

## Context

Spec component table, row `policy-skill`: "A new skill encoding one policy, with trigger tests". Glossary: a policy skill encodes one rule the project must apply consistently, such as a security or compliance standard. The skill writes a model-invoked skill into the consuming repo's `.claude/skills/<name>/SKILL.md` from `templates/policy-skill.md`: a trigger-rich description, the rule, how to apply it, and what to do on conflict. The `spec` skill reads these when flagging policy conflicts. Trigger tests are eval cases (T7) that give a prompt which should load the skill and one which should not, asserting on the transcript. Composition over configuration: one policy per skill, no settings.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/policy-skill/SKILL.md` is user-invoked and takes the policy statement as its argument.
- `templates/policy-skill.md` is a complete SKILL.md with placeholders and no `disable-model-invocation`.
- The guide routes "make the project always do X" to it.

## Evidence
