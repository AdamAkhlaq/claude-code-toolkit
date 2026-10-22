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
status: done
executed_by: single
branch: ticket/0001-T10
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

### Evidence 2026-10-22 17:56

Eval suite, run from a clone with `claude plugin eval . --trust-plugin --runs 1 --no-publish --scaffold --json` (Claude Code 2.1.304). Two findings on the way: the runner refuses `--allow-tools Bash` on this machine because of credential files it cannot sandbox, so every case was reshaped to need no Bash grant (the verify case gets its project from a `scaffold.sh` and the judge accepts an agent that cannot run commands but refuses to call the work done without the output); and `regex` graders are JavaScript regexes, so case-insensitivity is `flags: i`, not `(?i)`, which threw "Invalid regular expression". After both fixes, with the plugin and without it (the baseline arm):

```
case                          with   without   delta
grilling-numbered-round       1.00   0.00      +1.00   (grilling loaded; judge: numbered, recommended answers)
guide-routes-to-setup         1.00   0.50      +0.50   (names /toolkit:setup; wrote nothing)
verify-before-claiming-done   1.00   0.33      +0.67   (verify loaded; judge PASS; no bare done claim)
```

Cost of the full run: about 0.56 USD for the first three-case run, 0.16 USD for the one-case rerun. All three cases pass with the plugin, none pass without it.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
.................................................
----------------------------------------------------------------------
Ran 49 tests in 1.367s

OK
```

Before `evals/` existed, `tests.test_components.EvalSuiteRules` failed with `AssertionError: 0 not greater than or equal to 3 : evals/ must hold at least three cases`.

GitHub Action: see the next evidence block, recorded after the workflow's first run.

### Evidence 2026-10-22 17:57 (GitHub Action)

The workflow was triggered by a temporary draft pull request from this ticket branch into the integration branch (#5, closed unmerged once recorded). Run https://github.com/AdamAkhlaq/claude-code-toolkit/actions/runs/39818381023, conclusion `success`, job `validate` in 13 seconds on `ubuntu-latest` with no credentials in the environment:

```
Unit tests            Ran 49 tests in 1.638s / OK
Validate the plugin   claude plugin validate .   (exit 0, Claude Code 2.1.304 from npm)
```

So `claude plugin validate` needs no authentication, which the docs left unsaid. The job pins `@anthropic-ai/claude-code@2.1.304` on Node 22 and Python 3.12.

### Verifier 2026-10-22 18:02

Verdict: pass
Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `tests.test_components.EvalSuiteRules` is added on this branch; in a scratch clone it fails with `0 not greater than or equal to 3` when `evals/` is removed and with `unknown type 'judge'` when a grader type is changed. The case format matches the one T7 fixed.
3. proving test run: 0, `python3 -m unittest tests.test_components.EvalSuiteRules -v` reports `Ran 2 tests ... OK`
4. feedback command: 0, `Ran 49 tests in 1.515s / OK`
5. acceptance: 4 of 4 checked, none failed. Eval suite reproduced from a fresh clone under the scratchpad with `claude plugin eval . --trust-plugin --runs 1 --no-publish --scaffold --json` (exit 0, 0.46 USD): grilling-numbered-round 1.00 with / 0.00 without, guide-routes-to-setup 1.00 / 0.50, verify-before-claiming-done 1.00 / 0.33. `gh run view 39818381023 --json conclusion` reports `success` for workflow `validate` on event `pull_request` from this branch; `validate.yml` triggers on `pull_request` and `push` to `main`. README Development section documents the eval command, that CI runs unit tests plus `claude plugin validate .`, and that `evals/results/` is ignored (confirmed in `.gitignore`); `CLAUDE.md` Commands lists the eval command.
6. scope: ok
7. tests intact: ok, the only test change is the added `EvalSuiteRules` class; no deleted assertions, skips or loosened values. No em dash in the diff; prettier clean on all changed Markdown.
