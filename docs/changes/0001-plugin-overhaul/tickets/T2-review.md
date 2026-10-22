---
id: T2
title: Add the reviewer agent and the review skill over REVIEW.md
blocked_by: [T1]
files:
  [
    agents/reviewer.md,
    skills/review/SKILL.md,
    templates/REVIEW.md,
    README.md,
    PHILOSOPHY.md,
    GLOSSARY.md,
    skills/guide/SKILL.md,
    tests/test_components.py,
  ]
proves: "tests/test_components.py passes with the README listing review as shipped in 0.3.0 and the reviewer agent carrying a read-only tool allowlist"
status: done
executed_by: single
branch: ticket/0001-T2
---

## Context

Spec: `review` runs "three `REVIEW.md` passes, findings in `review.md` and on the PR"; `reviewer` "executes one `REVIEW.md` pass". Philosophy "Verification is independent" and "Mistakes become memory": each pass runs in its own reviewer context, findings are Important or Nit (glossary), nits are capped at five, every Important finding is fixed or waived by the code owner before merge, and a flag raised in two reviews becomes a `CLAUDE.md` line through the `claude-md` discipline. The skill reads the repo's `REVIEW.md`, falling back to the template when absent, writes `review.md` in the change folder, and posts findings to the pull request when one exists so that `pr-sweep` can resolve them.

Seam: `tests/test_components.py`. Extend it so the reviewer agent, like the researcher, carries no editing tools.

## Acceptance

- The proving test passes.
- `agents/reviewer.md` has a tool allowlist without Edit, Write or Agent, and the test asserts it.
- `skills/review/SKILL.md` is user-invoked, runs one reviewer per pass in `REVIEW.md`, merges findings into `docs/changes/<change>/review.md`, and records waivers with the waiver's owner.
- `templates/REVIEW.md` states the finding format the reviewer returns.
- PHILOSOPHY "Verification is independent" links `review` and `reviewer`; the guide routes a finished change to `review`.

## Evidence

### Evidence 2026-10-22 17:27

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.296s

OK
```

Before `agents/reviewer.md` and `skills/review/SKILL.md` existed, with the README row at 0.3.0 and the read-only assertion extended to the reviewer, `tests.test_components` failed with `KeyError: 'reviewer'` and `AssertionError: 'review' not found in [...]`.

### Verifier 2026-10-22 17:28

Verdict: pass

Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `tests/test_components.py` is the seam the ticket names; the branch extends `test_readers_cannot_write` to the reviewer (KeyError without `agents/reviewer.md`, AssertionError if it carried Edit, Write, NotebookEdit or Agent) and `test_invocation_matches_readme` requires `skills/review/SKILL.md` once the README row reads 0.3.0.
3. proving test run: 0, `python3 -m unittest tests.test_components` printed `Ran 10 tests in 0.010s` then `OK`
4. feedback command: 0, `python3 -m unittest discover -s tests` printed `Ran 46 tests in 1.296s` then `OK`
5. acceptance: 5 of 5 checked, none failed. Proving test run above. `agents/reviewer.md` tools are `Read, Grep, Glob, Bash` and the test loops over `researcher` and `reviewer`. `skills/review/SKILL.md` carries `disable-model-invocation: true`, step 3 starts one `toolkit:reviewer` per pass under the Passes heading with nothing but the pass and diff, step 6 writes `docs/changes/<change>/review.md` and its Waivers section names the finding, the reason and the code owner. `templates/REVIEW.md` gained a Finding format section stating the `[Important|Nit] <path>:<line> ... Fix: ...` line. PHILOSOPHY line 17 links `review` and `reviewer`; the guide's "Every ticket is done" row now routes to `/toolkit:review <change>`.
6. scope: ok. Changed: GLOSSARY.md, PHILOSOPHY.md, README.md, agents/reviewer.md, skills/guide/SKILL.md, skills/review/SKILL.md, templates/REVIEW.md, tests/test_components.py, plus the ticket file.
7. tests intact: ok. The only test diff widens one assertion loop from `researcher` to `researcher` and `reviewer`; no assertion removed, no skip or expected-failure marker, no loosened value.
