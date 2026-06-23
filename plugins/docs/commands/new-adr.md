---
description: Scaffold a new Architecture Decision Record (ADR) from the standard template.
argument-hint: [decision title]
disable-model-invocation: true
---

Create a new Architecture Decision Record titled: **$ARGUMENTS**

Follow the `docs:adr` skill for structure, the quality rubric, and the choice
between the Nygard and MADR templates (it bundles both under `skills/adr/templates/`).

Steps:

1. **Apply the `adr` skill** to load the canonical structure and rubric. Pick the
   template: Nygard (default) unless the decision is contested or has several
   serious alternatives, in which case use MADR.
2. **Find the next number:** scan `docs/adr/` for the highest `NNNN-` prefix and
   add one (start at `0001` if empty). Create `docs/adr/` if it doesn't exist.
3. **Draft the ADR:** copy the chosen template and fill every section. Pull
   Context, Decision, and Consequences from this conversation and the repo where
   possible; ask the user only for what you genuinely can't infer. Leave `Status:
   Proposed`.
4. **Write the file** to `docs/adr/NNNN-kebab-case-title.md` (slug derived from
   the title).
5. **Print the path** and a one-line summary of the decision recorded.
