---
name: runbook
description: >-
  Write or improve an operational runbook / playbook for a service — how to
  operate it, what its alerts mean, and how to troubleshoot and recover it. Use
  when the user wants a runbook, on-call playbook, operational guide, or
  step-by-step recovery procedures. Pairs with the rca skill (a runbook is the
  proactive twin of a postmortem).
---

# Operational Runbook / Playbook

A runbook tells an on-call engineer how to operate a service and what to do when
it misbehaves — at 3am, tired, under pressure. Its job is to turn an alert into a
known set of diagnosis and recovery steps, cutting time-to-mitigate. Write for a
competent engineer who does *not* know this service's internals: every step
should be scannable, actionable, and ideally copy-pasteable.

## When to use it

Write or update a runbook for any service that pages a human, has non-obvious
operational tasks, or whose recovery isn't self-evident from the code. Each alert
that can fire should link to the runbook entry that resolves it. Keep it living —
a stale runbook is worse than none because it misleads under pressure.

## Canonical structure

Adapted from the Skelton-Thatcher run-book template and SRE on-call practice.
Include what applies; cut what doesn't.

1. **Service metadata** (top of the page, always) — service name, owning team,
   on-call rotation/contact, source repo, runtime/where it lives, related
   services, SLOs/SLA.
2. **Overview** — what the service does, in business and technical terms, and its
   place in the system (a small diagram or dependency list helps).
3. **Dashboards & monitoring** — direct links to the dashboards, log queries, and
   health checks an on-call would open first, with the key metrics to watch.
4. **Alerts** — for *each* alert: what it means, severity, likely causes,
   diagnosis steps, and remediation. This is the heart of the runbook.
5. **Common operational tasks** — deploy, roll back, restart, scale, drain,
   rotate secrets, run a backfill — each as concrete, copy-pasteable steps with a
   success check.
6. **Failure modes & troubleshooting** — known ways it breaks and how to confirm
   and fix each; include rollback procedures.
7. **Dependencies** — upstream and downstream services, what breaks if each is
   down, and how to tell.
8. **Recovery / DR** — backup/restore and disaster-recovery procedures, with
   expected RTO/RPO if defined.
9. **Escalation** — who to page next, when, and how, if the steps above don't
   resolve it.

## Quality rubric

A strong runbook:

- **Has clear triggers** — a responder can instantly tell whether an entry
  applies to the alert in front of them.
- **Is actionable, not narrative** — numbered steps and runnable commands, each
  with a way to confirm it worked; not prose.
- **Is wired to monitoring** — live dashboard/log links and the exact metrics and
  thresholds that matter.
- **Includes rollback/safe-abort** — every risky operation says how to undo it.
- **Has an explicit escalation path** — names who's next and when to escalate.
- **Is current** — reflects the system as it is today; last-reviewed date present.

## Common pitfalls

- Prose descriptions instead of executable steps.
- Commands with no success/failure check, or no rollback.
- Dead dashboard links and stale thresholds.
- No escalation path — the on-call dead-ends.
- Writing it once and never revisiting it after the system changes.

## Naming & storage

- Directory: `docs/runbooks/`
- Filename: `<service-name>.md` (one runbook per service), or
  `<service>-<scenario>.md` for a focused incident playbook.
- Link each alert definition to its runbook entry.

## Template

Copy `templates/runbook.md` and fill it in.

## Sources

- Skelton-Thatcher run-book template — https://github.com/SkeltonThatcher/run-book-template
- Christian Emmer, "An effective incident runbook template" — https://emmer.dev/blog/an-effective-incident-runbook-template/
- Google SRE Workbook, "On-call" — https://sre.google/workbook/on-call/
