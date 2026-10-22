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

### Evidence 2026-10-22 17:31 (after reopen)

Added the merge-conflict stop condition to the preconditions and the rules of `skills/pr-sweep/SKILL.md`.

Command: `python3 -m unittest discover -s tests`

Exit code: 1

```
AssertionError: Regex didn't match: '[Nn]ever push' not found in "\n# PR sweep\n\nA pull request is done when every review thread is resolved and every check is green. This skill works through both until the list is empty or something needs a human.\n\nThe pull request: $ARGUMENTS\n\nIf the argument is empty, use `gh pr view --json number` on the current branch.\n\n## Steps\n\n1. **Preconditions.** `.claude/toolkit.json` exists with a `feedbackCommand`. `gh auth status` succeeds. The pull request's head branch is checked out and the tree is clean. Note the change id from the branch name or the commit trailers. Check `gh pr view <n> --json mergeable`: a merge conflict with the base branch is a stop condition. Show the conflicting files from `git merge-tree` and hand the resolution to the user; resolving someone's conflict silently rewrites their intent.\n\n2. **Read the whole list first.** Collect, in one pass:\n   - Unresolved review threads: `gh api graphql` on `pullRequest.reviewThreads` with `isResolved`, `path`, `line`, and each comment's author and body.\n   - Failing or pending checks: `gh pr checks <n>` and, for each failure, the log through `gh run view <id> --log-failed`.\n   - The review record, `docs/changes/<change>/review.md`, when it exists, so the sweep closes its boxes too.\n     Show the user the list, grouped as comments and checks, before changing anything. Number the items; the numbers are how you refer to them from here.\n\n3. **Sort each item.** Every item is one of:\n   - **Fix.** A concrete request or a real failure. Make the change.\n   - **Answer.** A question, or a request that is wrong given the spec or the plan. Reply with the reason, citing the artifact, and resolve the thread only when the author agrees or the user says to.\n   - **Escalate.** A request that changes the design, the scope or a one-way-door decision. It is not fixed in a comment thread: it becomes a dated amendment to `spec.md` or `plan.md`, through the `toolkit:grilling` skill with the user, and possibly a new ticket. Say which, and stop the sweep on that item.\n     Where the sorting is a judgment call, ask the user in one numbered round.\n\n4. **Work the fixes, smallest first.** For each:\n   - A comment: make the change on its line and nowhere else. Verify with the `toolkit:verify` skill. Commit as `fix(<scope>): <what the comment asked>` with the trailer `Change: <NNNN>` and the thread's URL in the body.\n   - A failing check: reproduce the failure locally with the feedback command, or the check's own command when the feedback command does not cover it. Fix it. Verify. Commit as `fix(ci): <what failed>`. If the same check fails again after your fix, stop and report; do not loop on a check that may be flaky or environmental. Say which it looks like and why.\n     Do not fold several items into one commit; the thread's author wants to see their change.\n\n5. **Push, with approval.** Show the commits and ask for go. Push with `git push`. Never force-push; if the branch has diverged, say so and stop. After the push, reply on each fixed thread with the commit hash and resolve it (`resolveReviewThread` mutation). Tick the matching boxes in `review.md` with the hash.\n\n6. **Wait for the checks**, then go back to step 2. Repeat until the list is empty or every remaining item is an escalation or an answer awaiting its author.\n\n7. **Learn.** A comment of the same kind as one in an earlier review, in this change's `review.md` or another's, is a pattern: apply the `toolkit:claude-md` discipline and propose the line.\n\n8. **Report.** What is green, what was answered and awaits a reply, what was escalated and to which artifact, and whether the pull request is ready to merge. Merging is the user's; say so.\n\n## Rules\n\n- Fix exactly what was asked. A sweep is not a refactor.\n- One commit per item, with the thread or check named, so the reviewer can follow.\n- Never force-push, never rebase a pushed branch, never resolve a thread the author has not been answered on.\n- A design-level comment stops the sweep. The artifact changes first, then the code.\n- A merge conflict stops the sweep, whether found at the start or after a push. The user resolves it.\n" : skills/pr-sweep: a skill that commits must say it never pushes

----------------------------------------------------------------------
Ran 46 tests in 1.304s

FAILED (failures=1)
```
