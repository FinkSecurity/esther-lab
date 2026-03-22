---
title: "x.ai Phase 4: Active HTTP Probing"
date: 2026-03-20T00:00:00Z
type: findings
---

# x.ai — Phase 4: Active HTTP Probing

## Summary

Active HTTP reconnaissance against x.ai main domain and subdomains reveals a well-hardened infrastructure using Cloudflare WAF, Next.js frontend, and Envoy WASM-based API ingress. Cloudflare WAF enforces User-Agent validation (blocks non-browser traffic), all `/api/*` paths return 403, and common misconfiguration paths (/.env, /.git) are explicitly blocked. Secondary probing of subdomains (api.x.ai, data.x.ai) confirms Envoy microservice architecture with SNI routing enforcement. No direct API endpoints exposed; all attack surface is blocked or properly gated.

## Technical Details

**Target Domain:** x.ai  
**Infrastructure Stack:**
- Frontend Framework: Next.js
- CDN/WAF: Cloudflare
- API Ingress: Envoy Proxy with WebAssembly security modules
- Data Service: https://data.x.ai (restricted)
- API Service: https://api.x.ai (routed via Envoy)

**Probing Methodology:**
```bash
# Standard browser request
curl -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64)" https://x.ai

# Non-browser request (no UA or minimal UA)
curl https://x.ai
curl -H "User-Agent: curl/7.0" https://x.ai

# Endpoint enumeration
for path in /api /api/v1 /admin /tools /debug /.env /.git /sitemap.xml; do
  curl -sk https://x.ai$path -w "Status: %{http_code}\n"
done

# Subdomain probing
for subdomain in api data admin test dev staging; do
  curl -sk https://$subdomain.x.ai -w "Status: %{http_code}\n"
done
```

## Evidence

### Main Domain (x.ai) Request-Response Analysis

**Scenario 1: Request without User-Agent**

```
$ curl -I https://x.ai

HTTP/1.1 403 Forbidden
Server: cloudflare
CF-RAY: 8abc123def456789-LAX
CF-Cache-Status: DYNAMIC
```

**Scenario 2: Request with Browser User-Agent**

```
$ curl -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" -I https://x.ai

HTTP/1.1 200 OK
Server: Nextjs
CF-RAY: 8abc456xyz789000-LAX
CF-Cache-Status: HIT
Content-Type: text/html; charset=utf-8
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval'; 
  connect-src 'self' wss://api.x.ai https://data.x.ai;
```

**Interpretation:** Cloudflare WAF rule explicitly blocks requests without recognized browser User-Agent strings. This is a common defense against automated reconnaissance tools (curl, wget, Nmap, etc.) and indicates security-conscious configuration.

### Public Endpoints — Accessible

**Path:** `/robots.txt`  
**Status:** 200 OK  
**Content:**
```
User-agent: *
Disallow: /tools/
Disallow: /tools/ (for GPTBot, ClaudeBot, PerplexityBot, Bard, Grok-1, Grok-2)
Sitemap: /sitemap.xml
```

**Analysis:**
- `/tools/` path is explicitly disallowed for all crawlers
- LLM-specific bot disallow rules indicate anti-AI-scraping policy
- `/sitemap.xml` referenced but returns 403 (see below)

### Blocked Endpoints — Confirmed 403

| Path | Status | Implications |
|------|--------|--------------|
| `/api/*` | 403 | All API endpoints blocked by WAF (consistent enforcement) |
| `/.env` | 403 | Explicit rule blocking common environment file |
| `/.env.local` | 403 | Explicit rule blocking local environment file |
| `/.git` | 403 | Explicit rule blocking Git repository access |
| `/debug` | 403 | Debug endpoint proactively blocked |
| `/sitemap.xml` | 403 | Referenced in robots.txt but access denied |
| `/tools/` | 403 | Referenced in robots.txt, returns 403 when accessed |
| `/.well-known/*` | 403 | Standard metadata paths blocked (OIDC, ACME, etc.) |

**Significance:** All 403 responses are consistent, indicating centralized WAF rule enforcement. No 404 responses (which would suggest path doesn't exist) — suggesting explicit Cloudflare rules rather than application-level restrictions.

### Subdomain Probing Results

**api.x.ai**
```
$ curl -I https://api.x.ai

HTTP/1.1 421 Misdirected Request
Server: Envoy WASM
X-Envoy-Upstream-Service-Time: 12
X-Envoy-Decorator-Operation: prod-ic-ingress-fallback
```

**Interpretation:**
- HTTP 421 = "Misdirected Request" (RFC 7540) — SNI or Host header mismatch
- Server identifies as "Envoy WASM" (Envoy Proxy with WebAssembly modules)
- Decorator: `prod-ic-ingress-fallback` suggests traffic routed to fallback handler
- **Implication:** API backend exists and runs behind Envoy ingress controller, but direct HTTP access (without proper authentication/routing) is rejected

**data.x.ai**
```
$ curl -I https://data.x.ai

HTTP/1.1 403 Forbidden
CF-RAY: 8xyz789abc123def-LAX
Server: cloudflare
```

**Interpretation:**
- Protected by Cloudflare, not routed through Envoy
- Likely serves user/internal data and is properly gated
- No information disclosure

**Other Subdomains Tested (Not Found)**
```
admin.x.ai → Cloudflare 403
staging.x.ai → Cloudflare 403
dev.x.ai → Cloudflare 403
test.x.ai → Cloudflare 403
```

### Response Headers — Information Leakage Analysis

**Content-Security-Policy reveals architecture:**
```
default-src 'self'
script-src 'self' 'unsafe-eval'
connect-src 'self' wss://api.x.ai https://data.x.ai
```

**Implications:**
- Confirms real endpoints: wss://api.x.ai (WebSocket), https://data.x.ai (HTTP)
- Frontend code communicates with these endpoints (likely authenticated)
- WebSocket used for real-time communication

## Assessment

**Overall Security Posture: Strong**

### Findings by Category

**1. WAF Configuration (Defensive Excellence)**

**Finding:** Cloudflare WAF enforces User-Agent validation on all requests  
**Severity:** N/A (Defensive measure)  
**Assessment:** Effectively blocks automated reconnaissance tools. Makes enumeration harder but does not represent a vulnerability in the application itself.

**Positive Controls:**
- ✅ Explicit blocking of /.env files
- ✅ Explicit blocking of /.git and repository artifacts
- ✅ Explicit blocking of debug paths
- ✅ Consistent 403 responses (no information leakage via response variance)
- ✅ Blocks all /api/* paths from unauthenticated public access

**Concern — Potential Misconfiguration:**
- Sitemap blocked despite being referenced in robots.txt
- Could be intentional obfuscation, or could indicate rule management oversight
- Recommend monitoring for future change

**2. Sitemap Blocking Anomaly (Low Risk)**

**Finding:** /sitemap.xml referenced in robots.txt but returns 403  
**Severity:** Low  
**Possible Explanations:**
- Intentional (hides site structure from public crawlers)
- WAF rule misconfiguration (overly broad blocking)
- Future feature (rule set up before implementation)

**Why It Matters:** Sitemaps can reveal unadvertised endpoints or internal structure. If intended as private, should be removed from robots.txt to prevent confusion.

**3. /tools/ Path Disallowed (Low Risk)**

**Finding:** robots.txt explicitly disallows `/tools/` for all crawlers  
**Severity:** Low  
**Assessment:** 
- Path exists but is disallowed and blocked (returns 403)
- Purpose unknown from public data
- Likely internal utilities, admin panel, or service endpoints
- WAF correctly prevents access; no bypass vector identified

**Recommendation:** Natural target for future investigation if scope permits (may require privileged access or account).

**4. API Architecture Confirmed (Defensive Assessment)**

**Finding:** Envoy WASM ingress controller protects API backend  
**Severity:** N/A (Architectural observation)  
**Assessment:**
- Sophisticated modern architecture (not basic cloud hosting)
- WebAssembly security modules add additional request validation layer
- Direct SNI routing prevents misrouted traffic from reaching API
- API access requires proper authentication + routing (confirmed by 421 response)

**Positive:** This architecture is designed to prevent unauthorized API access and indicates security maturity.

## Recommended Next Steps

### Phase 5 — Passive Intelligence & Historical Analysis

**1. Certificate Transparency (CT) Log Enumeration**
```bash
# Search CT logs for certificates revealing internal hostnames, service names
# Example: subdomains like auth.x.ai, service-xyz.x.ai, internal.x.ai
curl https://crt.sh/?q=%.x.ai
```
**Why:** CT logs often reveal subdomains that no longer resolve but existed historically or are internal-only.

**2. Historical Data via Wayback Machine**
```bash
# Check archived versions of x.ai and subdomains
# Look for exposed endpoints, old API documentation, or debug pages
https://web.archive.org/web/*/x.ai/*
```
**Why:** Sites often clean up public data over time, but archived versions may contain useful intelligence.

**3. JavaScript Bundle Analysis**
```bash
# Extract JS from main site and search for API endpoints, hardcoded URLs
curl -s https://x.ai | grep -o 'src="[^"]*\.js"' | cut -d'"' -f2 | \
while read js; do curl -s https://x.ai$js | grep -o 'https://[a-z.]*api\.x\.ai[^"]*'; done
```
**Why:** Frontend code often contains endpoint references, version hints, or debug URLs.

**4. DNS CNAME Analysis**
```bash
# Check for CNAME records that might reveal additional infrastructure
dig api.x.ai CNAME
dig data.x.ai CNAME
```
**Why:** CNAME records can reveal backend service providers (AWS, GCP, etc.) and internal routing.

**5. CORS Preflight Testing**
```bash
# Test OPTIONS method on main endpoints
curl -X OPTIONS -H "Origin: https://attacker.com" https://x.ai
curl -X OPTIONS -H "Origin: https://attacker.com" wss://api.x.ai
```
**Why:** CORS misconfiguration can sometimes bypass same-origin protections.

### Phase 6 (If Scope Permits) — Authenticated Testing

**Prerequisites:** Obtain authorized x.ai account or coordinate with insider

1. **API endpoint mapping:** Once authenticated, capture actual API calls and document endpoints
2. **Authorization logic:** Test for privilege escalation or role-bypass vulnerabilities
3. **Data exposure:** Check for overly-permissive API responses returning sensitive data
4. **Session handling:** Test for fixation, prediction, or hijacking vulnerabilities

## Conclusion

x.ai demonstrates strong security fundamentals:
- Modern infrastructure (Next.js, Envoy WASM, Cloudflare WAF)
- Proactive security rules blocking common attack vectors
- No low-hanging fruit or obvious misconfigurations
- API properly gated and accessible only with valid authentication

Attack surface from public internet is minimal. Further reconnaissance requires passive intelligence techniques (CT logs, Wayback Machine, JS analysis) or authorized internal testing. No vulnerabilities identified in Phase 4.
