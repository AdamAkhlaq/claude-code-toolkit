---
id: T3
title: Add the pr-sweep skill
blocked_by: [T2]
files: [skills/pr-sweep/SKILL.md, README.md, skills/guide/SKILL.md]
proves: "tests/test_components.py passes with the README listing pr-sweep as shipped in 0.3.0"
status: in-progress
executed_by: single
branch: ticket/0001-T3
---

## Context

Spec: `pr-sweep` "resolves comments and failing checks until the PR is green". It reads the pull request's unresolved review threads and failing checks with `gh`, fixes or answers each comment, repairs each failing check with the feedback command as the judge, and pushes only with the user's go-ahead per push. A comment that asks for a change of design is not fixed in place: it becomes an amendment to the change's artifacts. A flag seen in two reviews goes to `CLAUDE.md` through the `claude-md` discipline. The skill never force-pushes.

Seam: `tests/test_components.py`.

## Acceptance

- The proving test passes.
- `skills/pr-sweep/SKILL.md` is user-invoked, takes an optional pull request number, and stops on a design-level comment, a check that fails twice after a fix, and a merge conflict.
- The guide routes an open pull request with comments or red checks to `pr-sweep`.

## Evidence
