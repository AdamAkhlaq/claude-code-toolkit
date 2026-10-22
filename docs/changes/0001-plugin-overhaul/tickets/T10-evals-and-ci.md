---
id: T10
title: Add the plugin's own eval suite and a GitHub Action
blocked_by: [T9]
files:
  [
    evals/,
    .github/workflows/validate.yml,
    README.md,
    CLAUDE.md,
    tests/test_components.py,
  ]
proves: "tests/test_components.py checks that every case under evals/ has a prompt.md with a name and at least one grader with a known type, and the suite has at least three cases that pass that check; the workflow runs the unit tests and plugin validation on every pull request"
status: todo
---

## Context

Plan phase 3 step 3: "`evals/` suite for the plugin and a GitHub Action running validate". Cases in the format T7 describes, exercising skills on real tasks: at least one for `guide` (a repo without `.claude/toolkit.json` is routed to `/toolkit:setup`, a `regex` grader on the last message), one trigger test for a model-invoked skill (`verify` loads when the prompt asks whether work is done, `tool_used` on `Skill` with `arm: both`), and one for `grilling` (questions arrive numbered with a recommended answer, an `llm` grader). Run the suite once locally with `--runs 1 --no-publish` and quote the summary table as evidence; the cases must pass with the plugin. The Action installs a pinned `@anthropic-ai/claude-code` on Node 22, runs `python3 -m unittest discover -s tests`, and runs `claude plugin validate .` without `--strict`, because the root `CLAUDE.md` warning is expected. Whether validate needs credentials is undocumented; the first run of the Action on the pull request answers it, and the evidence records the answer. The eval suite is not run in CI; it costs money and the plan limits CI to validate.

Seam: `tests/test_components.py` for the suite's shape; the Action's first run for CI.

## Acceptance

- The proving test passes.
- `claude plugin eval . --runs 1 --no-publish` passes every case with the plugin; the summary is quoted in Evidence.
- `.github/workflows/validate.yml` runs on pull requests and pushes to main and is green on this change's pull request.
- README documents how to run the evals and what CI checks. `CLAUDE.md` lists the eval command.

## Evidence
