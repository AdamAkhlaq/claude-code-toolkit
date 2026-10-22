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
status: done
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

### Evidence 2026-10-22 17:49

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.368s

OK
```

Before `skills/policy-skill/SKILL.md` existed, with the README row at 0.4.0, `tests.test_components` failed with `AssertionError: 'policy-skill' not found in [...]`.

### Verifier 2026-10-22 17:50

Verdict: pass
Checks:

1. ticket integrity: ok. `id`, `title`, `blocked_by`, `files`, `proves`, `status: in-progress`, `executed_by`, `branch` all present; Evidence quotes the feedback command run with exit 0 and output.
2. proving test present and meaningful: ok. `tests/test_components.py` existed on the integration branch and is unchanged here (`git diff change/0001-phase-3...HEAD -- tests/` is empty). Flipping the README row from `planned 0.4.0` to `0.4.0` makes `test_invocation_matches_readme` require `skills/policy-skill/SKILL.md` and its `disable-model-invocation: true`. In a scratch extract of the branch without `skills/policy-skill/`, the module fails with `AssertionError: 'policy-skill' not found in [...] : README lists policy-skill as shipped but skills/policy-skill/SKILL.md is missing`.
3. proving test run: 0, `python3 -m unittest tests.test_components -v` ran 10 tests, `OK`.
4. feedback command: 0, `python3 -m unittest discover -s tests` ran 46 tests in 1.329s, `OK`.
5. acceptance: 4 of 4 checked, none failed. Proving test passes (check 3). `skills/policy-skill/SKILL.md` carries `disable-model-invocation: true`, an `argument-hint` of the policy in one or two sentences, and binds `$ARGUMENTS` as the policy. `templates/policy-skill.md` is a full SKILL.md: frontmatter with `name` and a trigger-rich `description` (rule, triggers, near misses) and no `disable-model-invocation`, body sections The rule, Why, How to apply it, When it conflicts, Owner, each with a placeholder comment. `skills/guide/SKILL.md` routes "The project must always do X": a rule every change should follow to `/toolkit:policy-skill`. Also checked: GLOSSARY "Policy skill" now names the writer, the reader and the trigger tests; no em dash in any changed file; `prettier --check` clean on all changed Markdown; `claude plugin validate .` passes with only the pre-existing CLAUDE.md warning; the skill references only `toolkit:researcher`, `toolkit:grilling`, `toolkit:glossary` and the `/toolkit:eval-case` hand-off, and says never push.
6. scope: ok. Changed on the branch: `GLOSSARY.md`, `README.md`, `skills/guide/SKILL.md`, `skills/policy-skill/SKILL.md`, `templates/policy-skill.md` and the ticket file; all in `files`. `toolkit-graph validate` reports `0001-plugin-overhaul: ok (11 tickets)`.
7. tests intact: ok. No test file changed on the branch.
