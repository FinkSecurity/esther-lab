# Phase 4: Active HTTP Probing — x.ai

**Date:** 2026-03-20  
**Status:** In Progress  
**Phase:** 4 (Active Reconnaissance)

## Summary

Began active HTTP probing against confirmed live x.ai assets. Primary findings focus on infrastructure, WAF behavior, and attack surface mapping.

## Key Findings

### Main Domain (x.ai)

**Response Behavior:**
- Initial request (no User-Agent): HTTP 403 Forbidden (Cloudflare WAF)
- Request with browser User-Agent: HTTP 200 OK
- **Implication:** Cloudflare WAF blocking non-browser traffic

**Technology Stack:**
- Framework: Next.js (server: Nextjs)
- Hosting: Cloudflare (cf-ray headers, cf-cache-status)
- Response Headers Reveal:
  - Content-Security-Policy with wss://api.x.ai endpoint
  - Data CDN at https://data.x.ai
  - External integrations: Spline Design, Typekit, YouTube, Google Docs

**Public Endpoints:**
- ✅ /robots.txt (HTTP 200) — Accessible
  - Disallows /tools/ for all user agents
  - Disallows /tools/ specifically for LLM bots (GPTBot, ClaudeBot, PerplexityBot, etc.)
  - References sitemap at /sitemap.xml

**Blocked Paths:**
- All /api/* endpoints return 403 (WAF block)
- /.env, /.env.local — 403 (likely Cloudflare rule)
- /debug, /.git — 403 (likely Cloudflare rule)
- /sitemap.xml — 403 (interesting: referenced but blocked)
- /tools/ — 403 (robot-disallowed path)

### Subdomain Probing

**data.x.ai**
- Response: HTTP 403
- Appears to be restricted data endpoint

**api.x.ai**
- Response: HTTP 421 Misdirected Request
- Server: Envoy WASM service (prod-ic-ingress-fallback)
- **Implication:** API backend exists, using Envoy ingress controller with WebAssembly security module
- 421 suggests SNI (Server Name Indication) mismatch or routing misconfiguration
- Not intended to be accessed directly from public internet

## Attack Surface Assessment

### Low-Hanging Fruit
- No .env, .git, or debug endpoints exposed
- No open admin panels
- Cloudflare WAF is actively blocking non-standard requests

### Interesting Observations
1. **Robot Disallow Patterns:** /tools/ is specifically disallowed for LLM bots. This suggests:
   - Possible API endpoint or internal tools path
   - Anti-AI-scraping measures in place
   - May be worth fuzzing if it exists as a real endpoint

2. **API Architecture:** Envoy WASM ingress controller indicates:
   - Modern, containerized microservice architecture
   - Sophisticated WAF/ingress rules (not just vanilla Cloudflare)
   - Production-grade security posture

3. **Sitemap Blocking:** /sitemap.xml is blocked despite being referenced in robots.txt
   - Possible oversight or intentional (hidden sitemap from public access)

## Next Steps (Phase 5 Recommendations)

- Certificate transparency (CT) logs — check for SSL certificates revealing internal hostnames or services
- Subdomain fuzzing (DNS brute force with common names)
- Check historical data (Wayback Machine, certificate history)
- Analyze JavaScript bundles from main site for API endpoints
- Look for CORS misconfigurations or information disclosure in OPTIONS requests

## Conclusion

x.ai's infrastructure is well-protected with modern WAF rules and microservice architecture. The organization is clearly security-conscious. Direct API enumeration via HTTP is not viable; pivot to passive intelligence (CT logs, historical data, JS analysis).

---

**Investigation Status:** Ongoing. No vulnerabilities identified in Phase 4.
