---
name: claude-md
description: Create, trim or extend a CLAUDE.md so the same mistake is not made twice. Use when the user corrects you on something they have corrected before, when a review raises a flag that was raised in an earlier review, when a CLAUDE.md is missing, bloated or describes things the code already shows, or when the user asks to remember a rule for the project. CLAUDE.md is memory for what cannot be learned from the code.
---

# CLAUDE.md

`CLAUDE.md` is read at the start of every session. It holds what a capable engineer joining the project could not work out from the code and the docs: the commands, the conventions that are enforced but unwritten, the places not to touch, and the corrections that keep recurring.

## What goes in

- **Commands.** Build, test, lint, run, and the one feedback command, each on one line with what healthy output looks like if that is not obvious.
- **Workflow rules.** How branches, commits, changes and releases work here, when they differ from the default.
- **Never.** Things that must not be done, one line each, with the reason in a clause when the reason is not obvious.
- **Repeated corrections.** A correction the user has given twice, or a review flag raised in two separate reviews, becomes one line. The first time, remember it for the session and say that a repeat will go in `CLAUDE.md`. The second time, add it.

## What stays out

- Anything derivable by reading the code: directory layout, what a module does, how a function works. It drifts the moment the code changes.
- Explanations, philosophy and rationale longer than a clause. A link to a doc is fine.
- Per-task state. That belongs in the change's artifacts.
- Secrets, hostnames, credentials.

## Form

- Imperative, one rule per line, bullets under short headings. No prose paragraphs.
- Specific enough to act on. "Use the nvm `claude` binary, the one on PATH is a work wrapper" beats "be careful which claude you run".
- Under about 60 lines. When it grows past that, trim: merge duplicates, delete anything the code or a linter now enforces, and move long explanations to a doc that the file links.
- Nested `CLAUDE.md` files scope to their directory. Put a line in the narrowest scope it applies to.

## How to change it

1. Read the current file in full, including any nested ones under the paths involved.
2. Draft the exact line, or the exact lines to remove. Show the diff to the user.
3. Apply it only when the user agrees. Never commit it yourself; the user commits with their next change.
4. If there is no `CLAUDE.md` at all, say so and suggest running `/init`, then `/toolkit:setup`, which adds the definition of done. Do not write one from scratch here unless the user asks.
