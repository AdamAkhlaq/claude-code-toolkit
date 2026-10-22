---
name: review
description: Review a change before it merges: one reviewer agent per pass in REVIEW.md, findings merged into review.md in the change folder and posted to the pull request, every Important finding fixed or waived by the code owner. Run with the change id or slug, or a pull request number.
disable-model-invocation: true
argument-hint: "<change id, slug, or PR number>"
---

# Review

Three independent passes over the change's diff, each in a context that has not seen the others, merged into one record. The author's view of the code is not part of the input. The review ends with every Important finding fixed or waived, and the record committed beside the change's other artifacts.

The target: $ARGUMENTS

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. `REVIEW.md` exists at the repo root; if not, say that `/toolkit:setup` creates it from the plugin's template and stop. Resolve the change: a change id or slug under `docs/changes/`, or a pull request number, from which `gh pr view` gives the branch and the change id from its commit trailers. With an empty argument, take the one change whose intent is `building` and whose tickets are all done.

2. **Fix the diff.** The range is `<base>...<head>`: the default branch and the integration branch, or the pull request's base and head. Record the head commit hash; the review is of that commit, and a later push needs a fresh pass over the delta.

3. **Run the passes.** Read `REVIEW.md`. For each pass under its Passes heading, start one `toolkit:reviewer` agent with: the pass text quoted in full, the severity rules, the diff range, the change folder, and nothing else. Start them in parallel. Do not pass one reviewer's findings to another.

4. **Merge.** Collect the reports. Drop duplicates, keeping the stronger severity. Keep every Important. Keep at most five Nits across all passes, chosen by value; say how many were dropped. Re-read each Important finding against the code yourself before recording it: a reviewer can be wrong about a line, and a wrong Important costs the author an argument.

5. **Look for repeats.** Compare the findings with every other `docs/changes/*/review.md`. A finding of the same kind raised in an earlier review is a pattern: apply the `toolkit:claude-md` discipline and propose the line.

6. **Write `review.md`** in the change folder:

   ```
   ---
   id: "<NNNN>"
   slug: "<slug>"
   reviewed: <head commit hash>
   created: <date>
   ---

   # Review: <title>

   ## Important
   - [ ] <path>:<line> <finding>. Fix: <fix>.

   ## Nits
   - <path>:<line> <finding>. Fix: <fix>.

   ## Out of pass
   - <one line each>

   ## Waivers
   <none yet>
   ```

   Every Important finding is a checkbox. A finding is closed either by a fix, with the commit hash written after the box, or by a waiver: a line under Waivers naming the finding, the reason, and the code owner who waived it, in their words.

7. **Post to the pull request** when one exists: each finding as an inline review comment on its line with `gh api` (`POST /repos/{owner}/{repo}/pulls/{n}/comments` with `commit_id`, `path`, `line`, `body`), then one summary comment linking `review.md` and listing the Important findings. Nits that have no line go in the summary. If there is no pull request, say so; the findings live in `review.md` until there is.

8. **Gate.** Show the user the Important findings and the proposed `CLAUDE.md` line if any. Ask one question: fix now, or waive, per finding. Fixes are small by definition; make each one, verify with the `toolkit:verify` skill, commit it on the integration branch with the trailer `Change: <NNNN>` and the finding's path in the message, and tick the box with the hash. Waivers need the owner's words and name. A fix that is not small is not a fix: it is a new ticket, appended to the graph with `/toolkit:tickets`, and the finding stays open until that ticket is done.

9. **Commit `review.md`, with approval.** Message `docs(<NNNN>): review of <head hash>`, trailer `Change: <NNNN>`. Commit only when the user says go. Never push.

10. **Hand off.** If a pull request exists, `/toolkit:pr-sweep <n>` takes it from here. If not, the user pushes and opens one.

## Rules

- A pass runs in its own context. Never review the diff yourself first and hand the reviewers your conclusions.
- Important findings are never silently dropped. Fixed, or waived with a name.
- Review the commit you recorded. New commits mean a new pass over the delta, appended to `review.md` as a dated section.
- Never push.
