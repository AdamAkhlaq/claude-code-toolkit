---
name: changelog
description: >-
  Create or update a CHANGELOG following the Keep a Changelog format and
  Semantic Versioning. Use when the user wants to write a changelog, add release
  notes, record what changed in a release, or maintain an [Unreleased] section.
---

# Changelog

A changelog is a curated, human-readable list of notable changes per release. It
exists so a *person* — a user deciding whether to upgrade, a teammate auditing a
release — can see what changed without reading the git log. Write entries for
humans, not machines: explain the impact, not the implementation.

## When to use it

For any project with releases or versioned consumers. Maintain a top
`[Unreleased]` section as you merge changes, then stamp it with a version and date
at release time. Don't auto-generate it from commit messages — curation is the
point.

## Format rules (Keep a Changelog)

These are rigid — follow them exactly:

- File is `CHANGELOG.md` at the repo root; title is `# Changelog`, followed by a
  note that it follows Keep a Changelog and Semantic Versioning.
- Keep an **`## [Unreleased]`** section at the top for changes not yet released.
- Releases are listed **newest first** (reverse chronological).
- Each release heading is **`## [x.y.z] - YYYY-MM-DD`** (ISO 8601 date).
- Within a release, group entries under these **exact** change types, only the
  ones that apply:
  - **Added** — new features.
  - **Changed** — changes to existing functionality.
  - **Deprecated** — soon-to-be-removed features.
  - **Removed** — features removed in this release.
  - **Fixed** — bug fixes.
  - **Security** — vulnerabilities addressed.
- Version numbers follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`): breaking
  change → MAJOR, backwards-compatible feature → MINOR, backwards-compatible fix →
  PATCH.
- Note **yanked** releases as `## [x.y.z] - YYYY-MM-DD [YANKED]`.
- Make versions linkable with reference links at the bottom (compare URLs).

## Quality rubric

A strong changelog:

- **Is for humans** — each entry states user-facing impact in plain language, not
  a commit hash or internal detail.
- **Uses the exact change-type groups** consistently across releases — no ad-hoc
  categories.
- **Is SemVer-aligned** — the version bump matches the nature of the changes
  (breaking vs feature vs fix).
- **Keeps `[Unreleased]` current** — changes land there as they merge, not in a
  scramble at release time.
- **Links versions** — every version is a clickable compare/tag link.

## Common pitfalls

- Dumping raw `git log` output — unreadable and not curated.
- Inventing categories instead of the six standard ones.
- Missing or non-ISO dates; releases out of order.
- A version bump that doesn't match SemVer (e.g. a breaking change in a PATCH).
- Forgetting to move `[Unreleased]` entries into the new version on release.

## Naming & storage

- `CHANGELOG.md` at the repo root.

## Template

Copy `templates/changelog.md` and fill it in. On release, rename `[Unreleased]`
to the new version + date and start a fresh empty `[Unreleased]`.

## Sources

- Keep a Changelog v1.1.0 — https://keepachangelog.com/en/1.1.0/
- Semantic Versioning — https://semver.org/
