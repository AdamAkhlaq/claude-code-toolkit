---
description: Run a full frontend audit (accessibility + performance + review) over the UI.
argument-hint: [file/dir, or blank for the whole UI / current diff]
disable-model-invocation: true
---

Run a full frontend audit on: **$ARGUMENTS** (defaults to the current diff, or the
main UI source if the user asks for the whole app).

Coordinate the `frontend` plugin's agents and synthesize one report:

1. Determine the files in scope. For a large codebase, focus on the changed or
   named files and state what you covered.
2. Run, in parallel where possible:
   - **`a11y-auditor`** — WCAG 2.2 AA + ARIA pass.
   - **`perf-auditor`** — Core Web Vitals + bundle/asset risks.
   - **`frontend-reviewer`** — semantics, CSS, security, component design, i18n/SEO.
3. **Merge and de-duplicate** the findings into a single prioritized report:
   **Blocking / Should-fix / Nits**, grouped by area, each with location and a
   concrete fix. Call out the top 3 things to do first.
4. List the **manual checks** that require a human (real contrast, screen-reader
   output, field performance measurement) and which tools to use.

Be honest about coverage — if only part of a large UI was audited, say so.
