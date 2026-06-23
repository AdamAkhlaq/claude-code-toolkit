# frontend

A Claude Code plugin of **framework-agnostic** frontend best practices, grounded in
credible sources (W3C, web.dev/Google, MDN, OWASP, patterns.dev, Testing Library,
GOV.UK, Brad Frost) rather than invented. The skills apply automatically when you
build or review UI; the agents audit existing code.

## Skills

| Skill | Covers | Based on |
|-------|--------|----------|
| `accessibility` | WCAG 2.2 AA, ARIA APG patterns, keyboard, focus, contrast | W3C WCAG 2.2, WAI-ARIA APG |
| `performance` | Core Web Vitals (LCP/INP/CLS), loading, bundles | Google web.dev |
| `semantic-html` | Right elements, landmarks, headings, no div-soup | WHATWG, MDN |
| `css-architecture` | Cascade layers, container queries, tokens, methodologies | MDN, web.dev |
| `component-design` | Composition, compound components, rendering strategies | patterns.dev |
| `frontend-security` | XSS, CSP, sanitization, SRI, cookies | OWASP Cheat Sheets |
| `frontend-testing` | Testing-Library queries, Testing Trophy, a11y tests | Testing Library |
| `forms-ux` | Labels, validation UX, error handling | GOV.UK, Nielsen Norman Group |
| `design-systems` | Atomic Design, design tokens, Storybook | Brad Frost, W3C DTCG |
| `i18n` | `Intl` API, externalised strings, RTL | MDN, ECMAScript Intl |
| `seo` | Titles/meta, structured data, crawlability | Google Search Central |

## Commands

- **`/frontend:new-component`** — scaffold an accessible, semantic component to your
  project's conventions.
- **`/frontend:a11y-check`** — run a WCAG 2.2 AA accessibility check (delegates to
  `a11y-auditor`).
- **`/frontend:audit`** — full audit: a11y + performance + review, synthesized into
  one report.

## Agents

- **`frontend-reviewer`** — reviews UI code across *all* dimensions (a11y, perf,
  semantics, CSS, security, component design, i18n/SEO) at once.
- **`a11y-auditor`** — deep accessibility-only pass against WCAG 2.2 + ARIA APG.
- **`perf-auditor`** — deep Core Web Vitals + bundle/asset pass.

Use `frontend-reviewer` for a broad pre-merge review; reach for the focused
auditors when you want depth in one area.

## Scope

Deliberately **framework-agnostic** — these are web-platform fundamentals that hold
across React, Vue, Svelte, or vanilla. A framework-specific layer (e.g. a `react`
set) can be added later as its own plugin.

## Install

```
/plugin marketplace add adamakhlaq/claude-code-toolkit
/plugin install frontend@claude-code-toolkit
```

Or cherry-pick a single skill by copying its folder (e.g. `skills/accessibility/`)
into `~/.claude/skills/`.
