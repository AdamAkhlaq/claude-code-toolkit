# Correction of Errors (COE): <incident name>

- **Date of incident:** YYYY-MM-DD
- **Authors:** <names>
- **Status:** Draft <!-- Draft | In Review | Final -->

> Blameless and action-oriented: focus on systemic correction, not individual fault.

## Summary

<Standalone context for a reader who wasn't involved. Write this last.>

## Impact

<Customers/requests affected, duration, and business/SLO impact — quantified.>

## Timeline

| Time (UTC) | Event |
|------------|-------|
| HH:MM | <event with supporting data> |

## Metrics

<What metric defines the impact, and how it was (or will be) monitored so this is
detected automatically next time.>

## Incident Questions

- **How was it detected, and how long did that take?** <…>
- **How long to diagnose once detected?** <…>
- **How long to mitigate once diagnosed?** <…>
- **What made detection / diagnosis / mitigation slow?** <…>

## Root Cause Analysis — 5 Whys

1. **Why did <the incident> happen?** <answer>
2. **Why did <answer 1> happen?** <answer>
3. **Why did <answer 2> happen?** <answer>
4. **Why did <answer 3> happen?** <answer>
5. **Why did <answer 4> happen?** <systemic root cause>

> Stop when "why" yields no further useful answer. Expect more than one chain for
> tangled incidents.

## Action Items

| Action | Category (prevent / diagnose / mitigate) | Owner | Due | Tracking |
|--------|------------------------------------------|-------|-----|----------|
| <specific, achievable action> | prevent | @owner | YYYY-MM-DD | <link> |

## Related Items

- <links to connected incidents, ADRs, or follow-up docs>
