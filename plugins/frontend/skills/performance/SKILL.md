---
name: performance
description: >-
  Apply web performance best practices based on Google's Core Web Vitals and
  web.dev. Use when building or reviewing UI for speed, when the user mentions
  performance, Core Web Vitals, LCP, INP, CLS, Lighthouse, bundle size, slow
  loads, or jank.
---

# Web Performance

Performance is a user-experience and SEO concern measured by **Core Web Vitals**,
assessed at the **75th percentile** of real-user loads. Optimise the field metrics,
not just lab scores.

## Core Web Vitals (current thresholds)

| Metric | Measures | Good | Needs work | Poor |
|--------|----------|------|------------|------|
| **LCP** — Largest Contentful Paint | loading | ≤ 2.5s | 2.5–4s | > 4s |
| **INP** — Interaction to Next Paint | responsiveness | ≤ 200ms | 200–500ms | > 500ms |
| **CLS** — Cumulative Layout Shift | visual stability | ≤ 0.1 | 0.1–0.25 | > 0.25 |

> **INP replaced First Input Delay (FID)** as a Core Web Vital on 12 March 2024.
> Unlike FID (first interaction only), INP measures responsiveness across *all*
> interactions. Don't optimise for FID anymore.

## Optimise LCP (≤ 2.5s)

- Preload the LCP image (`<link rel=preload as=image>`) and set
  `fetchpriority="high"`; **never** `loading="lazy"` on the LCP image.
- Serve modern formats (AVIF/WebP) with responsive `srcset`/`sizes`.
- Fonts: WOFF2 + `font-display: swap|optional`; preload critical fonts.
- Cut render-blocking CSS/JS; inline critical CSS, defer the rest; reduce TTFB
  with caching/CDN.
- Make the LCP resource discoverable in the initial HTML (not injected by JS).

## Optimise INP (≤ 200ms)

- Minimise main-thread work in event handlers; break long tasks (>50ms) into
  chunks (`scheduler.yield()`/`setTimeout`, `requestIdleCallback` for non-urgent).
- Batch DOM reads then writes to avoid layout thrashing.
- Use `content-visibility: auto` to skip rendering off-screen content; keep the
  DOM small.
- Render the visual update first, defer follow-up logic to the next frame.

## Prevent CLS (≤ 0.1)

- Set explicit `width`/`height` (or `aspect-ratio`) on images, video, iframes, ads.
- Reserve space for dynamically injected content; don't insert above existing
  content except on user interaction.
- Avoid layout-triggering font swaps; animate with `transform`/`opacity`, not
  geometry.

## Shipping less JavaScript

- Set a JS **bundle budget** and enforce it in CI.
- Code-split by route and component; `import()` non-critical features lazily.
- Tree-shake, minify, compress (Brotli/gzip); audit with the bundle analyzer.
- Cache aggressively (`Cache-Control`, immutable hashed assets, a service worker
  where it fits).

## Tools

- **Lighthouse** (lab) and **PageSpeed Insights** (lab + field).
- **Chrome UX Report (CrUX)** — real-user field data; the source of truth for
  ranking.
- **RAIL** is still a useful mental model: Response <100ms, Animation ~16ms/frame
  (60fps), Idle work in ≤50ms chunks, Load fast.

## Common pitfalls

- Lazy-loading the hero/LCP image.
- Optimising lab scores while field CrUX stays poor.
- Large unsplit JS bundles blocking interactivity (hurts INP).
- Images and ads with no reserved dimensions (CLS).

## Sources

- Core Web Vitals — https://web.dev/explore/learn-core-web-vitals
- Optimize LCP — https://web.dev/articles/optimize-lcp
- Optimize INP — https://web.dev/articles/optimize-inp
- INP replaces FID — https://web.dev/blog/inp-cwv-march-12
- CWV & Search ranking — https://developers.google.com/search/docs/appearance/core-web-vitals
