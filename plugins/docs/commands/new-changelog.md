---
description: Create a CHANGELOG, or add a release/entry, in Keep a Changelog format.
argument-hint: [version or change summary]
disable-model-invocation: true
---

Create or update the changelog. Argument: **$ARGUMENTS** (a version like `1.2.0`
to cut a release, or a short description of a change to add to `[Unreleased]`).

Follow the `docs:changelog` skill for the Keep a Changelog format rules and
SemVer. The blank template is at `skills/changelog/templates/changelog.md`.

Steps:

1. **Apply the `changelog` skill** to load the format rules and rubric.
2. **If `CHANGELOG.md` doesn't exist:** create it from the template at the repo
   root, then proceed.
3. **Determine the change set:** infer notable, user-facing changes from recent
   commits/PRs since the last release. Curate them — human-readable impact, not
   raw commit messages — and sort into the exact groups Added / Changed /
   Deprecated / Removed / Fixed / Security.
4. **Apply the argument:**
   - If it's a **version**: move the `[Unreleased]` entries under a new
     `## [version] - YYYY-MM-DD` heading (today's date), start a fresh empty
     `[Unreleased]`, and update the reference/compare links. Sanity-check the bump
     against SemVer given the changes (warn if a breaking change is in a non-MAJOR
     bump).
   - If it's a **change description**: add it under the right group in
     `[Unreleased]`.
5. **Write the file** and print a summary of what was added or released.
