---
name: seo
description: >-
  Apply technical SEO best practices based on Google Search Central. Use when
  building or reviewing pages for search discoverability, or when the user mentions
  SEO, meta tags, structured data, schema.org, sitemaps, canonical URLs, or
  crawlability.
---

# Technical SEO

Technical SEO is making content **discoverable, crawlable, and understandable** to
search engines — and it overlaps heavily with accessibility and performance done
well. This skill covers the engineering side, not content strategy.

## Key practices

- **Semantic structure** — proper heading hierarchy and semantic elements
  (`<nav>`, `<main>`, `<article>`) help engines understand the page (see
  `semantic-html`).
- **Titles & meta** — a unique, descriptive `<title>` (~50–60 chars) and
  `<meta name="description">` (~150–160 chars) per page.
- **Structured data** — add schema.org markup in **JSON-LD** for eligible content
  (Article, Product, FAQ, Breadcrumb…) to enable rich results.
- **Crawlability** — let Googlebot fetch CSS/JS/images; manage with `robots.txt`;
  provide a valid `sitemap.xml` and submit it in Search Console.
- **Canonical URLs** — set `rel="canonical"` to the preferred URL where duplicates
  or query-param variants exist.
- **Mobile-first** — Google indexes the mobile rendering; ensure responsive layout
  and tap-friendly targets.
- **Core Web Vitals** — LCP/INP/CLS are ranking signals; see the `performance`
  skill.
- **Descriptive links & alt text** — meaningful link text and image `alt` help
  both SEO and accessibility.
- **`hreflang`** — for multilingual/multiregional sites, declare language/region
  variants (pairs with the `i18n` skill).
- **HTTPS** everywhere.

## Note on rendering

If the site is client-rendered (CSR), confirm content is actually rendered for
crawlers — prefer SSR/SSG/prerendering for content that must rank (see
`component-design` rendering strategies).

## Checklist

- [ ] Unique `<title>` and meta description per page.
- [ ] Semantic headings/structure.
- [ ] JSON-LD structured data for eligible content types.
- [ ] Crawlable resources; valid sitemap; sensible `robots.txt`.
- [ ] Canonical URLs set.
- [ ] Responsive/mobile-friendly; good Core Web Vitals.
- [ ] Descriptive links and image alt text; HTTPS; `hreflang` if multilingual.

## Sources

- Google Search Central — SEO Starter Guide — https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Google Search Central — Search Essentials — https://developers.google.com/search/docs/essentials
- schema.org — https://schema.org/
