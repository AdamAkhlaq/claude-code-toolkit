---
name: spec
description: Write spec.md for an accepted intent, the second gate. States the outcome in testable terms, the scope, numbered requirements, and every policy conflict found, then asks for a go or no-go. Run with the change id or slug.
disable-model-invocation: true
argument-hint: "<change id or slug>"
---

# Spec

Turn an accepted intent into an agreed, testable outcome. The spec is what the plan is written against and what the review's compliance pass checks the diff against, so every requirement in it has to be observable.

The change: $ARGUMENTS

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. Resolve the change under `docs/changes/`; if the argument is empty and exactly one change has an accepted intent and no `spec.md`, take that one, otherwise ask. The intent's `status` must be `accepted`. If `spec.md` already exists, the user wants an amendment: read it, ask what changed, and add a dated `## Amendment` section rather than a new file.

2. **Read the context the spec must respect.** `intent.md` in full. `GLOSSARY.md`. Every file under `docs/adr/`. `REVIEW.md`. `CLAUDE.md` and any policy skills the repo carries. Every other live change's `intent.md` and `spec.md`, to find overlap. Use the `toolkit:researcher` agent for anything that needs code reading: the current behaviour the requirements replace, the contracts the change must keep.

3. **Draft from the template at `templates/spec.md`.**
   - **Outcome**: the intent's proposed outcome restated so that each sentence could be checked by a test or an observation. If this disagrees with the intent, this wins and the intent gets an amendment in the same commit.
   - **Scope**: in and out, with the things a reader would assume are in but are not, named.
   - **Requirements**: numbered, one observable statement each, grouped when there are more than a handful. Each uses glossary terms. A requirement that cannot be tested is rewritten until it can or moved to Design notes as guidance.
   - **Policy conflicts flagged**: each place the spec collides with an ADR, a policy skill, a security or compliance rule, `REVIEW.md`, a global rule in `CLAUDE.md`, or another live change. Name the conflict, who owns the policy, and the resolution or the open decision. Write `None found` only after looking at all of the sources in step 2.
   - **Design notes**: optional. API shapes, data model, sketches. Enough for someone who was not in the room to write the plan.
     Apply the `toolkit:glossary` discipline to new terms.

4. **Grill the decisions.** Scope boundaries, conflict resolutions, and any requirement the intent left ambiguous are decisions. Run the `toolkit:grilling` skill: one numbered round, recommended answers, at most two rounds. Facts are looked up, not asked.

5. **Present at the gate.** Show the spec, the conflicts, and the glossary changes. Ask for one decision: go or no-go. On go, set `go_no_go: go`, `decided_by` to the user's name, and `status: accepted`. On no-go, set `go_no_go: no-go`, record the reason under Outcome, and set the intent's status to `abandoned` with an amendment saying why; the spec is still committed, because a decision not to build is also a decision worth keeping.

6. **Commit, with approval.** Stage `spec.md`, any intent amendment, and `GLOSSARY.md` if changed. Message `docs(<NNNN>): spec for <title>` with the trailer `Change: <NNNN>`. Commit only when the user says go. Never push.

7. **Hand off.** One line: `/toolkit:plan <NNNN>` is next, or nothing if no-go.

## Rules

- Requirements describe behaviour, not implementation. "Requests over the limit receive 429" is a requirement; "use a token bucket" is a design note.
- Scope out loud. The cost of an unstated assumption is a ticket that builds the wrong thing.
- Every conflict is written down even when resolved in a minute, because the review pass reads this section.
- After the commit, amend with a dated section; never rewrite.
