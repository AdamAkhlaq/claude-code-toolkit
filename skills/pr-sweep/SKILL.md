---
name: pr-sweep
description: Bring a pull request to green: read its unresolved review threads and failing checks, fix or answer each comment, repair each failing check with the feedback command as the judge, and push with your go-ahead, until nothing is left. Run with the pull request number, or bare for the current branch's pull request.
disable-model-invocation: true
argument-hint: "[pull request number]"
---

# PR sweep

A pull request is done when every review thread is resolved and every check is green. This skill works through both until the list is empty or something needs a human.

The pull request: $ARGUMENTS

If the argument is empty, use `gh pr view --json number` on the current branch.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists with a `feedbackCommand`. `gh auth status` succeeds. The pull request's head branch is checked out and the tree is clean. Note the change id from the branch name or the commit trailers.

2. **Read the whole list first.** Collect, in one pass:
   - Unresolved review threads: `gh api graphql` on `pullRequest.reviewThreads` with `isResolved`, `path`, `line`, and each comment's author and body.
   - Failing or pending checks: `gh pr checks <n>` and, for each failure, the log through `gh run view <id> --log-failed`.
   - The review record, `docs/changes/<change>/review.md`, when it exists, so the sweep closes its boxes too.
     Show the user the list, grouped as comments and checks, before changing anything. Number the items; the numbers are how you refer to them from here.

3. **Sort each item.** Every item is one of:
   - **Fix.** A concrete request or a real failure. Make the change.
   - **Answer.** A question, or a request that is wrong given the spec or the plan. Reply with the reason, citing the artifact, and resolve the thread only when the author agrees or the user says to.
   - **Escalate.** A request that changes the design, the scope or a one-way-door decision. It is not fixed in a comment thread: it becomes a dated amendment to `spec.md` or `plan.md`, through the `toolkit:grilling` skill with the user, and possibly a new ticket. Say which, and stop the sweep on that item.
     Where the sorting is a judgment call, ask the user in one numbered round.

4. **Work the fixes, smallest first.** For each:
   - A comment: make the change on its line and nowhere else. Verify with the `toolkit:verify` skill. Commit as `fix(<scope>): <what the comment asked>` with the trailer `Change: <NNNN>` and the thread's URL in the body.
   - A failing check: reproduce the failure locally with the feedback command, or the check's own command when the feedback command does not cover it. Fix it. Verify. Commit as `fix(ci): <what failed>`. If the same check fails again after your fix, stop and report; do not loop on a check that may be flaky or environmental. Say which it looks like and why.
     Do not fold several items into one commit; the thread's author wants to see their change.

5. **Push, with approval.** Show the commits and ask for go. Push with `git push`. Never force-push; if the branch has diverged, say so and stop. After the push, reply on each fixed thread with the commit hash and resolve it (`resolveReviewThread` mutation). Tick the matching boxes in `review.md` with the hash.

6. **Wait for the checks**, then go back to step 2. Repeat until the list is empty or every remaining item is an escalation or an answer awaiting its author.

7. **Learn.** A comment of the same kind as one in an earlier review, in this change's `review.md` or another's, is a pattern: apply the `toolkit:claude-md` discipline and propose the line.

8. **Report.** What is green, what was answered and awaits a reply, what was escalated and to which artifact, and whether the pull request is ready to merge. Merging is the user's; say so.

## Rules

- Fix exactly what was asked. A sweep is not a refactor.
- One commit per item, with the thread or check named, so the reviewer can follow.
- Never force-push, never rebase a pushed branch, never resolve a thread the author has not been answered on.
- A design-level comment stops the sweep. The artifact changes first, then the code.
