---
name: rca
description: >-
  Write or improve a Root Cause Analysis / postmortem after an incident or
  outage. Use when the user mentions a postmortem, RCA, incident writeup,
  Correction of Errors (COE), "5 whys", blameless retro, or wants to document
  what broke and how to prevent recurrence.
---

# Root Cause Analysis / Postmortem

A postmortem turns an incident into durable learning: what happened, why the
*system* allowed it, and the specific changes that stop it recurring. The goal is
not a record of blame — it's a record of how the system and process will be
better. Write it while details are fresh (within ~48 hours of resolution).

## The blameless rule (non-negotiable)

Assume everyone acted reasonably with the information they had. The question is
never "why did this person make a mistake?" but "why did the system let this
happen, and why was the right action not the easy one?". Replace person-blaming
language ("Alice deployed a bad config") with system framing ("a config with no
validation reached production because the pipeline had no gate"). Blame kills the
disclosure that makes postmortems valuable.

## When to use it

For any incident worth learning from: an outage, a data issue, a severe
degradation, a near-miss, or a security event. For routine bugs caught in review
or with no production impact, a normal bug ticket is enough.

## Choosing a format

Two bundled templates — both blameless, both action-oriented:

- **Google SRE postmortem** (`templates/postmortem.md`) — the default. Strong on
  impact, timeline, detection, and "what went well / wrong / where we got lucky".
- **Amazon COE** (`templates/coe.md`) — Correction of Errors, structured around
  the **5 Whys** and explicit incident questions (how fast detected, diagnosed,
  mitigated). Use when you want a rigorous, drill-down causal analysis.

Use the 5 Whys (iteratively ask "why?" until you reach a systemic cause, not a
person) within either format. Stop when "why" yields no further useful answer —
not mechanically at five. For tangled incidents, expect multiple contributing
causes, not a single root.

## Canonical structure (Google SRE)

1. **Summary** — what happened, when, and what was affected, in a few sentences a
   stranger could understand. Write it last.
2. **Impact** — quantified: users/requests affected, duration, revenue/SLO burn,
   data loss. Numbers, not adjectives.
3. **Root Causes** — the systemic contributing factors (usually 2–5), reached via
   5 Whys. Systems and process, never individuals.
4. **Trigger** — the specific event that activated the latent fault.
5. **Resolution** — what was done to mitigate and restore service.
6. **Detection** — how you found out (alert? customer? which monitor?) and how
   long that took. Slow/missing detection is itself a finding.
7. **Timeline** — chronological, UTC timestamps: from trigger → detection →
   mitigation → resolution. The factual spine of the doc.
8. **Action Items** — specific, **owned**, **dated**, tracked to closure. Split
   into prevent / detect-faster / mitigate-faster. "Improve monitoring" is not an
   action item; "Add alert on queue depth > N, owner @x, due YYYY-MM-DD" is.
9. **Lessons Learned** — *What went well*, *What went wrong*, *Where we got
   lucky*. The last one surfaces latent risk you haven't paid for yet.

## Quality rubric

A strong postmortem:

- **Is blameless** — systemic framing throughout; no named scapegoat.
- **Quantifies impact** — real numbers and a precise duration.
- **Reaches systemic causes** — 5-Whys depth, not "human error" or
  "misconfiguration" as a stopping point.
- **Has actionable follow-up** — every action item is specific, owned, dated, and
  tracked; they map back to the causes.
- **Covers the whole lifecycle** — not just the bug, but why detection and
  mitigation were as slow as they were.
- **Has an honest "got lucky"** — names the risks that didn't bite this time.

## Common pitfalls

- Blameful language, or a "root cause" of "human error".
- Vague, unowned, undated action items that never get tracked.
- No quantified impact or precise timeline.
- Writing it weeks late, or treating it as a compliance checkbox.
- Stopping at the first cause instead of asking why the system permitted it.

## Naming & storage

- Directory: `docs/postmortems/`
- Filename: `YYYY-MM-DD-short-incident-name.md`.
- Keep an index linking incidents to their action items and closure status.

## Templates

- `templates/postmortem.md` — Google SRE blameless postmortem.
- `templates/coe.md` — Amazon Correction of Errors (5 Whys).

## Sources

- Google SRE Book, "Postmortem Culture: Learning from Failure" — https://sre.google/sre-book/postmortem-culture/
- Google SRE example postmortem — https://sre.google/sre-book/example-postmortem/
- AWS, "Creating a Correction of Errors document" — https://aws.amazon.com/blogs/mt/creating-a-correction-of-errors-document/
