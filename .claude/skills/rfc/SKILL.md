---
name: rfc
description: >-
  Write or improve an RFC / design document for a non-trivial change before
  building it. Use when the user wants a design doc, technical proposal, RFC, or
  to think through and socialise an approach with goals, alternatives, and
  trade-offs. For recording a decision that has already been made, use the adr
  skill; for incident analysis, use the rca skill.
---

# RFC / Design Document

A design doc (a.k.a. RFC) is the artifact you write **before** building something
non-trivial. Its real value is the *process*: forcing yourself to think through
the problem, surfacing alternatives, and getting review from people who'll catch
issues while they're still cheap. The document is the medium; the design and the
shared understanding are the product.

## When to use it

Write one when the work is large, risky, cross-team, hard to reverse, or
controversial — anything where being wrong is expensive and a few engineers'
review is worth a day of writing. Skip it for small, obvious, or easily reversed
changes; a good PR description is enough there.

This skill is for the **proposal**. Once the design is agreed and a specific
architectural decision falls out of it, capture that decision compactly with the
**adr** skill and link the two.

## Canonical structure

Based on "Design Docs at Google", with proposal elements from the Rust RFC
process. Adapt — not every doc needs every section — but justify omissions.

1. **Title / metadata** — title, author(s), reviewers, status, date.
2. **Context & Scope** — the landscape and the problem. What exists today, why
   it's a problem now, and the boundaries of what this doc addresses. Neutral and
   brief; orient the reader, don't argue yet.
3. **Goals** — what success looks like, ideally measurable.
4. **Non-Goals** — what you are explicitly *not* solving. This is one of the most
   valuable sections: it scopes the review and pre-empts "but what about…".
5. **Design / Proposed Solution** — the actual proposal, in enough detail to
   evaluate: data model, APIs/interfaces, request flow, key components, failure
   handling. Diagrams where they help. This is the bulk of the doc.
6. **Alternatives Considered** — the other serious options and *why you rejected
   them*. At least one or two, with honest trade-offs. A design with no
   alternatives reads as unexamined.
7. **Cross-Cutting Concerns** — security, privacy, data handling, performance &
   scale, observability, cost, backwards compatibility, operability. Call out the
   ones that apply; state "N/A — because…" for the ones that don't.
8. **Drawbacks** — why we might choose *not* to do this at all.
9. **Rollout Plan** — how it ships safely: phasing, flags, migration, fallback,
   what you'll monitor.
10. **Unresolved Questions** — open issues you want reviewers to weigh in on.
    Naming them builds trust; pretending certainty erodes it.

## Review workflow

The doc is meant to be commented on. Share it for a defined review window
(typically ~1 week), gather feedback inline, iterate, and reach an explicit
decision (accepted / rejected / deferred) from the responsible decision-maker(s).
Once accepted it becomes the source of truth for implementation; record any hard
architectural decision it produced as an ADR.

## Quality rubric

A strong design doc:

- **Leads with the problem, not the solution** — Context & Scope makes the reader
  care before the proposal appears.
- **Has real Non-Goals** — scope is bounded explicitly, not left implicit.
- **Considers ≥2 serious alternatives** with honest trade-offs, including the
  status quo / "do nothing" where relevant.
- **Engages the cross-cutting concerns** that actually apply, and says so for the
  ones that don't.
- **Is honest about uncertainty** — Drawbacks and Unresolved Questions are
  populated, not empty.
- **Is right-sized** — long enough to evaluate the design, short enough that busy
  reviewers actually read it. Detail belongs in proportion to risk.

## Common pitfalls

- Jumping straight to the solution with no framing of the problem.
- Empty or trivial Non-Goals / Alternatives — the sections that prove you thought.
- Hand-waving the cross-cutting concerns (security, rollback, observability).
- A wall of low-level detail no reviewer can hold in their head — summarise,
  link the deep specifics.
- Writing it after the code is built — then it's documentation, not design.

## Naming & storage

- Directory: `docs/rfc/` (or `docs/design/`).
- Filename: `NNNN-kebab-case-title.md`, zero-padded sequence.
- Track status in the metadata header: `Draft` → `In Review` → `Accepted` /
  `Rejected` / `Superseded`.

## Template

Copy `templates/design-doc.md` and fill it in.

## Sources

- Malte Ubl, "Design Docs at Google" — https://www.industrialempathy.com/posts/design-docs-at-google/
- Rust RFC process & template — https://github.com/rust-lang/rfcs
- Oxide RFD process — https://rfd.shared.oxide.computer/rfd/0001
