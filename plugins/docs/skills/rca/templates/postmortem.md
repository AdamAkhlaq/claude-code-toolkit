# Postmortem: <incident name>

- **Date of incident:** YYYY-MM-DD
- **Authors:** <names>
- **Status:** Draft <!-- Draft | In Review | Final -->
- **Severity:** <SEV-n>

> Blameless: this document describes how the *system and process* allowed the
> incident, not who to blame. Frame every cause systemically.

## Summary

<What happened, when, and what was affected — a few sentences a stranger could
follow. Write this last.>

## Impact

- **Duration:** <start–end, UTC> (<total>)
- **Users / requests affected:** <quantified>
- **SLO / revenue / data impact:** <quantified>

## Root Causes

<The systemic contributing factors, reached via 5 Whys. Systems and process, not
individuals.>

## Trigger

<The specific event that activated the latent fault.>

## Detection

<How the incident was detected and how long that took. If detection was slow or
manual, that is itself a finding.>

## Resolution

<What was done to mitigate and fully restore service.>

## Timeline (UTC)

| Time | Event |
|------|-------|
| HH:MM | <trigger> |
| HH:MM | <detection> |
| HH:MM | <mitigation> |
| HH:MM | <resolution> |

## Action Items

| Action | Type (prevent / detect / mitigate) | Owner | Due | Tracking |
|--------|-----------------------------------|-------|-----|----------|
| <specific action> | prevent | @owner | YYYY-MM-DD | <link> |

## Lessons Learned

- **What went well:** <…>
- **What went wrong:** <…>
- **Where we got lucky:** <latent risks that didn't bite this time>
