---
name: tickets
description: Decompose an accepted plan into a validated graph of tracer-bullet tickets under docs/changes/<change>/tickets/, the fourth gate. Each ticket proves one behaviour with one test at an agreed seam, fits one session, and lists the files it touches. Run with the change id or slug.
disable-model-invocation: true
argument-hint: "<change id or slug>"
---

# Tickets

Cut the plan into tracer bullets and wire them into a graph the tool can validate. After this gate the work can be executed by anyone, in any order the graph allows, without the conversation.

The change: $ARGUMENTS

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`. The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`; run it as `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" <command> <change>`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. Resolve the change; with an empty argument take the one change whose plan is `accepted` and whose `tickets/` folder is empty, otherwise ask. If tickets exist, the user wants to add or amend: read them all first, keep existing ids, and append new ones.

2. **Read.** `plan.md` for the approach, seams and execution mode. `spec.md` for the numbered requirements. `GLOSSARY.md`. The files the approach names, enough to know which paths each ticket touches.

3. **Cut the tickets.** Each ticket is one tracer bullet:
   - **One behaviour**, stated in `proves` as the test that will show it: "GET /items with an expired token returns 401" rather than "auth middleware".
   - **One seam** from the plan, named in Context. The proving test lives there.
   - **Fits one session**: a fresh agent can read the ticket, write the test and the code, and verify, without running out of context. If a ticket needs more than one proving test, more than about five files, or a design decision not in the plan, split it.
   - **Vertical, not horizontal.** Prefer "the endpoint returns the first real response, with a stub store" to "the store layer" then "the service layer" then "the endpoint". The first ticket of a feature should make something observable end to end, however thin.
   - **Files**: every path it will touch, including tests and the glossary if it adds a term. The validator uses this list to keep parallel tickets apart, so be complete rather than optimistic.
   - **Blocked by**: only the tickets whose output this one needs. Fewer edges, more parallelism. Never add an edge to control order for its own sake.
   - **Serial**: `serial: true` for a one-way door: a migration that runs against real data, a deploy, a public contract change. These run alone with a human watching.
   - **Executor**: only when one ticket needs a different executor from the plan's mode, with the reason in Context.
     Every spec requirement must be covered by at least one ticket's acceptance list. Keep a requirement-to-ticket map and show it at the gate.

4. **Write the files.** `tickets/T<n>-<slug>.md` from `templates/ticket.md`, numbered from `T1` in rough execution order. Context says which requirements and which seam, and any gotcha already known. Acceptance is a checklist whose first line is always the proving test passing. Evidence stays empty.

5. **Validate.** Run `validate <change>`. Fix every error it lists: missing fields, unknown or cyclic edges, parallel tickets sharing a file. Repeat until it prints `ok`. Then run `render <change>` and include the Mermaid graph in what you show the user, and `frontier <change>` to show which tickets start first.

6. **Grill the decisions.** Where the cut could reasonably go another way, where a ticket is a one-way door, and where a requirement has no natural ticket, run the `toolkit:grilling` skill. One numbered round, at most two.

7. **Present at the gate.** The ticket list with id, title, blocked-by and files; the requirement map; the graph; the frontier. Ask the user to accept or name what to change. On accept, set the intent's `status` to `building` with a one-line amendment noting the date and ticket count.

8. **Commit, with approval.** Stage `tickets/`, the intent amendment, and `GLOSSARY.md` if changed. Message `docs(<NNNN>): tickets for <title>` with the trailer `Change: <NNNN>`. Commit only when the user says go. Never push.

9. **Hand off.** One line: `/toolkit:implement <NNNN>` is next, and which execution mode it will use.

## Rules

- `proves` is a sentence a test can be written from. If you cannot phrase it, the ticket is not one behaviour.
- The graph tool is the judge of the graph. Never argue with its output; fix the tickets.
- Tickets are the contract for executors who have not seen the conversation. Write for them.
- After the gate, a ticket is amended in place by its executor (status, files, evidence) and new tickets are appended; nothing is deleted. A ticket that turns out to be wrong gets `status: done` with an Evidence note saying it was dropped and why, so the graph stays valid.
