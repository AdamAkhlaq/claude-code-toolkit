# Backlog

Follow-ups found while working a change or a review and not yet taken into one. Each line names where it was found. A line leaves this file when a change takes it, in the commit that adds the change's intent or ticket.

- `red-guard`, `secret-guard` and `ticket-sync` do not read a substitution in double quotes, nested escaped backticks or a substitution in an expanding heredoc body, so `echo "$(git commit -am x)"` commits without the feedback check or the secret scan. `deploy-gate` catches all of these. Found in 0003 T7; kept out of 0003 at T12's gate, for its own change after 0.5.1.
- `_common.find_commit` recurses from every `eval` word, so a call with a chain of `eval` and no commit costs twice as much per word, and `red-guard` reaches its 600 s timeout and blocks. Found in 0003 T6.
- `_common.find_commit` copies the rest of the token list at every token, so `red-guard`, `secret-guard` and `ticket-sync` take time quadratic in a call's words: 20,000 short commands take 6 s and 30,000 heredocs 13 s, the same at `d0fb265`. Under `red-guard`'s 600 s timeout, but the other two have none. Found in 0003 T13.
- The brace budget is per `shell_tokens` call, not per hook call, so a word expanding to about 1,000,000 characters takes 2.3 s in `deploy-gate`: under its 30 s timeout, worth bounding per hook call if it grows. Found in the fourth review of 0003.
- `_common.closing_paren`'s cache is never cleared and is keyed on whole command strings: fine in a one-shot hook process, unbounded if `_common` is ever imported and reused. Found in the fifth review of 0003.
- `secret-guard` and `ticket-sync` have no timeout in `hooks/hooks.json` and no `"onFailure": "block"`, so a call they cannot finish reading in time runs, against `CLAUDE.md`'s rule. Found in the third review of 0003.
- `agents/implementer.md:27` loops when a hook blocks a commit on a timeout or a fault rather than a red feedback command. Found in the review of 0002.
- The `setup` skill's step 9 does not name `red-guard`. Found in the review of 0002.
- On a case-insensitive filesystem, the default on macOS, `GIT tag v1`, `Git tag v1` and zsh's `=GIT tag v1` run `git`, in bash and zsh, but `deploy-gate` matches `gatedCommands` patterns case-sensitively and `find_commit` compares names exactly, so all four hooks miss them. Matching a program word case-insensitively changes how a consumer's patterns apply, so it needs its own decision. Found while working T15 of 0003.
- No proving-test row covers a `((` straight after a `)`, which T16 reads as arithmetic so that zsh's `for i (a)((x=1<<E))` and `foreach i (a)((x=1<<E));end` forms, with `git tag v1` and `E` on the lines after, stay blocked; the fix was probed in bash and zsh but a later change could drop it unnoticed. Found by T16's verifier in 0003.
- `CHANGELOG.md`'s `[Unreleased]` compare link points at `v0.4.0` and there is no `[0.5.0]` link. Found in the first review of 0003.
