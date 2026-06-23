---
description: Scaffold a new operational runbook from the standard template.
argument-hint: [service name]
disable-model-invocation: true
---

Create a new operational runbook for the service: **$ARGUMENTS**

Follow the `docs:runbook` skill for structure and the quality rubric. The blank
template is at `skills/runbook/templates/runbook.md`.

Steps:

1. **Apply the `runbook` skill** to load the canonical structure and rubric.
2. **Gather what you can from the repo:** service name, owning team, repo link,
   how it's deployed/run, dependencies, and any existing dashboards/alerts. Ask
   the user for on-call/contact details and dashboard links you can't infer.
3. **Draft the runbook:** copy the template and fill it in. Make alert and task
   steps concrete and copy-pasteable, each with a success check and a rollback
   where relevant. Set `Last reviewed` to today.
4. **Write the file** to `docs/runbooks/<service-name>.md` (create the directory
   if needed).
5. **Print the path** and note any sections you left as placeholders for the
   owner to complete (e.g. live dashboard links).
