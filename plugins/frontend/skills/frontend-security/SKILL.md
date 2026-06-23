---
name: frontend-security
description: >-
  Apply client-side web security best practices based on OWASP. Use when building
  or reviewing UI that renders user content, handles auth/sessions, loads
  third-party scripts, or when the user mentions XSS, CSP, CSRF, sanitization,
  innerHTML/dangerouslySetInnerHTML, clickjacking, or frontend security.
---

# Frontend Security

Client-side security is **defense in depth** — no single control stops XSS, so
layer output encoding, sanitization, CSP, and Trusted Types. Assume all input is
hostile, including data from your own APIs.

## Cross-site scripting (XSS) — the main threat

XSS runs attacker JS in your page (reflected, stored, or DOM-based). Defend in
layers:

- **Avoid dangerous sinks** — don't write untrusted data via `innerHTML`,
  `document.write`, `eval`, the `Function` constructor, or
  `dangerouslySetInnerHTML`.
- **Use safe DOM APIs** — `textContent`, `setAttribute`, `.value`,
  `createElement`. These don't parse HTML.
- **Context-aware output encoding** — HTML, JS, URL, and CSS contexts each need
  different escaping; a value safe in one is unsafe in another.
- **Sanitize when you must render HTML** — use a vetted sanitizer (**DOMPurify**)
  with a strict allow-list; never hand-roll regex sanitization.
- **Trusted Types** — enforce that injection sinks only receive sanitized values.

## Content Security Policy (CSP)

- Prefer a **strict, nonce- (or hash-) based** CSP over host allow-lists — it's
  far harder to bypass. Regenerate the nonce per request.
- Add **`frame-ancestors 'none'`** (with `X-Frame-Options: DENY` fallback) to stop
  clickjacking.
- Treat CSP as a second line of defense, not a substitute for encoding.

## Other essentials

- **Subresource Integrity (SRI)** — add integrity hashes + `crossorigin` to
  third-party `<script>`/`<link>` so a compromised CDN can't swap them.
- **Cookies** — `Secure`, `HttpOnly`, and `SameSite` (Strict/Lax) for session
  cookies.
- **CSRF** — rely on `SameSite` cookies and anti-CSRF tokens for state-changing
  requests; don't perform mutations on GET.
- **Third-party scripts** — minimise them; each is code you don't control running
  in your origin. Audit and pin them.
- **Don't expose secrets** — no API keys/tokens in client bundles or logs.

## Checklist

- [ ] No untrusted data into `innerHTML`/`dangerouslySetInnerHTML`/`eval`.
- [ ] DOMPurify (strict config) where HTML rendering is unavoidable.
- [ ] Strict nonce-based CSP + `frame-ancestors`.
- [ ] SRI on all third-party CDN assets.
- [ ] `Secure`/`HttpOnly`/`SameSite` cookies; CSRF protection on mutations.
- [ ] No secrets shipped to the client.

## Sources

- OWASP XSS Prevention Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- OWASP DOM-based XSS Prevention — https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html
- OWASP CSP Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
- MDN CSP — https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- DOMPurify — https://github.com/cure53/DOMPurify
