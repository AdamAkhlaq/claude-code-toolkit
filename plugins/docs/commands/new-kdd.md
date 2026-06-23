---
description: Scaffold a new Key Decision Document (KDD) from the standard template.
argument-hint: [decision title]
disable-model-invocation: true
---

Create a new Key Decision Document titled: **$ARGUMENTS**

Follow the `docs:kdd` skill for structure and the quality rubric. The blank
template is at `skills/kdd/templates/kdd.md`.

First, sanity-check the doc type: if this is a **purely architectural/technical**
decision, tell the user it likely belongs in an ADR (`/docs:new-adr`) and confirm
before proceeding.

Steps:

1. **Apply the `kdd` skill** to load the canonical structure and rubric.
2. **Find the next number:** scan `docs/decisions/` for the highest `NNNN-` prefix
   and add one (start at `0001` if empty). Create `docs/decisions/` if needed.
3. **Draft the KDD:** copy the template and fill what you can from this
   conversation. Ensure Decision Drivers, at least two Options, the Stakeholders/
   Approvers table, and a Review/Revisit date are populated — these are what make
   a KDD complete. Ask the user for approvers and the revisit date if unknown.
   Leave `Status: Proposed`.
4. **Write the file** to `docs/decisions/NNNN-kebab-case-title.md`.
5. **Print the path** and a one-line summary of the decision recorded.
