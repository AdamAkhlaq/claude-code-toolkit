---
name: forms-ux
description: >-
  Apply form design and validation UX best practices based on the GOV.UK Design
  System and Nielsen Norman Group. Use when building or reviewing forms, inputs,
  validation, or error handling, or when the user mentions form design, labels,
  validation UX, or error messages.
---

# Forms & UX

Forms are where users do the work, so reduce that work. The strongest evidence
base comes from the GOV.UK Design System and Nielsen Norman Group: keep forms
simple, label clearly, and make errors easy to recover from.

## Layout & structure

- **One column.** Multi-column forms cause skipped fields and confused order.
- **Ask only what you need.** Every field has a cost — remove the inessential.
- **Group related fields** logically; for long flows, consider one thing (or one
  group) per page so users focus and recover from errors easily.

## Labels & guidance

- **Always-visible labels**, above the field. **Never use placeholder text as the
  label** — it vanishes on input, has poor contrast, and breaks for AT.
- **Mark optional, not required.** If most fields are required, label the few
  optional ones rather than starring everything.
- **Help text up front**, near the field — don't make users discover requirements
  via errors.
- **Right input types & autocomplete** (`type="email"`, `inputmode`,
  `autocomplete` tokens) for fast, correct entry.

## Validation & errors

- **Validate at the right time** — inline after the user leaves a field (on blur)
  for quick feedback; always re-check on submit.
- **Specific, kind messages** — say what's wrong *and how to fix it* ("Enter a date
  in DD/MM/YYYY"), not "Invalid input".
- **Error summary** at the top for longer/multi-field forms, linking to each
  field.
- **Accessibility** — associate errors with their input (`aria-describedby`),
  announce them (`role="alert"`/live region), and move focus to the first error
  (or the summary) on submit.

## Checklist

- [ ] Single-column layout, minimal fields.
- [ ] Visible labels above inputs; no placeholder-as-label.
- [ ] Optional fields marked (not required ones).
- [ ] Correct `type`/`inputmode`/`autocomplete`.
- [ ] Inline-on-blur + on-submit validation.
- [ ] Specific, actionable error text.
- [ ] Errors associated, announced, and focus-managed; error summary for long
      forms.

## Sources

- GOV.UK Design System — form structure & validation — https://design-system.service.gov.uk/patterns/validation/
- GOV.UK Design System — components — https://design-system.service.gov.uk/components/
- Nielsen Norman Group — web form design — https://www.nngroup.com/articles/web-form-design/
