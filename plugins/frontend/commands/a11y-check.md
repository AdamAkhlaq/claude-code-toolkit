---
description: Run an accessibility (WCAG 2.2 AA) check over selected frontend code.
argument-hint: [file/dir/component, or blank for the current diff]
disable-model-invocation: true
---

Run an accessibility check on: **$ARGUMENTS** (defaults to the current diff /
recently changed UI files if no argument is given).

Delegate to the **`a11y-auditor`** agent for the deep WCAG 2.2 AA + ARIA APG pass,
then relay its findings. If the target is large, scope to the changed/named files
and say so.

Return the auditor's prioritized result: **Blocking / Should-fix / Nits**, each
tied to a WCAG criterion or APG pattern with a concrete fix, plus the list of
**manual checks** (contrast, screen-reader, real focus order) that static review
can't confirm.
