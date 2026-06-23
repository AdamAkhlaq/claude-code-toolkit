# docs

A Claude Code plugin for writing and reviewing the documents that come up while
coding — grounded in formats from Google, Amazon, and established standards rather
than invented from scratch.

## What's inside

Eight document types, each with a **skill** (the structure + a quality rubric +
bundled templates) and a **`/docs:new-*` command** (scaffolds a fresh doc), plus two
shared **agents** — `doc-reviewer` (deep review of one doc) and `docs-auditor`
(wide audit of the whole repo's docs).

| Type | Skill | Command | Based on |
|------|-------|---------|----------|
| **ADR** — Architecture Decision Record | `adr` | `/docs:new-adr` | Nygard + MADR |
| **RFC** — Design document | `rfc` | `/docs:new-rfc` | "Design Docs at Google", Rust RFC |
| **RCA** — Postmortem | `rca` | `/docs:new-rca` | Google SRE blameless + Amazon COE / 5-Whys |
| **KDD** — Key Decision Document | `kdd` | `/docs:new-kdd` | Decision-record practice |
| **Runbook** — Operational playbook | `runbook` | `/docs:new-runbook` | Skelton-Thatcher, Google SRE on-call |
| **README** — Project front door | `readme` | `/docs:new-readme` | Standard Readme, Make a README, Diátaxis |
| **Changelog** — Release notes | `changelog` | `/docs:new-changelog` | Keep a Changelog + SemVer |
| **PRD** — Product Requirements Document | `prd` | `/docs:new-prd` | Atlassian, SVPG, Lenny's one-pager |

- **Skills** apply automatically when you ask Claude to write or improve one of
  these docs (e.g. "help me write an ADR for choosing Postgres"). They carry the
  canonical structure, a quality rubric, common pitfalls, and the templates.
- **Commands** are explicit: `/docs:new-adr <title>` scaffolds a numbered file
  from the template and fills what it can from context.
- **`doc-reviewer`** is an agent that goes **deep on one doc** — detects its type
  and grades it against the rubric, returning Blocking / Should-fix / Nit feedback.
  Ask: "use doc-reviewer on docs/postmortems/2026-06-01-outage.md".
- **`docs-auditor`** is an agent that goes **wide across the repo** — surveys all
  documentation and reports gaps, staleness, and abandoned items as a prioritized
  worklist. Ask: "run docs-auditor on this repo". It's the corpus-level partner to
  `doc-reviewer`: the auditor finds *where* the problems are; the reviewer fixes a
  given doc *deeply*.

## ADR vs KDD

**ADR** is for architectural/technical decisions that live beside the code
(datastore, API contract, system boundary) — numbered and immutable. **KDD** is for
broader significant decisions (product, process, vendor, org) that record
stakeholders/approvers and a revisit date. When in doubt and it's about how the
system is built, use ADR.

## Storage conventions

| Type | Path | Filename |
|------|------|----------|
| ADR | `docs/adr/` | `NNNN-kebab-title.md` |
| RFC | `docs/rfc/` | `NNNN-kebab-title.md` |
| RCA | `docs/postmortems/` | `YYYY-MM-DD-incident.md` |
| KDD | `docs/decisions/` | `NNNN-kebab-title.md` |
| Runbook | `docs/runbooks/` | `<service>.md` |
| README | repo root | `README.md` |
| Changelog | repo root | `CHANGELOG.md` |
| PRD | `docs/prd/` | `NNNN-kebab-title.md` |

## Install

```
/plugin marketplace add adamakhlaq/claude-code-toolkit
/plugin install docs@claude-code-toolkit
```

Or cherry-pick a single skill by copying its folder (e.g. `skills/adr/`) into
`~/.claude/skills/`.
