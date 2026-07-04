---
name: {{skill-name}}
# ^ kebab-case, matches this folder's name. This is how the skill is referenced.
description: >-
  {{ONE OR TWO SENTENCES describing WHAT this skill does and — critically — WHEN
  Claude should reach for it. The description is the trigger: Claude reads it to
  decide whether to apply the skill, so make it sharp. Name the concrete
  situations, verbs, and phrases a user would use ("when the user asks to X",
  "when mentioning Y"). Say when NOT to use it and point to the better skill.
  A vague description means the skill fires at the wrong time or never fires.}}
when_to_use: >-
  {{OPTIONAL sharper trigger — the specific cues that should activate this skill,
  e.g. "user says 'write a postmortem' or an incident just resolved". Delete this
  line if the description already carries the trigger clearly.}}
---

<!--
  ARCHETYPE: TEMPLATE — a skeleton for authoring your OWN skill.

  Build a skill the THIRD time you hand-do a task, not speculatively. If you've
  only done it once or twice, you don't yet know the real steps — write it down
  as notes, and promote it to a skill once the pattern is stable.

  Fill in the frontmatter and the Steps below, delete every guidance comment and
  this banner, then save. Keep the body tight: numbered, imperative steps that
  encode what you actually do — not background theory.
-->

# {{Skill Title}}

{{One line on what following this skill produces or accomplishes.}}

## Steps

<!-- Numbered, imperative, in order. Each step is an action Claude takes. Keep
     them concrete enough to follow without you in the room. -->

1. {{First step — what to gather / read / confirm before starting.}}
2. {{Second step — the core action.}}
3. {{Third step — check the result / hand it back.}}

## Notes

<!-- OPTIONAL. Edge cases, gotchas, or "don't do X" warnings that don't fit as a
     step. Delete this section if you have none. -->
- {{gotcha or constraint}}

<!--
  BEFORE SAVING: delete all guidance comments and the banner, and replace every
  {{TOKEN}}. Nothing meta should remain in the finished skill.
-->
