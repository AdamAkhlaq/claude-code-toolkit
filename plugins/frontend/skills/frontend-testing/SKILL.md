---
name: frontend-testing
description: >-
  Apply frontend testing best practices based on Testing Library and the Testing
  Trophy. Use when writing or reviewing UI tests, choosing what to test, or when
  the user mentions Testing Library, getByRole, the testing trophy, jest-axe,
  Playwright, Cypress, or accessibility testing.
---

# Frontend Testing

Test your UI the way a **user** experiences it, not the way it's implemented.
Tests coupled to internals break on every refactor; tests written against
behaviour and the accessibility tree give durable confidence.

## Guiding principle

> "The more your tests resemble the way your software is used, the more confidence
> they can give you." — Testing Library

Query the DOM the way a user/assistive tech does, in this priority order:

1. **`getByRole`** (optionally with `name`) — primary; also proves the element is
   semantic and accessible.
2. **`getByLabelText`** — form fields.
3. **`getByPlaceholderText` / `getByText` / `getByDisplayValue`**.
4. **`getByTestId`** — last resort, for dynamic/non-semantic content only.

Avoid asserting on implementation details (internal state, class names, component
instances).

## The Testing Trophy — where to invest

- **Static** (TypeScript, ESLint) — catches whole classes of bugs at zero runtime
  cost; the base.
- **Unit** — pure functions and isolated logic.
- **Integration** — components working together with mocked network; the **sweet
  spot** — most confidence per unit of effort and resilience to refactors.
- **E2E** (Playwright / Cypress) — a few **critical user journeys** (login,
  checkout); high value but slow and costlier to maintain, so use sparingly.

## Accessibility testing

- Add **`jest-axe`** / axe-core assertions in integration tests to catch WCAG
  violations early (complements, doesn't replace, manual + screen-reader testing).
- Because Testing Library queries by role/label, accessible components and good
  tests reinforce each other.

## Checklist

- [ ] Prefer `getByRole`/`getByLabelText`; reserve `getByTestId` for the
      untestable.
- [ ] Bulk of suite is **integration** tests with mocked network.
- [ ] E2E only for critical paths.
- [ ] Static analysis (TS + lint) wired into CI as the first gate.
- [ ] axe assertions on key components.
- [ ] Mock external dependencies (network, time, storage) — test your code, not
      third parties.
- [ ] No assertions on internal state or class names.

## Sources

- Testing Library (guiding principles, query priority) — https://testing-library.com/docs/queries/about/
- The Testing Trophy — https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications
- jest-axe — https://github.com/nickcolley/jest-axe
- Playwright — https://playwright.dev/docs/intro
