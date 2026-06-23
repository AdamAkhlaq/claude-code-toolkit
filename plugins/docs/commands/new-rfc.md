---
description: Scaffold a new RFC / design document from the standard template.
argument-hint: [proposal title]
disable-model-invocation: true
---

Create a new RFC / design document titled: **$ARGUMENTS**

Follow the `docs:rfc` skill for structure (Context & Scope, Goals, Non-Goals,
Design, Alternatives, Cross-Cutting Concerns, Drawbacks, Rollout, Unresolved
Questions) and the quality rubric. The blank template is at
`skills/rfc/templates/design-doc.md`.

Steps:

1. **Apply the `rfc` skill** to load the canonical structure and rubric.
2. **Find the next number:** scan `docs/rfc/` for the highest `NNNN-` prefix and
   add one (start at `0001` if empty). Create `docs/rfc/` if it doesn't exist.
3. **Draft the RFC:** copy the template and fill what you can from this
   conversation and the repo. Make sure Non-Goals and at least two real
   Alternatives are populated — do not leave them as placeholders. Ask the user
   for the goals and any constraints you can't infer. Leave `Status: Draft`.
4. **Write the file** to `docs/rfc/NNNN-kebab-case-title.md`.
5. **Print the path** and list any Unresolved Questions you flagged for review.
