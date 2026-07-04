---
name: adr
description: >-
  Write or improve an Architecture Decision Record (ADR). Use when capturing a
  significant architectural or technical decision, when the user mentions ADRs,
  decision records, "why did we choose X over Y", or wants to document a
  technical trade-off. For broader non-architectural decisions (product,
  process, org), use the kdd skill instead.
---

# Architecture Decision Record (ADR)

An ADR captures **one** architecturally significant decision — the context that
forced it, the option chosen, and the consequences you now have to live with.
ADRs are short, immutable once accepted, and live in the repo beside the code
they govern so the "why" travels with the "what".

## When to use it

Write an ADR when a decision is **architecturally significant**: it's costly to
reverse, affects the shape of the system, constrains future work, or future
engineers will ask "why on earth is it like this?". Examples: choosing a
datastore, a sync vs async boundary, an auth model, a public API contract, a
build/deploy topology.

**When *not* to use it:**
- Reversible, local implementation details → just write good code/comments.
- Broader decisions that aren't about system architecture (product direction,
  team process, vendor choice, hiring) → use the **kdd** (Key Decision Document)
  skill, which records stakeholders and a revisit date.

## Choosing a format

Two formats are bundled. Both are legitimate — pick by weight of the decision:

- **Nygard** (`templates/adr-nygard.md`) — minimal: Status, Context, Decision,
  Consequences. Default for most decisions; fast to write, easy to read.
- **MADR** (`templates/adr-madr.md`) — richer: adds Decision Drivers, an
  explicit Considered Options comparison, and Validation. Use when the decision
  is contested, has several serious alternatives, or needs an audit trail.

## Canonical structure

Nygard (the core four — present in both formats):

1. **Title** — `ADR-NNNN: short imperative phrase` (e.g. "Use PostgreSQL for the
   primary store"). Numbered, not dated.
2. **Status** — `Proposed` → `Accepted` → later `Deprecated` / `Superseded by
   ADR-NNNN`. Never edit an accepted ADR's decision; supersede it with a new one.
3. **Context** — the forces at play: the problem, constraints, requirements, and
   assumptions. Neutral and factual — no solution yet. A reader should feel the
   tension that makes the decision non-obvious.
4. **Decision** — the choice, stated in active voice ("We will…"). Just what was
   decided and the core reasoning.
5. **Consequences** — what becomes easier *and* harder afterwards. State the
   negatives honestly; every real decision has them. Include follow-on work and
   new constraints.

MADR adds, between Context and Decision:

- **Decision Drivers** — the criteria that actually matter (perf, cost,
  team familiarity, operational burden…).
- **Considered Options** — each serious option with its pros/cons against the
  drivers. At least two; "do nothing" is often a valid one.
- **Validation** (after Decision) — how you'll confirm the decision was right
  (a benchmark, a spike result, a metric to watch).

## Quality rubric

A strong ADR:

- **Captures the tension** — Context makes clear why the decision was hard; a
  reader could almost predict the options from it.
- **Justifies over alternatives** — explains why the chosen option beat the
  others, not merely what was picked. (MADR makes this explicit; in Nygard, fold
  it into Context/Decision.)
- **States honest consequences** — names the downsides and the new constraints,
  not just the wins.
- **Is decision-scoped** — one decision per record; no implementation manual, no
  unrelated decisions bundled in.
- **Is discoverable & immutable** — numbered, linked from an index; superseded
  records point forward to their replacement rather than being edited.
- **Is concise** — typically one page. If it's longer, it's probably an RFC (use
  the **rfc** skill) and the ADR should record only the resulting decision.

## Common pitfalls

- Writing the ADR *after* implementation as a rubber stamp — write it when the
  decision is being made, while alternatives are live.
- Listing only the chosen option (no alternatives, no drivers) — unfalsifiable.
- Burying the decision in a wall of background — keep Context tight.
- Editing accepted ADRs — supersede instead, preserving history.
- Hiding the negative consequences — that's the most valuable part for the
  next engineer.

## Naming & storage

- Directory: `docs/adr/`
- Filename: `NNNN-kebab-case-title.md`, zero-padded sequence (e.g.
  `0001-use-postgresql-for-primary-store.md`).
- Maintain `docs/adr/README.md` as an index (number, title, status) when the set
  grows.

## Templates

Copy one of these and fill it in:

- `templates/adr-nygard.md` — lightweight default.
- `templates/adr-madr.md` — richer, for contested decisions.

## Sources

- Michael Nygard, "Documenting Architecture Decisions" — https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- ADR organization & examples — https://adr.github.io/
- MADR (Markdown Any Decision Records) — https://adr.github.io/madr/
