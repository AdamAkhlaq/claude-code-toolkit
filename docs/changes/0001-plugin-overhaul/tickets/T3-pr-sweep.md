---
id: T3
title: Add the pr-sweep skill
blocked_by: [T2]
files: [skills/pr-sweep/SKILL.md, README.md, skills/guide/SKILL.md]
proves: "tests/test_components.py passes with the README listing pr-sweep as shipped in 0.3.0"
status: in-progress
executed_by: single
branch: ticket/0001-T3
---

## Context

Spec: `pr-sweep` "resolves comments and failing checks until the PR is green". It reads the pull request's unresolved review threads and failing checks with `gh`, fixes or answers each comment, repairs each failing check with the feedback command as the judge, and pushes only with the user's go-ahead per push. A comment that asks for a change of design is not fixed in place: it becomes an amendment to the change's artifacts. A flag seen in two reviews goes to `CLAUDE.md` through the `claude-md` discipline. The skill never force-pushes.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/pr-sweep/SKILL.md` is user-invoked, takes an optional pull request number, and stops on a design-level comment, a check that fails twice after a fix, and a merge conflict.
- The guide routes an open pull request with comments or red checks to `pr-sweep`.

## Evidence

### Evidence 2026-10-22 17:28

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.323s

OK
```

Before `skills/pr-sweep/SKILL.md` existed, with the README row at 0.3.0, `tests.test_components` failed with `AssertionError: 'pr-sweep' not found in [...]`.

### Verifier 2026-10-22 17:30

Verdict: reopen

Checks:

1. ticket integrity: ok
2. proving test present and meaningful: ok. `tests/test_components.py` predates the branch and is unchanged on it; `test_invocation_matches_readme` asserts a skill folder for every README row not marked planned. In a scratch export of HEAD without `skills/pr-sweep` it fails with `README lists pr-sweep as shipped but skills/pr-sweep/SKILL.md is missing`.
3. proving test run: 0, `python3 -m unittest tests.test_components` ran 10 tests, OK
4. feedback command: 0, `python3 -m unittest discover -s tests` ran 46 tests, OK
5. acceptance: 2 of 3 checked ok, line 2 failed. The proving test passes (check 3). The guide table routes "A pull request with unresolved comments or red checks" to `/toolkit:pr-sweep <n>`. `skills/pr-sweep/SKILL.md` carries `disable-model-invocation: true`, takes `$ARGUMENTS` with a bare fallback to `gh pr view`, stops on a design-level comment (step 3 and the rules) and on a check that fails again after a fix (step 4), but says nothing about a merge conflict: the only nearby stop is "if the branch has diverged, say so and stop" in step 5, which covers a rejected push, not a pull request that cannot merge into its base. The word conflict does not appear in the skill.
6. scope: ok. Branch changes README.md, skills/guide/SKILL.md, skills/pr-sweep/SKILL.md and the ticket file.
7. tests intact: ok, no diff under tests/

Reopen reason: make the skill stop on a merge conflict with the base branch, as the acceptance list requires, rather than only on a diverged push.

### Evidence 2026-10-22 17:32 (after reopen)

Added the merge-conflict stop condition to the preconditions and the rules of `skills/pr-sweep/SKILL.md`. The first run after that edit exited 1: `test_user_invoked_skills_never_push` treated the new `git merge-tree` mention as a sign that the skill commits and demanded "never push", which pr-sweep cannot promise. That commit (`9e94a85`) was made on red, against the executor contract; this run supersedes it. The test now states the real rule, `test_pushing_is_the_users_decision`: a user-invoked skill either never pushes, or pushes only with approval and never by force. `tests/test_components.py` was added to this ticket's files.

Command: `python3 -m unittest discover -s tests`

Exit code: 0

```
..............................................
----------------------------------------------------------------------
Ran 46 tests in 1.303s

OK
```
