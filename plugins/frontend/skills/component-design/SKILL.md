---
name: component-design
description: >-
  Apply component design and rendering patterns for UI. Use when designing or
  reviewing components and their APIs, deciding composition vs configuration,
  controlled vs uncontrolled, or a rendering strategy, or when the user mentions
  component patterns, composition, compound components, render props, hooks, or
  CSR/SSR/SSG.
---

# Component Design & Patterns

Good components are **composable, accessible by default, and separate rendering
from state**. These patterns (per patterns.dev) are guidance, not rules — reach
for the simplest one that fits.

## API design principles

- **Composition over configuration** — prefer passing components/children over
  ever-growing config-object props. Compose, don't add a 12th boolean.
- **Separation of concerns** — keep stateful/side-effecting logic apart from pure
  presentation (container vs presentational).
- **Controlled vs uncontrolled** — default to **uncontrolled** (component owns its
  state) for simplicity; offer a **controlled** mode only when the parent needs to
  drive or observe state.
- **Accessible by default** — bake correct roles/labels/keyboard behaviour into the
  component so consumers can't easily make it inaccessible (see `accessibility`).
- **Clear, documented props** — predictable names, sensible defaults, explicit
  required vs optional; expose `aria-*`/`role` where relevant.

## Composition patterns

- **Container / presentational** — a container handles data/state; a presentational
  component just renders props. Improves testability and reuse.
- **Compound components** — a set that shares implicit state and is composed
  together (`<Tabs><Tab/></Tabs>`); great for tightly-coordinated widgets.
- **Render props / slots** — expose rendering control to the consumer.
- **Provider pattern** — share cross-cutting state (theme, auth, locale) to many
  components without prop-drilling.
- **Hooks / composables** — extract and reuse stateful logic; prefer over the older
  HOC pattern (clearer data flow, easier debugging).

## Rendering strategies (pick by use case)

- **CSR** — dynamic, app-like SPAs; weak initial load/SEO without help.
- **SSR** — render per request; good for SEO and fast first paint of dynamic
  content.
- **SSG** — pre-render at build; best for static/content pages.
- **ISR** — static with periodic/on-demand regeneration; hybrid freshness.
- **Streaming SSR** — flush HTML progressively for large pages.
- **Islands** — static page with independently-hydrated interactive regions; ship
  less JS (helps INP — see `performance`).

## Common pitfalls

- Boolean-prop explosion instead of composition.
- Making everything controlled (needless parent state) — or everything global.
- Components that can't be made accessible because behaviour is hard-coded wrong.
- HOC stacks where a hook/composable would be clearer.
- Choosing CSR for content that needs SEO/fast first paint.

## Sources

- patterns.dev (design & rendering patterns) — https://www.patterns.dev/
- Rendering on the web — https://web.dev/articles/rendering-on-the-web
