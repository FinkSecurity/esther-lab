# Phase 4 Continued: Active Subdomain Probing & Manual HTTP Analysis

**Date:** 2026-03-21  
**Status:** In Progress  
**Phase:** 4 (Active Reconnaissance - Subdomain Deep Dive)

## Summary

Continued active HTTP probing against x.ai subdomains discovered during Phase 3 enumeration. Manual probing revealed multiple live application endpoints and infrastructure patterns.

## Key Findings

### Primary Subdomains - Response Status

| Subdomain | Status | Response Code | Details |
|-----------|--------|----------------|---------|
| x.ai | 200 | OK | Main site, Next.js, Cloudflare WAF |
| api.x.ai | 421 | Misdirected Request | Envoy WASM ingress, SNI mismatch |
| console.x.ai | 307 | Temporary Redirect | Live application endpoint, redirects to /home |
| developer.x.ai | Timeout | — | DNS resolves but connection times out |
| status.x.ai | 403 | Forbidden | Cloudflare WAF block |
| docs.x.ai | 308 | Permanent Redirect | Redirect loop to itself |
| auth.x.ai | 403 | Forbidden | Cloudflare WAF block |
| chat.x.ai | NXDOMAIN | — | Does not resolve |
| login.x.ai | NXDOMAIN | — | Does not resolve |
| register.x.ai | NXDOMAIN | — | Does not resolve |
| oauth.x.ai | NXDOMAIN | — | Does not resolve |
| account.x.ai | NXDOMAIN | — | Does not resolve |
| settings.x.ai | NXDOMAIN | — | Does not resolve |
| profile.x.ai | NXDOMAIN | — | Does not resolve |
| api-keys.x.ai | NXDOMAIN | — | Does not resolve |
| credentials.x.ai | NXDOMAIN | — | Does not resolve |
| dashboard.x.ai | NXDOMAIN | — | Does not resolve |
| widget.x.ai | NXDOMAIN | — | Does not resolve |
| embed.x.ai | NXDOMAIN | — | Does not resolve |
| help.x.ai | NXDOMAIN | — | Does not resolve |
| support.x.ai | NXDOMAIN | — | Does not resolve |

### Live Application Endpoints

#### console.x.ai (307 Redirect)
- **Status:** Live authenticated application
- **Behavior:** HTTP 307 Temporary Redirect to /home path
- **Implication:** Authentication-protected console interface
- **Next Step:** Attempted access redirects unauthenticated users to login flow
- **Headers:** Cloudflare CF-RAY headers, no auth cookies forwarded
- **Technology:** Likely Next.js based on response patterns

### Protected Endpoints (403 Forbidden)

**auth.x.ai** and **status.x.ai** return 403 but don't timeout:
- **Significance:** Endpoints exist and are intentionally blocked
- **WAF Behavior:** Cloudflare blocking, not origin server rejection
- **Implication:** These subdomains are DNS-configured but access-restricted at WAF layer

### Infrastructure Observations

1. **Envoy WASM on api.x.ai**
   - 421 Misdirected Request from prod-ic-ingress-fallback
   - Suggests backend API infrastructure separate from web tier
   - WASM-based security module indicates advanced WAF setup
   - Not directly accessible from public internet (by design)

2. **Cloudflare WAF Rules**
   - Aggressive filtering of non-standard requests
   - Browser User-Agent bypass required for main site
   - Some subdomains entirely blocked (403)
   - Others not provisioned (NXDOMAIN)

3. **docs.x.ai Redirect Loop**
   - Redirects to self (308 permanent)
   - Suggests misconfigured documentation portal or deliberate access restriction

## Attack Surface Assessment

### Confirmed Live Endpoints
- console.x.ai — Authenticated application (requires credentials)
- api.x.ai — Backend API (421 error suggests proxy misconfiguration or intentional block)
- auth.x.ai — Authentication service (blocked by WAF)
- docs.x.ai — Documentation (misconfigured redirect)

### Low-Risk Observations
- No open authentication endpoints
- No exposed credentials or API keys in headers
- No verbose error messages
- WAF actively protecting application

### Potential Interest (Requires Further Testing)
- **console.x.ai redirect behavior** — Could investigate if unauthenticated redirect patterns leak information
- **api.x.ai 421 response** — Could test if SNI bypass or header manipulation triggers different behavior
- **Reverse proxy configuration** — Envoy WASM suggests complex infrastructure, potential for misconfiguration

## Next Steps (Phase 5 Recommendations)

1. **Certificate Transparency Analysis** — Identify all valid certificates for *.x.ai subdomains
2. **JavaScript Bundle Analysis** — Extract API endpoints from main site JS
3. **Historical Data Review** — Wayback Machine snapshots of console, docs endpoints
4. **HTTP Request Fuzzing** — Test auth.x.ai and docs.x.ai with header manipulation
5. **Origin IP Discovery** — Find origin IP bypassing Cloudflare WAF

## Nuclei Scan Status

Automated vulnerability scanning in progress. Results pending.

## Conclusion

x.ai's infrastructure is segmented with:
- Web tier (main site, console) on Cloudflare
- Backend API (api.x.ai) on Envoy proxy
- Protected endpoints (auth, status, docs) intentionally restricted

No obvious vulnerabilities found in passive reconnaissance. Further testing requires:
- Authentication bypass attempts (rate limiting, credential enumeration)
- WAF bypass techniques
- API reverse engineering from JavaScript

---

**Investigation Status:** Ongoing. Awaiting nuclei scan completion.
