---
name: intent
description: Turn any input (an idea, a conversation, a pasted ticket, an alert) into a committed intent.md under docs/changes/, the first gate of the workflow. Run with the input as the argument, or bare to use the current conversation.
disable-model-invocation: true
argument-hint: "[the idea, ticket text, or alert]"
---

# Intent

Start from anything, end in a committed `intent.md`. This is the open front door and the fixed exit: whatever form the input takes, the output has one shape, and the problem is understood before anyone designs a solution.

The input: $ARGUMENTS

If the argument is empty, the input is the conversation so far. If it is a path or a URL, read it.

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`. The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` must exist; if not, stop and point at `/toolkit:setup`. Note the current branch and whether the tree is clean, so the commit at the end lands where the user expects.

2. **Keep the origin verbatim.** Copy the input as it arrived into the Origin section: the quoted conversation, the pasted ticket, the alert text. Do not tidy it. If it arrived in the conversation, quote the user's own sentences.

3. **Check for an existing change.** Read `docs/changes/*/intent.md` titles and problems. If this input is already covered by a live change, say so and stop; the right move is an amendment to that change, not a new one.

4. **Look before asking.** Use the `toolkit:researcher` agent, or look directly when the subject is small, to find: the code paths involved, how the behaviour works today, prior changes, ADRs and incidents on the subject, and the glossary terms in play. Facts found here go into the draft with their citations. Nothing found here is asked.

5. **Draft.** Fill the template at `templates/intent.md`:
   - **Problem**: what is wrong or missing, for whom, and what it costs, in the project's vocabulary. No solution. If the input arrived as a solution ("add a cache"), work back to the problem it solves and write that; the proposed solution is noted in Proposed outcome as one option, not the outcome.
   - **Proposed outcome**: what is observably true once this is done. A reader could check it without reading code.
   - **Affected users and systems**: who feels it, and the paths that carry it, located not guessed. Delete the section if obvious.
   - **Constraints**: ADRs, policies, compatibility promises, deadlines. Delete if none.
   - **Open questions**: every unknown, one line each, tagged `Fact:` or `Decision:`.
     Apply the `toolkit:glossary` discipline to every term the draft introduces.

6. **Grill until ready.** The definition of ready, all of which must hold:
   - The problem names who has it and what it costs, and contains no solution.
   - The outcome is observable.
   - Every `Fact:` question has been looked up or has a named person who can answer it.
   - Every `Decision:` question has an answer from the user, or is explicitly left open with an owner.
   - The affected code has been located, or the change is small enough that locating it is the first ticket.
     For what is missing, run the `toolkit:grilling` skill: one numbered round, recommended answers, at most two rounds. Record the answers under Open questions as resolved lines.

7. **Allocate the change.** Propose a slug of two to four lowercase words. Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" new <slug>` to allocate the id and create `docs/changes/<NNNN>-<slug>/tickets/`. Write `intent.md` there with `id`, `slug`, `status: proposed`, `originator` (the git user name) and `created` (today).

8. **Present at the gate.** Show the user the file, the glossary entries added, and the open questions that remain. Ask one thing: accept, or what to change. On accept, set `status: accepted` and `accepted_by` to the user's name. On changes, edit and present again; the artifact is not yet committed, so it may be rewritten freely until it is.

9. **Commit, with approval.** Create the branch `change/<NNNN>-<slug>` from the current branch if the user is on the default branch, otherwise stay where they are and say so. Stage `docs/changes/<NNNN>-<slug>/intent.md` and `GLOSSARY.md` if it changed. Show the proposed message, `docs(<NNNN>): intent for <title>` with the trailer `Change: <NNNN>`, and commit only when the user says go. The gate is passed when the commit exists.

10. **Hand off.** One line: the next step is `/toolkit:spec <NNNN>`.

## Rules

- Never write a design, an approach or a file list into the intent. That is the spec's and the plan's job.
- Never drop the user's words from Origin. Shortening them loses the thing they actually asked for.
- After the commit, the intent is amended, never rewritten: later changes go in a dated `## Amendment <date>: <what changed>` section at the end.
- Never commit without the user's go-ahead, and never push.
