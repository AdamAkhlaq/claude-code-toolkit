---
name: fix-bug
description: Fix a bug the disciplined way: reproduce it as it was reported, narrow the reproduction to the fastest test that fails for the same reason, lock the tests, fix the code, verify, unlock. Leaves a change folder with the report as origin and the regression test as its one ticket. Run with the bug report, a failing test, or an issue link as the argument.
disable-model-invocation: true
argument-hint: "<bug report, failing test, or issue link>"
---

# Fix bug

No bug is fixed until it has been reproduced the way it was reported. A fix for a bug you have not seen is a guess, and reproducing it the user's way finds the real cause rather than a nearby one. Once seen, the bug is narrowed to the fastest test that fails for the same reason, that test is committed and locked, and only then is code changed.

The report: $ARGUMENTS

If the argument is empty, the report is in the conversation. If it is a path, a test name or a URL, read it.

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/`. The graph tool is `${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph`.

## Steps

1. **Preconditions.** `.claude/toolkit.json` exists with a `feedbackCommand`; without it, stop and point at `/toolkit:setup`. Note the branch and whether the tree is clean. If `.claude/.tests-locked` already exists, another fix is in progress: say so and stop.

2. **Keep the report verbatim.** Quote it as it arrived: the user's words, the stack trace, the issue text, the failing test's output. Do not tidy it.

3. **Reproduce as reported.** Follow the route the reporter took, as closely as the environment allows: the same command, inputs, data shape, user flow, and the same entry point, end to end if that is how they hit it. Use the `toolkit:researcher` agent to locate the code on that route when it is not obvious. Record exactly what you ran and what you saw, quoted. If you cannot reproduce it, say so with what you tried and run the `toolkit:grilling` skill for what is missing: environment, version, data, timing. Do not move on to a fix without a reproduction; a bug that cannot be reproduced gets an intent, not a fix.

4. **Narrow to the fastest failing test.** From the reproduction, walk inward to the nearest seam where a fast test still fails for the same reason: the same wrong value, the same exception, the same missing behaviour. Write that test in the project's test suite with a name that says what the bug was. Run it and quote the failure. If the project has no seam near enough and only an end-to-end test can show the bug, write that one and say why.

5. **Gate: confirm the test is the bug.** Show the user the reproduction, the test, and its failure output side by side. Ask one question: does this test capture the bug as you hit it? On yes, continue. On no, the test is wrong, not the report: go back to step 3.

6. **Record the change.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/toolkit-graph" new fix-<slug>`. Write `intent.md` from `templates/intent.md` with the report as Origin, the reproduction as Problem, and the outcome "the regression test passes and the reported route behaves as expected". Write one ticket `tickets/T1-<slug>.md` whose `proves` is the regression test and whose `files` are the test and the files you expect to change. A bug fix needs no spec or plan; note that in the intent.

7. **Commit the failing test and lock.** Stage the test, the intent and the ticket. Commit as `test(<scope>): reproduce <the bug>` with the trailers `Change: <NNNN>` and `Ticket: <NNNN>-T1`, after the user's go-ahead. Then create `.claude/.tests-locked`. From here the `lock-tests` hook blocks every edit to a test file, so the fix cannot pass by changing the test.

8. **Fix.** Set the ticket to `in-progress`. Change the code, as little of it as makes the test pass and the reported route behave. Resist fixing other things you notice; record them in the report. If, while fixing, you become convinced the test is wrong, say so with the reason and ask the user to unlock with `rm .claude/.tests-locked`; do not work around the hook.

9. **Verify.** Use the `toolkit:verify` skill: run the feedback command, quote the output into the ticket's Evidence. Then re-run the original reproduction from step 3 the reporter's way and quote that too. Both must pass. Then remove `.claude/.tests-locked`.

10. **Commit the fix, with approval.** Stage the code and the ticket. Message `fix(<scope>): <what was wrong>` with a body naming the root cause in a sentence, and the trailers. Set the ticket to `done` only after a `toolkit:verifier` agent has passed it; in a single-session fix, start the verifier now with the ticket path and the current directory.

11. **Learn.** If the root cause is a class of mistake that has come up before in this repo, in a review or a correction, apply the `toolkit:claude-md` discipline. If it caused an incident, say that `/toolkit:postmortem` arrives in 0.4.0 and record the follow-up in the intent's Open questions.

12. **Report.** The root cause in a sentence, the test that guards it, the evidence, and the next step: push and open a pull request, or `/toolkit:review` once it exists.

## Rules

- Reproduce before fixing. No reproduction, no fix.
- The regression test is committed before the fix and stays forever.
- Never edit, skip or weaken a test while the lock exists. The hook enforces it; the rule is the reason.
- Never push. The user pushes.
