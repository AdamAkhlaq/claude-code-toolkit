---
name: diagnose
description: Diagnose a finding from running software (an alert, a log excerpt, a metric that moved, a user complaint, a failing check) without changing anything, and write the diagnosis as a new intent.md so the fix goes through the same gates as any other change. Run with the finding as the argument.
disable-model-invocation: true
argument-hint: "<alert, log excerpt, metric, complaint, or link>"
---

# Diagnose

Something observed in running software needs explaining. This skill explains it and stops. Nothing is changed: no code, no config, no restarts. The output is an `intent.md` that says what was seen, what was found, and what is still unknown, so the work to fix it enters the workflow at the front door like everything else.

The finding: $ARGUMENTS

If the argument is empty, the finding is in the conversation. If it is a link, read it.

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`. The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists. The only writes this skill makes are under `docs/changes/`; say so at the start.

2. **Keep the finding verbatim.** The alert text, the log lines, the metric and its window, the user's words. Quote it. Note when it was observed and by whom.

3. **Establish what is normal.** Before explaining a change, find the baseline: what the metric usually reads, what the log usually says, what the user usually sees. Use the `toolkit:researcher` agent for history: `git log` around the time the finding started, recent changes under `docs/changes/` that touched the area, incidents under `docs/incidents/` with the same shape.

4. **Narrow.** Form at most three hypotheses, each with the evidence that would confirm or rule it out. Check each with reads only: code, configuration in the repo, logs the user provides, commit history. Do not run the system, do not deploy, do not restart, do not change a flag. If confirming a hypothesis needs an action, write it down as a `Fact:` open question for a human to perform, with the exact command and what each outcome would mean.

5. **Decide what this is.**
   - A reproducible bug with a known route: stop here, say so, and hand to `/toolkit:fix-bug` with the reproduction steps. Do not write an intent.
   - A gap, a design flaw, a missing guard, a capacity limit, or an unknown cause: continue.
   - Something that needs an incident record because users were affected: say that `/toolkit:postmortem` writes that record, and continue here with the follow-up work.

6. **Grill once.** Timeline gaps, access to logs you cannot read, and whether the finding is still happening are questions for the user. Run the `toolkit:grilling` skill, one round.

7. **Write the intent.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" new <slug>`. Fill `templates/intent.md`: the finding as Origin; the diagnosis as Problem, with the confirmed cause or the surviving hypotheses and the evidence for each, cited; the Proposed outcome as what will be observably true when it is fixed; Affected users and systems located; Open questions tagged `Fact:` or `Decision:`. Status `proposed`.

8. **Present, then commit with approval.** Show the intent. The user accepts or edits; on accept set `status: accepted`. Stage `docs/changes/<NNNN>-<slug>/intent.md`, show the message `docs(<NNNN>): intent from diagnosis of <finding>` with the trailer `Change: <NNNN>`, and commit only when the user says go. Never push.

9. **Hand off.** One line: `/toolkit:spec <NNNN>` is next, or `/toolkit:postmortem` first if users were affected.

## Rules

- Read-only. The one exception is the intent file. If you catch yourself about to change anything else, that is the fix, and the fix has not been gated.
- A hypothesis without evidence for or against it is listed as open, not as the cause.
- Never guess at a root cause to close the diagnosis sooner. "Unknown, here is what would tell us" is a complete answer.
