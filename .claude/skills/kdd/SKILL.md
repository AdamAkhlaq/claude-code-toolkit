---
name: kdd
description: >-
  Write or improve a Key Decision Document (KDD) — a record of a significant
  decision that is not purely architectural: product direction, process, tooling,
  vendor, or cross-team choices. Use when the user wants to capture a key
  decision, its rationale, the options weighed, and who signed off. For a purely
  architectural/technical decision, use the adr skill instead.
---

# Key Decision Document (KDD)

A KDD records a **significant decision** so that, months later, anyone can see
what was decided, why, who agreed, and when to revisit it. It's the broader
sibling of the ADR: an ADR is scoped to system architecture and lives beside the
code, whereas a KDD covers any consequential choice — product, process, tooling,
vendor, organisational, cross-team — that future people will need the reasoning
for.

## KDD vs ADR — pick the right one

- **Architectural/technical decision** (datastore, API contract, system
  boundary) → use the **adr** skill. ADRs are numbered, immutable, in-repo.
- **Broader significant decision** (which vendor, a team process, a roadmap
  trade-off, a tooling standard) → KDD. KDDs record **stakeholders/approvers** and
  a **revisit date**, because such decisions are often time-bound and owned by
  people outside a single codebase.

If you're unsure and the decision is fundamentally about how the *system* is
built, prefer an ADR.

## When to use it

When a decision is expensive to reverse, affects multiple people or teams, sets a
precedent, or will predictably be questioned later ("why are we doing it this
way?"). Skip it for routine, low-impact, or easily reversed choices.

## Canonical structure

1. **Decision Summary** — the decision in one or two sentences, up front, so a
   reader gets the answer immediately.
2. **Context / Background** — the situation that forced the decision: problem,
   constraints, what prompted it now.
3. **Decision Drivers** — the criteria that actually mattered (cost, time-to-
   market, risk, team capacity, strategic fit…).
4. **Options Considered** — the serious alternatives, each with its trade-offs
   against the drivers. Include "do nothing / status quo" where relevant. At
   least two.
5. **Decision & Rationale** — what was chosen and *why it beat the alternatives*,
   tied back to the drivers.
6. **Stakeholders / Approvers** — who was consulted, who decided, and who signed
   off (RACI-style if useful). This is what distinguishes a KDD from an ADR.
7. **Implications & Follow-ups** — consequences, new commitments, dependencies,
   and the concrete next steps with owners.
8. **Review / Revisit Date** — when this should be re-examined, or the condition
   that would reopen it. Decisions made under today's assumptions should have an
   expiry.

## Quality rubric

A strong KDD:

- **Answers first** — the decision is stated up top, not buried.
- **Shows the work** — drivers + ≥2 options with honest trade-offs, not a
  single foregone conclusion.
- **Names accountability** — explicit approvers/stakeholders, not an anonymous
  "we decided".
- **Justifies over alternatives** — explains why the chosen option won.
- **Has a revisit trigger** — a date or condition for re-examination.
- **Is honest about implications** — downstream costs and commitments, not just
  upside.

## Common pitfalls

- Reaching for a KDD when it's really an architectural decision (use an ADR).
- No named approvers — the decision has no accountable owner.
- Listing only the chosen option; no drivers, no alternatives.
- No revisit date — stale decisions silently outlive their assumptions.
- Restating background at length while burying the actual decision.

## Naming & storage

- Directory: `docs/decisions/`
- Filename: `NNNN-kebab-case-title.md`, zero-padded sequence (or date-prefixed if
  you prefer chronological ordering).
- Track status: `Proposed` → `Decided` → `Revisited` / `Superseded`.

## Template

Copy `templates/kdd.md` and fill it in.

## Related

- For architectural/technical decisions, use the **adr** skill.
- If a KDD requires a deeper design exploration first, write an **rfc** and link
  it from the Context section.
