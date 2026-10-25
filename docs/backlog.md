# Backlog

Follow-ups found while working a change or a review and not yet taken into one. Each line names where it was found. A line leaves this file when a change takes it, in the commit that adds the change's intent or ticket.

- `red-guard` does not read a substitution in double quotes, nested escaped backticks or a substitution in an expanding heredoc body, so `echo "$(git commit -am x)"` commits without the feedback check. `deploy-gate` catches all of these. Found in 0003 T7.
- `_common.find_commit` recurses from every `eval` word, so a call with a chain of `eval` and no commit costs twice as much per word, and `red-guard` reaches its 600 s timeout and blocks. Found in 0003 T6.
- `secret-guard` and `ticket-sync` have no timeout in `hooks/hooks.json` and no `"onFailure": "block"`, so a call they cannot finish reading in time runs, against `CLAUDE.md`'s rule. Found in the third review of 0003.
- `agents/implementer.md:27` loops when a hook blocks a commit on a timeout or a fault rather than a red feedback command. Found in the review of 0002.
- The `setup` skill's step 9 does not name `red-guard`. Found in the review of 0002.
- `CHANGELOG.md`'s `[Unreleased]` compare link points at `v0.4.0` and there is no `[0.5.0]` link. Found in the first review of 0003.
