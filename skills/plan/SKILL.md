---
name: plan
description: Write plan.md for a change whose spec has a go, the third gate. Runs in plan mode, interrogates the approach, agrees the seams tests will be written at, and records the execution decision with its reason. Run with the change id or slug.
disable-model-invocation: true
argument-hint: "<change id or slug>"
---

# Plan

Decide how the spec's outcome will be reached, where tests will live, and who executes the tickets. Nothing is built here. The plan is what `tickets` decomposes and what the verifier reads to know which seam a proving test belongs at.

The change: $ARGUMENTS

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. Resolve the change; with an empty argument take the one change whose spec has `go_no_go: go` and no `plan.md`, otherwise ask. If `plan.md` exists, this is an amendment: dated section, not a rewrite.

2. **Enter plan mode.** Call `EnterPlanMode` if the tool is available, so nothing is written until the plan is approved. If it is not available, say that no file will be written before the gate and keep to that.

3. **Read.** `spec.md` and `intent.md` in full, `GLOSSARY.md`, the ADRs, and the code the spec touches. Use the `toolkit:researcher` agent to map the modules involved and how they are tested today: where the existing tests sit, what runs them, how long they take. The seams must be real boundaries in this codebase, not boundaries you wish it had.

4. **Draft from the template at `templates/plan.md`.**
   - **Approach**: the modules touched, in the order the work happens, in a few paragraphs. Enough that the tickets fall out of it.
   - **Execution**: `single`, `subagents`, `team` or `headless`, with the reason in a sentence or two, and `concurrency`. The default is `single` for a change of a few tickets or one with shared state the originator wants to watch; `subagents` when tickets are file-disjoint and more than a handful; `team` when tickets must coordinate or the graph is large; `headless` when nobody will be at the keyboard. Set the frontmatter to match. Mark here any ticket that will be a one-way door, because it runs `serial` and with a human watching.
   - **Seams**: one per line, each a public boundary where behaviour can be observed from outside, with what a test there catches and what it misses. Prefer fast seams: a function, a module's public API, an HTTP handler with a fake dependency. One slow end-to-end seam is allowed when the spec's outcome can only be seen there. No ticket may test anywhere else.
   - **Interrogation**: what could break; which step is riskiest and what contains it; whether someone who never saw the conversation could implement from the plan and tickets alone. Answer each honestly in a sentence or two. A plan that cannot answer the third with yes is not finished.
   - **Rejected alternatives**: each with why it lost. A rejected alternative that was a one-way door, or a chosen approach that is one, also gets an ADR at `docs/adr/<NNNN>-<slug>.md` from `templates/adr.md`.

5. **Grill the decisions.** The execution mode, the seams, and any approach choice with a real alternative are decisions. Run the `toolkit:grilling` skill: one numbered round, recommended answers, at most two rounds.

6. **Present at the gate.** In plan mode this is the plan the user approves. Show the approach, the seams, the execution decision and its reason, and the rejected alternatives. On approval, call `ExitPlanMode` where it applies, write `plan.md` with `status: accepted`, and write any ADR. On changes, revise and present again.

7. **Commit, with approval.** Stage `plan.md`, any ADR, and `GLOSSARY.md` if changed. Message `docs(<NNNN>): plan for <title>` with the trailer `Change: <NNNN>`. Commit only when the user says go. Never push.

8. **Hand off.** One line: `/toolkit:tickets <NNNN>` is next.

## Rules

- Seams before tests, tests before code: a seam not in this file is not a place a ticket may write a test.
- The execution decision is recorded with its reason, so it can be revisited when the reason stops holding.
- The plan names what is touched, not every line that changes. Detail beyond what the tickets need is cost without value.
- After the commit, amend with a dated section; never rewrite.
