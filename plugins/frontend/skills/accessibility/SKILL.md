---
name: accessibility
description: >-
  Apply web accessibility (a11y) best practices based on WCAG 2.2 and the WAI-ARIA
  Authoring Practices Guide. Use when building or reviewing UI — components, forms,
  navigation, modals — or whenever the user mentions accessibility, a11y, WCAG,
  ARIA, screen readers, keyboard navigation, or focus management.
---

# Web Accessibility (a11y)

Accessibility means people with disabilities can perceive, operate, and understand
your UI. The authoritative standard is **WCAG 2.2** (W3C, published Oct 2023); the
common legal/target conformance level is **AA**. Build on semantic HTML first and
add ARIA only where the platform falls short.

## The four principles (POUR)

- **Perceivable** — information must be available to the senses (text alternatives,
  contrast, captions).
- **Operable** — all functionality works via keyboard; no traps; enough time.
- **Understandable** — predictable, consistent, with clear errors and help.
- **Robust** — valid markup and correct ARIA so assistive tech can rely on it.

## Practical checklist (target WCAG 2.2 AA)

- **Keyboard:** every interactive element is reachable and operable with Tab /
  Shift+Tab / Enter / Space / arrows; no keyboard traps.
- **Visible focus:** never `outline: none` without a replacement; focus indicator
  has ≥3:1 contrast (WCAG 2.2).
- **Contrast:** text ≥ **4.5:1** (normal) or **3:1** (large: ≥24px, or ≥19px bold).
- **Text alternatives:** meaningful `alt` for informative images; `alt=""` for
  decorative ones.
- **Form labels:** every control has an associated `<label for>`; errors are
  programmatically associated and announced.
- **Landmarks & headings:** use `<header> <nav> <main> <aside> <footer>`; one
  logical `<h1>`→`<h6>` order with no skipped levels.
- **Focus management:** modals trap focus and restore it on close; route changes
  move focus sensibly.
- **Reduced motion:** honor `prefers-reduced-motion`; nothing flashes >3×/second.
- **Target size (2.2):** pointer targets ≥ **24×24 CSS px** (AA) with adequate
  spacing.
- **Label in name:** an element's visible label is part of its accessible name.
- **Dragging alternative (2.2):** any drag action has a single-pointer alternative.

## The first rule of ARIA

**Don't use ARIA if a native element will do.** A `<button>` beats
`<div role="button">` — it's focusable, keyboard-operable, and announced for free.
Reach for ARIA only when no semantic element exists, and follow the APG pattern
exactly (roles, states, and the keyboard interaction it specifies).

## ARIA component patterns

For composite widgets, follow the WAI-ARIA Authoring Practices Guide rather than
inventing roles. It documents the canonical keyboard + ARIA behaviour for: dialog
(modal) and alertdialog, menu / menu button, tabs, accordion, disclosure,
combobox, listbox, checkbox / radio group, slider, spinbutton, tooltip, tree /
treegrid, table / grid, breadcrumb, carousel, toolbar, and more. Match the
expected keyboard model (e.g. arrow-key navigation within a composite, not Tab).

## Common pitfalls

- Clickable `<div>`s/`<span>`s instead of `<button>`/`<a>` — no keyboard, no role.
- Removing focus outlines for aesthetics with nothing in their place.
- Placeholder text used as the only label (disappears on input, low contrast).
- Color as the sole carrier of meaning (e.g. red = error with no text/icon).
- ARIA that lies — wrong roles or stale `aria-expanded`/`aria-selected` state.
- Skipped heading levels for visual sizing instead of CSS.

## How to verify

- Tab through the whole UI with no mouse; confirm order and visible focus.
- Run an automated check (axe / Lighthouse) — catches ~30–40%; the rest needs
  manual + screen-reader testing (VoiceOver, NVDA).
- Check contrast with a contrast checker; test at 200% zoom.

## Sources

- WCAG 2.2 — https://www.w3.org/TR/WCAG22/
- What's new in WCAG 2.2 — https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- WAI-ARIA Authoring Practices Guide (patterns) — https://www.w3.org/WAI/ARIA/apg/patterns/
- MDN accessibility — https://developer.mozilla.org/en-US/docs/Web/Accessibility
- WebAIM contrast & checklist — https://webaim.org/standards/wcag/checklist
