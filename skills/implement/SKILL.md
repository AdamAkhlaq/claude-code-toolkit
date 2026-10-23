---
name: implement
description: Execute a change's ticket graph: walk the frontier, hand each ready ticket to the executor the plan chose, verify every ticket independently, and merge the verified branches into the change's integration branch. Run with the change id or slug after the tickets gate.
disable-model-invocation: true
argument-hint: "<change id or slug>"
---

# Implement

Walk the ticket graph until every ticket is done. The ticket is the contract, the executor is the plan's recorded choice, and nothing merges until the verifier has passed it in a fresh context.

The change: $ARGUMENTS

The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`; run it as `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" <command> <change>`.

## Names

- Integration branch: `change/<NNNN>-<slug>`. The change's artifacts were committed here by the earlier gates.
- Ticket branch: `ticket/<NNNN>-<Tn>`, created from the integration branch when the ticket starts.
- Worktree: `.claude/worktrees/<NNNN>-<Tn>/`, one per ticket branch, when more than one executor runs at once. Add `.claude/worktrees/` to `.git/info/exclude` so it never shows up as untracked.
- Commit trailers: `Change: <NNNN>` on every commit, `Ticket: <NNNN>-<Tn>` on ticket commits.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists and has a `feedbackCommand`; without one, stop, because nothing can be verified. Resolve the change; with an empty argument take the one change whose intent is `building`. `validate <change>` prints `ok`. The integration branch exists and is checked out, and the tree is clean. If any of these fail, say which and stop.

2. **Read the execution decision.** `execution` and `concurrency` from `plan.md`, `concurrency` from `.claude/toolkit.json`. The effective concurrency is the smaller of the two. In `single` mode it is 1.

3. **Confirm once.** Tell the user what will happen: ticket branches will be created and committed to, verified tickets will be merged into the integration branch, nothing will be pushed, and the run will stop at any serial ticket, any ticket reopened twice, or any merge conflict. Ask for go. In `headless` mode the invocation is the go; do not ask.

4. **Loop until the frontier is empty.**

   a. `frontier --json <change>`. If empty and tickets remain, something is blocked on a reopened or in-progress ticket: show `status <change>` and stop.

   b. **Serial tickets run alone.** If the frontier contains a `serial: true` ticket, run only that ticket, in the main session, as `single`, and tell the user it is a one-way door they are expected to watch. In `headless` mode, stop before it and report that a human is needed.

   c. **Take up to the effective concurrency** from the frontier, lowest id first. A ticket with its own `executor` uses that instead of the plan's mode.

   d. **Start each ticket.** Create `ticket/<NNNN>-<Tn>` from the integration branch. For more than one executor at a time, or whenever the mode is not `single`, add a worktree for it: `git worktree add .claude/worktrees/<NNNN>-<Tn> ticket/<NNNN>-<Tn>`. In `single` mode, check the ticket branch out in the main working tree instead; a worktree isolates concurrent executors and there are none.

   e. **Execute.** The brief for any executor is: the ticket path, the checkout directory, the change folder, the integration branch name, and, on a retry, the verifier's reopen reason. By mode:
   - `single`: follow the steps in `${CLAUDE_PLUGIN_ROOT}/agents/implementer.md` yourself, in this session, with the user able to watch.
   - `subagents`: one `toolkit:implementer` agent per ticket, started in parallel, each in its worktree. Wait for all of them.
   - `team`: one teammate per ticket with the implementer brief when the session has agent-team tools; otherwise fall back to `subagents` and say so.
   - `headless`: as `subagents`, and never ask the user anything.

   f. **Verify each ticket that returns.** Start a `toolkit:verifier` agent with the ticket path, the checkout directory and the integration branch name. It has not seen the executor's work and must not; pass it nothing else. Read its three-line report.

   g. **On pass:** from the main working tree on the integration branch, `git merge --no-ff ticket/<NNNN>-<Tn>` with the message `merge(<Tn>): <ticket title>` and the trailers. Remove the worktree and delete the ticket branch. A merge conflict is a stop condition: leave the merge in progress, show the conflicting files, and hand it to the user.

   h. **On reopen:** send the ticket back to the same executor kind with the reopen reason, once. If it is reopened a second time, stop the run, leave the branch and worktree in place, show the verifier's checks, and hand it to the user. Other tickets already running finish and are verified and merged normally before the stop.

   i. **Keep the graph true.** After each merge, `validate <change>`; if an executor added files to a ticket and that created an overlap, the validator says so, and that is a stop condition the user resolves by editing tickets.

5. **Finish.** When every ticket is `done`: run the feedback command once more on the integration branch and quote the tail. Show `status <change>` and `render <change>`. Draft the pull request description: the change id and title, the spec's outcome in two lines, which tickets ran, whether the change was a one-way or two-way door, and the final evidence. Show it. The next step is `/toolkit:review <NNNN>`; after it, the user pushes and opens the pull request, or asks you to run `gh pr create` with it.

6. **Report.** Tickets merged, tickets stopped and why, and the exact command to resume: `/toolkit:implement <NNNN>` picks up from the frontier.

## Rules

- Never merge a ticket the verifier did not pass in this run. The executor's own evidence is necessary, not sufficient.
- Never push. Never touch the default branch.
- Never work a ticket outside its branch, and never let two executors share a working tree.
- Stop conditions stop. A serial ticket, a double reopen, a merge conflict and an invalid graph are the user's to resolve. Resuming is cheap; a bad merge is not.
- Record, do not reason: which tickets ran, with which executor, on which branch, is in the ticket files. The run leaves no state anywhere else.
