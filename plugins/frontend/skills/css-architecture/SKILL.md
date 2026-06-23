---
name: css-architecture
description: >-
  Apply modern CSS and styling-architecture best practices. Use when writing or
  reviewing CSS/styles, choosing a methodology, building responsive layouts, or
  when the user mentions CSS architecture, cascade layers, container queries,
  specificity, design tokens, BEM, Tailwind, or responsive design.
---

# CSS Architecture & Modern CSS

Maintainable CSS today is **low-specificity, layered, and component-centric**,
using native browser features instead of fighting the cascade. The goals: a
predictable cascade, responsive *components* (not just pages), and tokens as the
single source of visual truth.

## Modern CSS worth using

- **Cascade layers (`@layer`)** — order styles into named layers
  (`@layer reset, base, layout, components, utilities`) so precedence is explicit
  and specificity wars disappear.
- **Container queries (`@container`)** — style a component by *its container's*
  size, making it truly reusable regardless of where it's placed.
- **`:has()`** — style a parent based on its descendants (the long-missing
  "parent selector").
- **Logical properties** — `margin-inline`, `padding-block`, `inset-*` for
  writing-mode / RTL-agnostic layout.
- **Custom properties** — design tokens via `var(--token)`; scope for theming.
- **`clamp()` / fluid type** — responsive sizing without breakpoints.
- **Subgrid** and **native nesting** — nested layouts and co-located rules.

## Managing the cascade & specificity

- Keep selectors **low-specificity** — prefer a single class or element; let
  `@layer` order, not specificity, decide precedence.
- Use **`:where()`** (0 specificity) for resets and library styles so they're
  trivially overridable.
- Avoid `!important`, deep descendant chains, and ID selectors for styling.
- Audit specificity in DevTools; aim for a flat, low average.

## Choosing a methodology

- **BEM** — explicit `block__element--modifier` naming; good for large,
  multi-team codebases and preprocessor setups. Verbose.
- **Utility-first (e.g. Tailwind)** — compose in markup from a constrained token
  set; fast, prevents design drift, ships only used utilities. Markup-heavy;
  needs build tooling.
- **CUBE CSS** — Composition → Utility → Block → Exception; a middle path that
  leans on the cascade and treats utilities as exceptions.

They're not exclusive: a common modern setup is **cascade layers + custom-property
tokens + container queries**, with a methodology layered on top for naming.

## Responsive design

- **Mobile-first**; enhance up.
- Prefer **fluid** layouts (`clamp()`, flexible grid/flex, intrinsic sizing:
  `min-content`/`fit-content`) over many fixed breakpoints.
- Use **container queries** for component breakpoints instead of viewport media
  queries where the component should adapt to its slot.
- Responsive images: `srcset`/`sizes`, modern formats.

## Maintainability checklist

- [ ] Organise styles with `@layer` in an explicit order.
- [ ] Define color/space/type/shadow tokens as custom properties; theme by scope.
- [ ] Keep specificity low; `:where()` for overridable base/library styles.
- [ ] Logical properties for i18n/RTL readiness.
- [ ] Container queries for reusable component responsiveness.
- [ ] No `!important` / ID-based styling; document token naming.

## Sources

- MDN CSS cascade & layers — https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascade
- MDN container queries — https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_size_and_style_queries
- MDN custom properties — https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties
- web.dev Learn CSS — https://web.dev/learn/css
