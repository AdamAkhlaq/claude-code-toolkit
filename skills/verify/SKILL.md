---
name: verify
description: Run the project's feedback command and record its quoted output as evidence that work is done. Use before claiming a ticket, fix or task is complete, before committing code, when asked whether something works, or when a ticket's Evidence section is empty. Done means quoted output, never a belief.
---

# Verify

Work is done when the feedback command has run, after the last edit, and its output says so. Nothing else counts: not a passing run from earlier, not a test that was run in your head, not a summary of what the output probably was.

## The command

The feedback command is `feedbackCommand` in `.claude/toolkit.json`. Read it from there. If the key is empty or the file is missing, say so and ask the user which single command runs the project's checks and exits non-zero on failure. Do not invent one, and do not substitute a narrower command because it is faster.

Run it exactly as configured, from the project root, with no flags added. If the project also has a faster command for the one test that proves the current work, run that first for the quick signal, then run the feedback command for the record.

## The evidence

Quote, never paraphrase. The record is:

```
### Evidence <date> <time>
Command: <the command as run>
Exit code: <n>
<the last 30 lines of output, verbatim, in a fenced block>
```

Keep the lines that carry the verdict: counts of passed and failed, the names of failing tests, the final status line. Drop progress noise above them if the output is long, and say how many lines were dropped.

Where the evidence goes:

- A ticket: under its `## Evidence` heading, replacing any earlier evidence from this execution. The verifier's verdict goes beneath it later; never write a verdict for your own work.
- A bug fix without a ticket: in the commit message body, or in the message to the user.
- Anything else: in the message to the user, in a fenced block.

## When it fails

Report the failure with the quoted output and stop claiming completion. Then:

- Fix the code, not the test. If you believe the test is wrong, say so with the reason and let the user decide. If `.claude/.tests-locked` exists, test edits are blocked anyway.
- If the failure is in a test unrelated to the current work, say so, show it, and do not skip or mark it. A red suite is red.
- Do not commit while red. The `red-guard` hook enforces this: it runs the feedback command before every `git commit` that changes more than workflow documents and test files, and blocks the commit while it is red.
- Re-run after the fix. The evidence that counts is the last run.

## Rules

- Evidence is stale the moment a file changes. Any edit after the run means running again.
- Never report a result you did not see in this session.
- Never edit, skip, mark as expected-failure, or delete a test to reach green.
- The word "done" in a message to the user is always followed, in that message or the ticket, by the quoted output.
