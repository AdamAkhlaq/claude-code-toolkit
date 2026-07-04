---
name: readme
description: >-
  Write or improve a project README. Use when the user wants to create, rewrite,
  or review a README — the front-door doc explaining what a project is, why it
  exists, and how to install and use it. Follows the Standard Readme spec.
---

# Project README

The README is the front door to a project and usually the most-read doc you'll
write. Within the first screen a reader should learn **what this is**, **why it
exists**, and **how to use it**. Write for a newcomer who arrived with zero
context; optimise for being skimmable in ~30 seconds.

## When to use it

For any repo, package, or service that another human (including future you) will
open. Keep the README focused on orientation and getting started — push deep
material elsewhere (see *Scope & Diátaxis* below).

## Canonical structure

Based on the Standard Readme spec. Sections **must appear in this order**; omit
optional ones, but don't reorder. Required sections are marked.

1. **Title** *(required)* — the project name as an H1.
2. **Badges** *(optional)* — build, version, license status.
3. **Short description** *(required)* — one paragraph: what it is and what it's
   for, immediately under the title.
4. **Long description** *(optional)* — more detail if the short one isn't enough.
5. **Table of contents** *(required unless short)* — links to the level-2 headings.
6. **Security** *(optional)* — security-sensitive setup, if relevant.
7. **Background** *(optional)* — context and motivation: the problem it solves,
   why it exists, prior art.
8. **Install** *(required)* — exact, runnable steps to install it. Should work
   verbatim.
9. **Usage** *(required)* — the smallest runnable example, then common usage.
   Show, don't just tell.
10. **API** *(optional)* — interface reference, or a link to it.
11. **Maintainers** *(optional)* — who owns it.
12. **Contributing** *(required)* — how to contribute / where the guide lives.
13. **License** *(required)* — the exact license.

## Scope & Diátaxis

Keep the README to orientation + getting started. When a project needs deeper
docs, **don't bloat the README** — split content by reader need using the
[Diátaxis](https://diataxis.fr) model and link out to it:

- **Tutorial** — learning-oriented, hand-holding first project.
- **How-to guide** — task-oriented recipe for one goal.
- **Reference** — dry, accurate technical description (API, config).
- **Explanation** — the *why*: design, background, trade-offs.

These serve different needs and shouldn't be mixed into one page (or crammed into
the README). The README links to them; it isn't all of them.

## Quality rubric

A strong README:

- **Answers "what / why / how" on the first screen** — no scrolling to learn what
  the project is.
- **Has a runnable Install and Usage** — copy-pasteable steps and a minimal
  working example, not just description.
- **States honest scope** — what it does and what it deliberately doesn't.
- **Is skimmable** — clear headings, short paragraphs, a TOC when long.
- **Is current** — install/usage match the actual code; no dead links.

## Common pitfalls

- A title and a wall of prose with no quick "what is this?".
- Install/usage steps that don't actually run, or assume hidden setup.
- Everything dumped into the README instead of linked reference/how-tos.
- Missing license or contributing guidance.

## Naming & storage

- `README.md` at the repo root (or the relevant package/subdirectory root).
- Supporting docs under `docs/` (organised per Diátaxis when they grow).

## Template

Copy `templates/readme.md` and fill it in.

## Sources

- Standard Readme spec — https://github.com/RichardLitt/standard-readme/blob/main/spec.md
- Make a README — https://www.makeareadme.com/
- Diátaxis (documentation framework) — https://diataxis.fr/
