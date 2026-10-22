---
id: T5
title: PHILOSOPHY, the executor and the skills name red-guard as the enforcer
blocked_by: [T4]
files:
  [
    PHILOSOPHY.md,
    agents/implementer.md,
    skills/verify/SKILL.md,
    skills/fix-bug/SKILL.md,
    tests/test_components.py,
  ]
proves: "in tests/test_components.py, a new test asserts every hook script under hooks/scripts/ is linked in the Enforced by column of PHILOSOPHY.md's At a glance table, and it passes"
status: todo
---

## Context

Spec requirements 15 and 16. Plan approach step 5. Repo `CLAUDE.md`: the "Enforced by" column must stay accurate.

Write the test first: it fails today on both `red_guard` and `ticket_sync`, because `ticket-sync` was never placed in the table. Then:

- `PHILOSOPHY.md`: add a linked `red-guard` to the "Skills advise, hooks enforce" row and add "red commits" to that section's list of what hooks enforce. Add a linked `ticket-sync` to the "Artifacts are tool-agnostic" row: it keeps the ticket files, the source of truth, in step with the code they describe. Run prettier on the file; the table is aligned.
- `agents/implementer.md` steps 6 and 7: the `red-guard` hook stops a commit while the feedback command is red.
- `skills/verify/SKILL.md`: the same, in a sentence where the rule is stated.
- `skills/fix-bug/SKILL.md` step 7: the failing-test commit passes `red-guard` because it changes only test files and workflow documents; staging anything else with it will be blocked.

Hook names in prose are the hyphenated ones (`red-guard`); script names use underscores. Map one to the other the way `test_every_hook_script_is_registered_and_documented` does.

Seam: the repo's shape rules, `tests/test_components.py`.

## Acceptance

- The proving test passes, and it failed before the PHILOSOPHY edit, for `red_guard` and `ticket_sync`.
- The existing PHILOSOPHY link tests still pass.
- `python3 -m unittest discover -s tests` passes.

## Evidence
