---
description: Scaffold a new RCA / postmortem from the blameless template.
argument-hint: [incident name]
disable-model-invocation: true
---

Create a new Root Cause Analysis / postmortem for the incident: **$ARGUMENTS**

Follow the `docs:rca` skill for structure, the blameless rule, and the choice
between the Google SRE postmortem and the Amazon COE (5 Whys) templates under
`skills/rca/templates/`.

Steps:

1. **Apply the `rca` skill** to load the canonical structure, the blameless
   framing, and the rubric. Default to the SRE postmortem template; use the COE
   template if the user wants a 5-Whys-driven analysis.
2. **Find today's date** and the incident date; scan `docs/postmortems/` to avoid
   filename collisions. Create the directory if it doesn't exist.
3. **Draft the postmortem:** copy the chosen template and fill what you can from
   this conversation, logs, and the repo. Enforce the rubric as you write —
   quantify impact, keep every cause and action item **systemic** (never blame an
   individual), and make action items specific, owned, and dated. Use 5 Whys to
   push past surface causes. Leave `Status: Draft`.
4. **Write the file** to `docs/postmortems/YYYY-MM-DD-kebab-incident-name.md`.
5. **Print the path** and list the action items with their owners and due dates.
