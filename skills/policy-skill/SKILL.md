---
name: policy-skill
description: Encode one rule the project must apply consistently (a security standard, a compliance requirement, a data-handling policy, an API convention) as a model-invoked skill in the repo's .claude/skills/, with trigger tests that show it loads when it should and stays quiet when it should not. Run with the policy statement as the argument.
disable-model-invocation: true
argument-hint: "<the policy, in one or two sentences>"
---

# Policy skill

A policy is a rule that must hold across every change, not just the one being built. Writing it into a skill means every session that touches the subject reads it, the `spec` skill checks new work against it, and reviewers can cite it. One policy per skill. A different policy is a different skill, never a setting on this one.

The policy: $ARGUMENTS

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. Read every existing skill under `.claude/skills/` so the new one does not overlap or contradict one. If a skill for this policy already exists, the user wants an amendment: edit it, do not add a second.

2. **Pin the rule.** Restate the policy as one sentence in the imperative that a reviewer could check a diff against. If the statement you were given contains two rules, say so and ask which one this skill encodes; the other gets its own run. Use the `toolkit:researcher` agent to find where the project already applies or violates it, so the skill can point at real examples.

3. **Grill the edges.** The cases where the rule is unclear are decisions: exceptions, legacy paths, who may waive it. Run the `toolkit:grilling` skill, one round. Record the answers in the skill's Conflicts section.

4. **Write the skill** at `.claude/skills/<name>/SKILL.md` from `templates/policy-skill.md`. The name is the policy's subject, two or three words. The description is the trigger: the subjects, files, operations and words that should make Claude load it, and what it is not for. The body has the rule, how to apply it with examples from this codebase, what to do on conflict, and who owns it. Keep it under sixty lines. Apply the `toolkit:glossary` discipline to any term it introduces.

5. **Write the trigger tests.** Two eval cases in the format `templates/eval-case.md` shows, under `evals/policy-<name>-triggers/` and `evals/policy-<name>-stays-quiet/`: a prompt that should load the skill, with a `tool_used` grader on `Skill` matching the skill's name and `arm: both`; and a neighbouring prompt that should not, with the same grader at `min: 0` and `max: 0`. `/toolkit:eval-case` is the same discipline for any other behaviour.

6. **Wire it in.** Add one line to `REVIEW.md` under the compliance pass naming the policy skill, so reviewers check against it. If the rule should be enforced rather than advised, say which hook or CI check would do that and that this skill is the advisory half; hooks are added through a change, not here.

7. **Present, then commit with approval.** Show the skill, the two eval cases and the `REVIEW.md` line. Message `docs(policy): <name>`. Commit only when the user says go. Never push.

## Rules

- One policy per skill. Two rules in one file means two files.
- The rule is stated so a diff can be checked against it. "Be careful with PII" is not a policy; "Never log a field listed in `docs/pii-fields.md`" is.
- Advisory only. Anything that must always hold also needs a hook or a CI check, and the skill says so.
