---
name: i18n
description: >-
  Apply internationalization (i18n) and localization best practices based on MDN
  and the ECMAScript Intl API. Use when building or reviewing UI that must support
  multiple locales, languages, RTL, or locale-aware formatting, or when the user
  mentions i18n, l10n, Intl, translations, pluralization, or right-to-left text.
---

# Internationalization (i18n)

Designing for multiple languages and locales is far cheaper done up front than
retrofitted. The core moves: get strings out of code, and let the platform's
**`Intl`** API do locale-aware formatting instead of hand-rolling it.

## Key practices

- **Externalise all user-facing strings** into a translation/resource system —
  never hard-code copy in components.
- **Use the `Intl` API** for anything locale-dependent:
  - `Intl.DateTimeFormat` — dates/times.
  - `Intl.NumberFormat` — numbers, currency, percent, units.
  - `Intl.PluralRules` — correct plural categories per language (not just
    one/many).
  - `Intl.RelativeTimeFormat` — "3 days ago".
  - `Intl.ListFormat` — join lists ("a, b, and c") correctly per locale.
  - `Intl.DisplayNames` — localized language/region/currency names.
  - `Intl.Segmenter` — grapheme/word-aware text segmentation (emoji, scripts).
- **Never concatenate** translated fragments or format by hand — word order,
  plurals, and separators differ by locale. Pass full, parameterised messages to
  the formatter.
- **Locale handling** — accept BCP-47 tags with fallbacks (e.g.
  `navigator.languages`); set the document/`Intl` `lang` accordingly.
- **RTL / bidirectional** — design layouts with logical CSS properties (see
  `css-architecture`); test with Arabic/Hebrew; set `dir` correctly.
- **Don't bake formatted output into snapshots/tests** — `Intl` results vary by
  engine/ICU version; assert on inputs or use tolerant matchers.

## Checklist

- [ ] All strings externalised; no hard-coded copy.
- [ ] `Intl.*` used for dates, numbers, currency, plurals, lists, relative time.
- [ ] No manual concatenation of translated text or numbers/dates.
- [ ] BCP-47 locale negotiation with fallbacks; `lang`/`dir` set.
- [ ] Logical CSS properties; RTL tested.
- [ ] Tests tolerant of locale/ICU formatting differences.

## Sources

- MDN Internationalization guide — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Internationalization
- MDN `Intl` reference — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl
- W3C Internationalization — https://www.w3.org/International/
