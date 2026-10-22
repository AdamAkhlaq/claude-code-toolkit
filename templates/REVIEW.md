# Review

How this repository's changes are reviewed. The `review` skill runs each pass below in its own context and merges the findings. Edit the passes and the severity rules to fit the project. Keep the nit cap.

## Passes

### 1. Bugs and logic

Does the change do what the code claims, on the happy path and at the edges? Look for off-by-one errors, unhandled nulls, race conditions, swallowed errors, state that is read before it is written, and tests that pass without exercising the change.

### 2. Security

Does the change move trust boundaries? Look for injection, unvalidated input reaching a sink, secrets in code or logs, broadened permissions, new network calls, and dependencies added without a reason.

### 3. Compliance with the spec and plan

Read `spec.md` and `plan.md` for this change. Does the diff implement every requirement, and nothing beyond scope? Are tests at the seams the plan agreed? Is each ticket's `proves` test present and meaningful? Does the pull request state its merge danger honestly?

## Severity

**Important**: breaks behaviour, leaks data, breaches a policy, or diverges from the spec. Every Important finding must be fixed or explicitly waived by the code owner before merge.

**Nit**: everything else. At most five nits per review, chosen by value. Skip anything a formatter, linter or CI check already enforces, and skip generated paths.

## Not reviewed

- Generated files and vendored code.
- Formatting, import order and naming that a linter covers.
- Anything the CI pipeline already fails on.

## Feedback loop

A flag raised in two separate reviews is a pattern. Add a line to `CLAUDE.md` so it stops recurring, and consider an eval case.
