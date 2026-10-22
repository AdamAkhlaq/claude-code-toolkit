---
name: eval-case
description: Turn a past task, an incident, or a behaviour that must hold into an eval case under evals/: a prompt that would lead an agent toward the mistake, and graders that catch it. Run with the task, incident or behaviour to pin as the argument.
disable-model-invocation: true
argument-hint: "<task, incident, or behaviour to pin>"
---

# Eval case

A lesson that lives only in a transcript is gone when the session ends. An eval case keeps it: a prompt that recreates the situation, and checks that say whether the agent did the right thing. Postmortems produce one for each class of failure, policy skills get two to prove they trigger, and any task that went wrong once can get one so it does not go wrong twice.

The subject: $ARGUMENTS

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`.

## The format

The case format is the one `claude plugin eval` runs (Claude Code 2.1.269 or later), so a case written here runs unchanged in any plugin, and reads as a checklist anywhere else.

```
evals/<case-name>/
  prompt.md            frontmatter: name, description, tags, max_turns, allowed_tools; body: the prompt
  graders/<check>.md   frontmatter: type and its options; body: the rubric or pattern
```

Grader types: `regex` (a pattern against the last message, the trace, or a produced file), `tool_used` (a tool was or was not called, with an input match), `tool_order` (one tool before another), `file_exists` (a file the run created), `llm` (a judge reads the output against a PASS/FAIL rubric). `templates/eval-case.md` shows one of each.

In this repo, if it is a plugin, the suite runs with `claude plugin eval . --runs 1 --no-publish`. In a repo that is not a plugin there is no runner yet: run the prompt with `claude -p` and apply the graders by hand, and say so in the case's description.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. `evals/` is created on first use, with `evals/results/` ignored in `.gitignore`.

2. **Find the class, not the instance.** From the task or incident, state in one sentence what kind of mistake is being pinned: "skipped reproduction and fixed the wrong function", "logged a field the policy forbids", "claimed done without running the tests". The case tests the class. A case that only replays the exact incident catches nothing else.

3. **Write the prompt.** A realistic request, in the words a user would use, that would lead an agent toward the mistake if it did not know better. Include just enough context, inline or in a scaffold, that the mistake is possible. Do not hint at the right answer. Name the case after the behaviour, `<verb>-<object>`, and give it a `description` that says what it catches.

4. **Write the graders.** At least one deterministic grader (`regex`, `tool_used`, `tool_order`, `file_exists`) so the case cannot drift with the judge's mood, and one `llm` grader only when the behaviour cannot be pinned any other way. For a skill trigger test, `tool_used` on `Skill` with `input_match` on the skill's name and `arm: both`; for a must-not-trigger case, the same with `min: 0` and `max: 0`. Each grader's body says what PASS looks like and what FAIL looks like, in one line each.

5. **Run it once** if a runner is available, with `--runs 1 --no-publish`, and quote the result. A case that passes without the thing it tests (a plugin, a skill, a `CLAUDE.md` line) is not catching anything: check the baseline column and tighten the graders until the difference is real.

6. **Link it.** From the incident record's Follow-ups, the policy skill, or the change's intent, whichever produced it.

7. **Commit, with approval.** Stage `evals/<case-name>/` and `.gitignore` if changed. Message `test(evals): <case-name>`. Commit only when the user says go. Never push.

## Rules

- One class of mistake per case. Two mistakes are two cases.
- Deterministic first. A judge is a last resort and is never the only grader.
- Prompts are realistic and unhinted. A prompt that says "remember to run the tests" tests nothing.
