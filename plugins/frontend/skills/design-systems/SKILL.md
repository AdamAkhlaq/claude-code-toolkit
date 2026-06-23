---
name: design-systems
description: >-
  Apply design-system best practices — Atomic Design, design tokens, and component
  documentation. Use when building or organising a component library, defining
  tokens/theming, or when the user mentions design systems, atomic design, design
  tokens, Storybook, or a UI kit.
---

# Design Systems

A design system is the single source of truth for a product's UI: a token layer
(the visual decisions) and a component layer (their reusable implementation),
documented so design and engineering stay in sync.

## Atomic Design (structure)

Brad Frost's mental model for composing a UI from small to large:

- **Atoms** — basic building blocks (button, input, label, color, font).
- **Molecules** — small groups of atoms working together (a labelled input + button
  search field).
- **Organisms** — larger, distinct sections (a header, a product card grid).
- **Templates** — page-level layouts wiring organisms together, without real
  content.
- **Pages** — templates filled with real content; where you validate the system.

Use it as a *composition* guide, not a rigid taxonomy to argue over.

## Design tokens

- Tokens are named visual decisions — color, spacing, typography, radius, shadow,
  breakpoints — referenced everywhere instead of hard-coded values.
- Store them in the **W3C Design Tokens (DTCG)** JSON format (`$value`/`$type`) so
  they're tool- and platform-neutral and can be transformed (e.g. via Style
  Dictionary) into CSS custom properties, native, etc.
- **Theming** = swapping token values (light/dark, brand variants) without touching
  components. Pair with the `css-architecture` skill (custom properties + layers).
- Document the *intent* behind token values so future maintainers understand them.

## Components & documentation

- Build components against tokens, **accessible by default** (see `accessibility`
  and `component-design`).
- Use **Storybook** (or similar) to develop and document each component in
  isolation across its states/variants — the living source of truth and a visual
  test surface.

## Checklist

- [ ] Compose UI atoms → molecules → organisms → templates → pages.
- [ ] Define tokens (color/space/type/radius/shadow/breakpoints) in DTCG format.
- [ ] Implement tokens as CSS custom properties; theme by scope.
- [ ] Components consume tokens, never hard-coded values.
- [ ] Document every component and state in Storybook.
- [ ] Record the rationale behind token values.

## Sources

- Atomic Design — Brad Frost — https://atomicdesign.bradfrost.com/chapter-2/
- W3C Design Tokens Community Group — https://www.designtokens.org/
- Storybook — https://storybook.js.org/
