---
id: T7
title: Add the eval-case skill and its template
blocked_by: [T6]
files:
  [
    skills/eval-case/SKILL.md,
    templates/eval-case.md,
    README.md,
    PHILOSOPHY.md,
    GLOSSARY.md,
    skills/guide/SKILL.md,
    .gitignore,
  ]
proves: "tests/test_components.py passes with the README skill table listing eval-case as shipped in 0.4.0"
status: done
executed_by: single
branch: ticket/0001-T7
---

## Context

Spec component table, row `eval-case`: "A prompt plus checks under `evals/` from a past task or incident". Philosophy "Mistakes become memory": a postmortem produces an eval case that catches the same class of failure next time. The case format is the one `claude plugin eval` runs (Claude Code 2.1.269 or later): a directory `evals/<case>/` holding `prompt.md` (frontmatter `name`, `description`, `tags`, `max_turns`, `allowed_tools`; body is the prompt) and `graders/<name>.md` files whose frontmatter `type` is one of `regex`, `tool_used`, `tool_order`, `file_exists`, `llm` or `baseline`, with the rubric or pattern in the body. `evals/results/` is written by runs and is ignored. In a plugin the suite runs with `claude plugin eval .`; in a consuming repo the cases are run by hand with `claude -p` against the graders until a runner exists, which the spec puts out of scope. A trigger test for a model-invoked skill is a `tool_used` grader on the `Skill` tool with `arm: both`, and a negative one with `min: 0, max: 0`.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/eval-case/SKILL.md` is user-invoked and takes the task, incident or behaviour to pin as its argument.
- `templates/eval-case.md` shows a complete `prompt.md` and one grader of each kind the skill recommends.
- `.gitignore` ignores `evals/results/`.
- PHILOSOPHY "Mistakes become memory" links the skill. `GLOSSARY.md` defines eval case and grader. The guide routes "make sure this never happens again" to it.

## Evidence

### Evidence 2026-10-22 17:47

The T6 verifier noted that prettier rewrites unquoted `{{X}}` placeholders inside the template's fenced YAML to `{ { X } }`; the template now uses `<PLACEHOLDER>`, which prettier leaves alone.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.331s

OK
```

Before `skills/eval-case/SKILL.md` existed, with the README row at 0.4.0, `tests.test_components` failed with `AssertionError: 'eval-case' not found in [...]`.

### Verifier 2026-10-22 17:48

Verdict: pass

Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `tests/test_components.py::SkillRules::test_invocation_matches_readme` asserts `skills/<name>/SKILL.md` exists for every README skill row whose version cell lacks "planned"; this branch moves `eval-case` from `planned 0.4.0` to `0.4.0`, so the test fails without the skill. The test predates the branch and is unchanged, which is the seam the ticket names.
3. proving test run: 0, `python3 -m unittest tests.test_components`: Ran 10 tests in 0.014s, OK
4. feedback command: 0, `python3 -m unittest discover -s tests`: Ran 46 tests in 1.299s, OK
5. acceptance: 5 of 5 checked, none failed. Proving test passes (check 3). `skills/eval-case/SKILL.md` carries `disable-model-invocation: true`, an `argument-hint` of task, incident or behaviour, and binds `$ARGUMENTS` as the subject. `templates/eval-case.md` shows a full `prompt.md` (name, description, tags, max_turns, allowed_tools, body) and one grader each of `regex`, `tool_used` (positive and negative), `tool_order`, `file_exists` and `llm`, the five kinds the skill recommends. `.gitignore` ends with `evals/results/`. PHILOSOPHY "Mistakes become memory" links `./skills/eval-case/SKILL.md`; GLOSSARY defines "Eval case" and "Grader"; the guide table routes "Make sure this never happens again" to `/toolkit:eval-case`. Also checked: no em dash in any changed file, `prettier --check` clean on all changed Markdown, `claude plugin validate .` passes with only the pre-existing CLAUDE.md warning.
6. scope: ok. Changed on the branch: `.gitignore`, `GLOSSARY.md`, `PHILOSOPHY.md`, `README.md`, `skills/eval-case/SKILL.md`, `skills/guide/SKILL.md`, `templates/eval-case.md` and the ticket file; all in `files`.
7. tests intact: ok. `git diff change/0001-phase-3...HEAD -- tests/` is empty.
