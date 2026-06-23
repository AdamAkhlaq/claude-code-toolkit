---
description: Scaffold an accessible, semantic UI component following frontend best practices.
argument-hint: [component name/description]
disable-model-invocation: true
---

Create a new UI component: **$ARGUMENTS**

Build it to the `frontend` plugin's best practices — apply the relevant skills as
you go: `semantic-html`, `accessibility`, `component-design`, and
`css-architecture` (plus `forms-ux` if it's a form, `i18n` if it has copy).

Steps:

1. **Detect the project's conventions first.** Look at the framework, language
   (TS?), styling approach (CSS modules / Tailwind / styled), file layout, and
   existing components. Match them — don't impose a different stack.
2. **Design the component** per `component-design`: composition over configuration,
   uncontrolled by default (controlled mode only if needed), accessible-by-default
   API.
3. **Build it accessible and semantic:** correct native elements, proper
   labelling, keyboard operability, visible focus, and — only if it's a composite
   widget — the matching WAI-ARIA APG pattern (roles, states, keyboard model).
4. **Style it** with low-specificity CSS and design tokens/custom properties; no
   magic numbers; honour `prefers-reduced-motion`.
5. **Externalise user-facing strings** rather than hard-coding copy.
6. **Add a test** following `frontend-testing` (query by role/label) if the project
   has a test setup.
7. **Write the files** in the project's conventional location and **print the
   paths**, plus a short note of the accessibility decisions you made and anything
   the author should verify manually (e.g. real contrast, screen-reader output).
