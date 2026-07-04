---
name: prd
description: >-
  Write or improve a Product Requirements Document (PRD) — the what and why of a
  product or feature: problem, users, goals, success metrics, requirements, and
  scope. Use when the user wants a PRD, product spec, feature brief, or product
  one-pager. For the technical "how", write an rfc; for recording a decision, a
  kdd or adr.
---

# Product Requirements Document (PRD)

A PRD defines **what** to build and **why** — the problem, who has it, what
success looks like, and the requirements — so a team can align *before*
engineering starts. It is deliberately not the technical design (that's an RFC)
and not a decision record (that's a KDD/ADR). Its highest value is alignment:
nailing the problem and the measure of success before anyone writes code.

## When to use it

For a new product, a significant feature, or anything where it's worth getting
agreement on the problem and success criteria up front. Match the weight to the
work: a small feature deserves a **one-pager**; a major initiative deserves the
**full PRD**.

## Choosing a format

Two templates are bundled:

- **One-pager** (`templates/prd-one-pager.md`) — Lenny Rachitsky's 6-part brief:
  Description, Problem, Why now, Success, Audience, What. Default for most
  features; forces clarity in a page.
- **Full PRD** (`templates/prd-full.md`) — the comprehensive structure below.
  Use for large or cross-team initiatives.

## Canonical structure (full PRD)

Based on Atlassian's PRD template and SVPG (Marty Cagan) product principles.
Include what applies.

1. **Overview & context** — what this is and the background; one-paragraph summary.
2. **Goals & success metrics** — the outcomes you want, each **measurable** with a
   baseline and target. Avoid vanity metrics.
3. **Non-goals** — explicitly out of scope, to prevent scope creep.
4. **Users & use cases** — target personas, their needs, and key user stories.
5. **Requirements** — the functional requirements / user stories, **prioritised**
   (e.g. Must / Should / Could), each with **acceptance criteria**.
6. **UX & design** — flows, wireframes, or prototype links. For most PRDs the
   design carries more weight than prose.
7. **Non-functional requirements** — performance, scale, accessibility,
   compliance, where they matter.
8. **Dependencies & constraints** — other teams, APIs, platform limits, legal.
9. **Risks & assumptions** — categorised (value, usability, feasibility,
   viability per SVPG), with how you'll de-risk them.
10. **Rollout & milestones** — phasing, feature flags, migration, rough timeline.
11. **Open questions** — unresolved items, each with an owner.

## Quality rubric

A strong PRD:

- **Leads with the problem and the user**, not the solution — alignment before
  engineering.
- **Has measurable success metrics** — testable, with baseline and target.
- **States non-goals explicitly** — scope boundaries are clear.
- **Prioritises requirements** with acceptance criteria — not a flat wish-list.
- **Is honest about risk** — names value/usability/feasibility/viability risks and
  how they'll be tested.
- **Defers the "how"** — links to an RFC for technical design rather than
  embedding it.

## Common pitfalls

- Specifying a solution before the problem is nailed.
- Vague, unmeasurable goals ("improve engagement") with no baseline/target.
- No non-goals — scope creeps endlessly.
- A flat, unprioritised feature list with no acceptance criteria.
- Blending in technical design that belongs in an RFC.

## Naming & storage

- Directory: `docs/prd/` (or `docs/product/`).
- Filename: `NNNN-kebab-case-title.md`, zero-padded sequence.
- Track status: `Draft` → `In Review` → `Approved` / `Shipped`.

## Templates

- `templates/prd-one-pager.md` — concise default.
- `templates/prd-full.md` — comprehensive, for large initiatives.

## Related

- For the technical design, write an **rfc** and link it.
- For a specific recorded decision, use **adr** (architectural) or **kdd** (broader).

## Sources

- Atlassian, Product Requirements Document template — https://www.atlassian.com/software/confluence/templates/product-requirements
- Lenny Rachitsky's PRD one-pager — https://www.atlassian.com/software/confluence/templates/lennys-product-requirements
- Marty Cagan / SVPG, "Revisiting the Product Spec" — https://www.svpg.com/revisiting-the-product-spec/
