# Security Policy — Zen Fragrances

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please **do not** open a public issue.

Email us at: **security@zenfragrances.co.za**

We'll acknowledge your report within 48 hours and provide a timeline for resolution within 5 business days.

## Scope

| In scope | Out of scope |
|----------|-------------|
| SQL injection, XSS, CSRF | Social engineering attacks |
| Authentication bypass | Physical security |
| Payment processing flaws | DDoS / rate limiting (by design) |
| Sensitive data exposure | Third-party service vulnerabilities (Railway, Kapso, Meta) |
| API key leakage | Theoretical vulnerabilities without proof of concept |

## Supported Versions

Only the latest `main` branch is supported. We do not backport security fixes.

## Disclosure Policy

- Reporter provides details privately via email
- We acknowledge within 48 hours
- We fix and deploy within 14 days (critical: 72 hours)
- Reporter is credited in release notes (unless they prefer anonymity)
- CVE requested if applicable

## Security Best Practices We Follow

1. **No secrets in code** — All credentials via environment variables, `.env` in `.gitignore`
2. **Webhook signature verification** — HMAC-SHA256 on all WhatsApp webhooks
3. **Rate limiting** — Tiered rate limits on all public endpoints
4. **Idempotency** — Message deduplication prevents double-processing
5. **Database abstraction** — Parameterized queries prevent SQL injection
6. **Security headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
7. **HttpOnly cookies** — Dashboard auth tokens not accessible via JavaScript
8. **Atomic stock operations** — CHECK constraints prevent overselling

## GitHub Security Settings Enabled

- [ ] Private vulnerability reporting (Settings → Security)
- [ ] Secret scanning with push protection
- [ ] Dependabot alerts + dependency review
- [ ] Code scanning (CodeQL default setup)
- [ ] Branch protection on `main` (require PR + 1 approval)
