---
description: Scaffold a new Product Requirements Document (PRD) from the template.
argument-hint: [product or feature title]
disable-model-invocation: true
---

Create a new Product Requirements Document titled: **$ARGUMENTS**

Follow the `docs:prd` skill for structure, the quality rubric, and the choice
between the one-pager and full templates under `skills/prd/templates/`.

Steps:

1. **Apply the `prd` skill** to load the canonical structure and rubric. Default
   to the **one-pager** template; use the **full PRD** for a large or cross-team
   initiative (ask if unsure which fits).
2. **Find the next number:** scan `docs/prd/` for the highest `NNNN-` prefix and
   add one (start at `0001` if empty). Create `docs/prd/` if needed.
3. **Draft the PRD:** copy the chosen template and fill what you can from this
   conversation. Lead with the problem and the user; make success metrics
   measurable (baseline + target); populate non-goals and prioritised
   requirements. Keep the technical "how" out — note that it belongs in an RFC.
   Ask the user for goals/metrics you can't infer. Leave `Status: Draft`.
4. **Write the file** to `docs/prd/NNNN-kebab-case-title.md`.
5. **Print the path** and list any Open Questions you flagged.
