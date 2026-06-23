---
name: semantic-html
description: >-
  Write correct, semantic HTML. Use when building or reviewing markup, choosing
  elements, structuring a document, or when the user mentions semantic HTML,
  markup, document structure, landmarks, headings, or div-soup.
---

# Semantic HTML

Using the right element for the job is the cheapest accessibility, SEO, and
maintainability win there is. Semantic markup gives assistive tech and search
engines meaning for free, and makes code self-documenting. It's also the
foundation the `accessibility` skill builds on — get this right before reaching
for ARIA.

## Why it matters

- **Accessibility** — landmarks, headings, and native controls are announced and
  operable without extra ARIA.
- **SEO** — search engines use structure (headings, `<article>`, `<nav>`) to
  understand and rank content.
- **Maintainability** — `<nav>` says more than `<div class="nav">`.

## Key practices

- **Landmarks** as direct children of `<body>`: `<header> <nav> <main>` (one per
  page) `<aside> <footer>`.
- **Headings** in logical order `<h1>`→`<h6>`, no skipped levels; one main `<h1>`.
  Headings are for structure, not font size — style with CSS.
- **`<button>` vs `<a>`** — `<button>` performs an action; `<a href>` navigates.
  Don't swap them.
- **Content sectioning** — `<article>` for self-contained content, `<section>`
  (with a heading) for a thematic group, `<aside>` for tangential content.
- **Forms** — `<label for>` for every control; group related controls with
  `<fieldset>`/`<legend>`; use the right `input` `type`/`autocomplete`.
- **Lists** — `<ul>`/`<ol>`/`<dl>` for grouped items, not stacks of `<div>`.
- **Tables** — real `<table>` for tabular data with `<thead>`/`<tbody>` and
  `<th scope>`; never for layout.
- **Figures** — `<figure>`/`<figcaption>` for images with captions.

## Common anti-patterns

- **Div soup** — everything a `<div>`/`<span>`; no meaning for AT or search.
- **Clickable divs** — `<div onclick>` instead of `<button>`; not focusable or
  keyboard-operable without reimplementing what the platform gives free.
- **Heading misuse** — skipping levels, multiple `<h1>`s, headings chosen for size.
- **Placeholder-as-label** — disappears on input, fails labelling.
- **Nested interactives** — a link inside a button (or vice versa); invalid and
  unpredictable for screen readers.
- **Landmark nesting** — `<main>`/`<header>` buried inside unrelated containers.

## How to verify

- Inspect the document outline / landmarks (browser a11y tools, screen reader
  rotor) and confirm it reads as a sensible structure with no `<div>` where a
  semantic element belongs.

## Sources

- WHATWG HTML standard (semantics) — https://html.spec.whatwg.org/dev/semantics.html
- MDN semantic HTML / accessibility — https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML
- web.dev Learn HTML — https://web.dev/learn/html/semantic-html
- WebAIM semantic structure — https://webaim.org/techniques/semanticstructure/
