# Runbook: <service name>

| | |
|---|---|
| **Owning team** | <team> |
| **On-call / contact** | <rotation, Slack channel, pager> |
| **Repo** | <link> |
| **Runtime / location** | <where it runs> |
| **SLO / SLA** | <targets> |
| **Depends on** | <upstream services> |
| **Depended on by** | <downstream services> |
| **Last reviewed** | YYYY-MM-DD |

## Overview

<What the service does (business + technical) and its place in the system. A small
diagram or dependency sketch helps.>

## Dashboards & Monitoring

- **Dashboard:** <link> — key metrics: <…>
- **Logs:** <link / query>
- **Health check:** <endpoint / command>

## Alerts

### <AlertName>
- **Meaning:** <what fired and why it matters>
- **Severity:** <SEV-n / page vs ticket>
- **Likely causes:** <…>
- **Diagnose:**
  1. <step — with command / dashboard to check>
- **Remediate:**
  1. <step — copy-pasteable command>
  2. <verify it worked: …>
- **Rollback / safe-abort:** <how to undo>

## Common Operational Tasks

### Deploy
```
<command>
```
Verify: <…>

### Roll back
```
<command>
```

### <Restart / scale / drain / rotate secret / backfill>
```
<command>
```
Verify: <…>

## Failure Modes & Troubleshooting

| Symptom | Likely cause | Confirm | Fix |
|---------|--------------|---------|-----|
| <…> | <…> | <…> | <…> |

## Dependencies

| Dependency | If it's down… | How to tell |
|------------|---------------|-------------|
| <upstream> | <impact> | <signal> |

## Recovery / DR

<Backup & restore steps; disaster-recovery procedure; RTO/RPO if defined.>

## Escalation

If the above doesn't resolve it within <time>, escalate to <who / how>.
