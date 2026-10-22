---
name: postmortem
description: Write a blameless incident record under docs/incidents/ for something that affected users or broke production, turn each follow-up into an intent, and turn the class of failure into an eval case so it is caught next time. Run with the incident description, a link, or the diagnosis change id.
disable-model-invocation: true
argument-hint: "<incident description, link, or change id>"
---

# Postmortem

An incident is over when three things exist: a record of what happened, intents for the work it exposed, and an eval case that would catch the same class of failure before it ships again. Nothing here assigns blame. The record describes a system that allowed the failure, and the follow-ups change the system.

The incident: $ARGUMENTS

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`. The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists and `docs/incidents/` exists; if not, `/toolkit:setup` creates it. If the argument is a change id whose intent came from `diagnose`, read that intent first; it is the diagnosis and most of the timeline.

2. **Gather the facts.** Use the `toolkit:researcher` agent for the commits, deploys and changes in the window, and read whatever the user provides: alerts, logs, chat excerpts, the fix if one was made. Every fact goes in with its source and time. Where the order of events is unclear, that is a question, not a guess.

3. **Grill for the timeline.** The gaps only people can fill: when it was first noticed, by whom, what was tried, when it was resolved, how many users and which ones. Run the `toolkit:grilling` skill, one round, two at most.

4. **Write the record** at `docs/incidents/<YYYY-MM-DD>-<slug>.md` from `templates/incident.md`:
   - **Summary**: three sentences. What broke, for whom, for how long.
   - **Impact**: users, requests, data, money, trust, in numbers where there are numbers.
   - **Timeline**: one line per event, timestamped, from the first contributing change to the all-clear. Detection, diagnosis and mitigation times called out.
   - **Root cause**: the condition that, had it not held, would have prevented the incident. One paragraph. If more than one, the record says so.
   - **Contributing factors**: what made it possible, likelier or worse: missing tests, missing alerts, a gate skipped, a one-way door run without a human.
   - **What went well**: what limited the damage.
   - **Follow-ups**: a numbered list. Each is either work (becomes an intent), a rule (becomes a `CLAUDE.md` line through the `toolkit:claude-md` discipline, or a policy skill), or an eval case.
     Blameless in every line: systems and conditions, not people.

5. **Create the follow-up intents.** For each follow-up that is work, run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" new <slug>` and write an `intent.md` whose Origin is the incident record, with status `proposed`. Link each from the record's Follow-ups list by change id.

6. **Create the eval case.** The class of failure, not the instance: a prompt that would lead an agent toward the same mistake, and graders that catch it. Write it under `evals/<case-name>/` in the format `templates/eval-case.md` shows: a `prompt.md` and at least one deterministic grader. Link it from the record. `/toolkit:eval-case` does the same for a task that is not an incident.

7. **Present at the gate.** Show the record, the intents and the eval case. The user accepts or edits. On accept, set the record's `status` to `reviewed` and `owner` to the user's name.

8. **Commit, with approval.** Stage the record, the new change folders and `evals/`. Message `docs(incident): <slug>` with a `Change:` trailer per follow-up intent. Commit only when the user says go. Never push.

9. **Hand off.** One line per follow-up intent: `/toolkit:spec <NNNN>` when accepted.

## Rules

- Blameless. If a sentence names a person as the cause, rewrite it to name the condition that let their action cause harm.
- Every follow-up has a form: an intent, a rule, or an eval case. A follow-up that is none of these is a wish and is deleted.
- The record is an artifact: amended with dated sections after the gate, never rewritten.
