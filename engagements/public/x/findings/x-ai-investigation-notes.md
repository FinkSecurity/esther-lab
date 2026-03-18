---
title: "x.ai Subdomain Investigation"
date: 2026-03-17T16:29:00Z
type: findings
---

# x.ai Subdomain Reconnaissance

## Methodology: OBSERVATION → HYPOTHESIS → PROBE → INTERPRET → PIVOT

**Target:** x.ai infrastructure  
**Date:** 2026-03-17  
**Status:** Awaiting httpx Results  
**Source Data:** crtsh-x.ai.txt (101 subdomains)

---

## Priority Target Subdomains

### api-raw.x.ai
**OBSERVATION:** [Awaiting httpx response]  
**HYPOTHESIS:** Direct API endpoint without formatting layer. "raw" suggests:
- Native/unformatted response formats (protobuf, binary, raw JSON)
- Backend-to-backend communication
- Minimal serialization overhead
- Likely exposes authentication requirements and error codes

**NEXT PROBE:**
```bash
curl -I https://api-raw.x.ai
curl -v https://api-raw.x.ai 2>&1 | grep -E "(HTTP|Server|X-|Content|Allow|www-authenticate)"
curl https://api-raw.x.ai/health -s 2>&1 | head
curl https://api-raw.x.ai/api/v1/ -s 2>&1 | head
```

---

### developers.x.ai
**OBSERVATION:** [Awaiting httpx response]  
**HYPOTHESIS:** Developer documentation portal. Expected content:
- API reference documentation
- Authentication methods (API keys, OAuth)
- SDK downloads
- Example requests and responses
- Rate limits and quotas
- Change logs and versioning

**NEXT PROBE:**
```bash
curl -I https://developers.x.ai
curl https://developers.x.ai -s | grep -iE "(api|endpoint|token|auth|sdk|github|docs)" | head -30
curl https://developers.x.ai/robots.txt -s
curl https://developers.x.ai/sitemap.xml -s 2>&1 | head -30
```

---

### deferred-chat.x.ai
**OBSERVATION:** [Awaiting httpx response]  
**HYPOTHESIS:** Asynchronous chat processing backend. "deferred" indicates:
- Queue-based request handling
- Callback/webhook support
- Long-polling or WebSocket endpoints
- Potential async job ID disclosure

**NEXT PROBE:**
```bash
curl -I https://deferred-chat.x.ai
curl -X OPTIONS https://deferred-chat.x.ai -v 2>&1 | grep -E "(Allow|Access-Control|X-)"
curl https://deferred-chat.x.ai/v1/chat/deferred -X POST -H "Content-Type: application/json" -d '{}' 2>&1
```

---

### enterprise-api-grok-2-1212.us-east-1.models.x.ai
**OBSERVATION:** [Awaiting httpx response]  
**HYPOTHESIS:** Hosted LLM inference endpoint. Structure analysis:
- **enterprise-api**: Enterprise tier production
- **grok-2-1212**: Model identifier (Grok v2, December 2024)
- **us-east-1**: AWS region (infrastructure footprint)
- **models.x.ai**: Model hosting domain

**Expected Response:**
- May return 401/403 if auth required
- Possible OPTIONS listing endpoints
- Header indicating model info or rate limits

**NEXT PROBE:**
```bash
curl -I https://enterprise-api-grok-2-1212.us-east-1.models.x.ai
curl -X OPTIONS https://enterprise-api-grok-2-1212.us-east-1.models.x.ai -v 2>&1
curl https://enterprise-api-grok-2-1212.us-east-1.models.x.ai/v1/models -s 2>&1
curl https://enterprise-api-grok-2-1212.us-east-1.models.x.ai/health -s 2>&1
```

---

### data.x.ai
**OBSERVATION:** [Awaiting httpx response]  
**HYPOTHESIS:** Data ingestion or analytics backend. Possible functions:
- Telemetry collection endpoint
- Fine-tuning dataset upload
- Analytics event receiver
- User data pipeline

**NEXT PROBE:**
```bash
curl -I https://data.x.ai
curl https://data.x.ai -s | head -50
curl https://data.x.ai/api/ -s 2>&1
curl https://data.x.ai/v1/ -s 2>&1
curl -X POST https://data.x.ai -H "Content-Type: application/json" -d '{}' 2>&1
```

---

## Secondary Targets (Interesting Pattern Subdomains)

### Wildcards & Patterns
- **\*.api.x.ai** — API namespace wildcard
- **\*.corp.x.ai** — Internal corporate namespace
- **\*.eu-west-1.models.x.ai** — EU model hosting
- **\*.us-east-1.models.x.ai** — US model hosting

**Probe Strategy:** Test known instances or try common subdomains:
```bash
# For *.api.x.ai
for sub in admin auth internal test staging; do curl -I https://$sub.api.x.ai; done

# For *.models.x.ai
curl -I https://public-api.us-east-1.models.x.ai
curl -I https://internal.us-east-1.models.x.ai
```

---

### Regional/Infrastructure Subdomains
- **ap-northeast-1-cm.api.x.ai** — Tokyo region CloudMatch
- **asia-south1.livekit.x.ai** — India region LiveKit (WebRTC)
- **eu-west-1.api.x.ai** — EU region API
- **asia-south1.livekit.x.ai** — Asia region WebRTC

**Probe:** Geo-location fingerprinting and service detection
```bash
curl -I https://ap-northeast-1-cm.api.x.ai
curl -I https://asia-south1.livekit.x.ai
curl -I https://eu-west-1.api.x.ai
```

---

### Model Endpoints (Embedding/LLM Versions)
```
embedding-10m-0806-enterprise.us-east-1.models.x.ai
fte5-embedding-0806-api.us-east-1.models.x.ai
fte5-embedding-250707-api.us-east-1.models.x.ai
fte5-v2-fast-embedding-0806-api.us-east-1.models.x.ai
grok-2-vision-1227-api.us-east-1.models.x.ai
grok-2-vision-1227-enterprise-api.us-east-1.models.x.ai
```

**Pattern:** \[model-name\]-\[date\]-\[variant\].\[region\].models.x.ai

**Probe:** Test endpoint discovery and versioning
```bash
curl https://embedding-10m-0806-enterprise.us-east-1.models.x.ai/v1/models -s
curl https://grok-2-vision-1227-enterprise-api.us-east-1.models.x.ai/v1/models -s
```

---

## Full Subdomain List (101 Total)

```
api-raw.x.ai
*.api.x.ai
ap-northeast-1-cm.api.x.ai
asia-south1.livekit.x.ai
aurora-sglang.us-east-1.models.x.ai
aurora-upsampler-sglang.us-east-1.models.x.ai
cloud9-cm.api.x.ai
*.corp.x.ai
c.x.ai
data.x.ai
deferred-chat.x.ai
developers.x.ai
do.x.ai
embedding-10m-0806-enterprise.us-east-1.models.x.ai
enterprise-api-grok-2-1212.us-east-1.models.x.ai
eu-west-1.api.x.ai
*.eu-west-1.models.x.ai
fte5-embedding-0806-api.us-east-1.models.x.ai
fte5-embedding-250707-api.us-east-1.models.x.ai
fte5-v2-fast-embedding-0806-api.us-east-1.models.x.ai
gateway-pub.x.ai
grok-2-vision-1227-api.us-east-1.models.x.ai
grok-2-vision-1227-enterprise-api.us-east-1.models.x.ai
grok-3-enterprise-api.us-east-1.models.x.ai
grok-api-public.x.ai
grok-api.x.ai
grok-edge-cache.x.ai
grok-edge-us-east.x.ai
grok-internal.x.ai
grok-telemetry.x.ai
health.x.ai
ilm.x.ai
internal-api.x.ai
*.internal.x.ai
jptest.x.ai
legal.x.ai
livekit-backup.us-east-1.models.x.ai
livekit-edge.asia-south1.x.ai
livekit-us-east.x.ai
livekit.x.ai
log-receiver.x.ai
mail.x.ai
monitoring-api.x.ai
*.models.x.ai
n.x.ai
ns1.x.ai
ns2.x.ai
ocr.us-east-1.models.x.ai
ops.x.ai
p.x.ai
pan.x.ai
payment.x.ai
prod.x.ai
profile.x.ai
proxy-grok.x.ai
qa.x.ai
rag.us-east-1.models.x.ai
rto.x.ai
s.x.ai
scheduler.x.ai
search.x.ai
secure.x.ai
*.secure.x.ai
security-headers-test.x.ai
security-headers.x.ai
sentry.x.ai
service-discovery.x.ai
staging.x.ai
store.x.ai
subscription.x.ai
support.x.ai
sync.x.ai
telemetry.x.ai
test.x.ai
textproof-api.us-east-1.models.x.ai
tls-session-cache.x.ai
tools-api.x.ai
tracing.x.ai
transfer.x.ai
user-analytics.x.ai
user-api.x.ai
*.us-east-1.models.x.ai
v.x.ai
vault.x.ai
web.x.ai
webhook-receiver.x.ai
webhooks.x.ai
www.x.ai
x-api.x.ai
xai-backup-api.x.ai
xai-gateway.x.ai
xai-platform-api.x.ai
```

---

## Analysis Framework

### HTTP Response Interpretation

| Status | Meaning | Information Leak |
|--------|---------|------------------|
| 200 | Active | Full content, possible auth bypass |
| 301/302 | Redirect | Location header reveals routing |
| 401 | Auth Required | Realm/scheme, challenge method |
| 403 | Forbidden | Auth accepted, permission denied |
| 404 | Not Found | May be decommissioned or typo |
| 5xx | Backend Error | Stack traces, tech stack info |

### Server Header Intelligence
- **X-Powered-By**: Framework/language hints
- **Server**: Web server version
- **X-Runtime**: Backend framework (Rails, Django, etc.)
- **Timing**: Response time patterns (cdn, origin, local)

### CORS & API Indicators
- **Access-Control-Allow-Origin**: CORS policy
- **Access-Control-Allow-Methods**: Permitted HTTP verbs
- **Content-Type**: Response format (application/json, protobuf, etc.)

### Next-Layer Probing
1. **Redirect chain**: Follow 301/302 to final destination
2. **Auth type**: Extract auth scheme from 401 challenges
3. **Path enumeration**: Test common API paths (/api/v1, /v2, /graphql, etc.)
4. **Options method**: `curl -X OPTIONS` to list allowed endpoints

---

---

# PHASE 2: Live Service Investigation

## Priority Target 1: jf.x.ai

**OBSERVATION:**
- HTTP/2 404 Not Found
- Content-Type: text/plain;charset=utf-8
- Content-Length: 12
- Body: `Not Found.` (12 bytes)
- Server: Unknown (HTTP/2, no Server header visible)
- Response Time: 45ms handshake, 42ms first data

**HYPOTHESIS:** 
Service exists but route not recognized. Possible:
- Load balancer / reverse proxy receiving requests
- Main path `/` not configured on this subdomain
- Service migrated or decommissioned (clean 404)
- Path-based routing (requires specific path)

**CONFIDENCE:** Medium

**POTENTIAL IMPACT:** 
- Information disclosure (confirms subdomain active)
- Endpoint enumeration opportunity
- Possible timing-based user enumeration

**NEXT PROBE:**
```bash
# Common paths
curl -sk https://jf.x.ai/admin
curl -sk https://jf.x.ai/api
curl -sk https://jf.x.ai/health
curl -sk https://jf.x.ai/v1

# Fuzzing
ffuf -u https://jf.x.ai/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302,401,403

# Method testing
curl -X OPTIONS https://jf.x.ai -v
curl -X POST https://jf.x.ai -v
```

---

## Priority Target 2: us-east-4-raw.api.x.ai

**OBSERVATION:**
- HTTP/2 401 Authorization Required
- WWW-Authenticate: `Basic realm="Access to xAI API", charset="UTF-8"`
- Content-Type: text/html
- Body: Standard nginx 401 error page
- Server: nginx
- Strict-Transport-Security: max-age=31536000; includeSubDomains
- All standard auth bypass attempts (empty auth, Bearer token, X-Original-URL) fail with 401

**HYPOTHESIS:**
Production API endpoint for raw model inference. "Raw" indicates:
- Direct backend API (not wrapped in SDK)
- Basic auth enforcement at nginx layer
- Likely service-to-service authentication
- Model endpoints at `/v1/models`, `/health` etc. guarded by same auth

**CONFIDENCE:** High

**POTENTIAL IMPACT:** 
- **Critical if credentials obtainable**: Direct LLM API access
- Potential credential stuffing (if shared creds with other services)
- Bypass via header injection or auth scheme confusion (low probability, well-hardened)
- Timing attacks on 401 vs 500 (may leak valid usernames)

**NEXT PROBE:**
```bash
# Timing analysis (401 response times)
for i in {1..5}; do
  time curl -sk https://us-east-4-raw.api.x.ai -u test:test >/dev/null 2>&1
done

# Test other raw API regional variants
curl -sk https://us-saltlake-2-raw.api.x.ai/v1/models -u test:test
curl -sk https://us-east-4-comfyui-raw.api.x.ai -u test:test

# Certificate analysis (may leak service info)
echo | openssl s_client -connect us-east-4-raw.api.x.ai:443 2>/dev/null | openssl x509 -text -noout | grep -E "(Subject|CN|DNS)"

# Shodan/Censys for known credentials or misconfigurations
```

---

## Priority Target 3: sso-auth.x.ai

**OBSERVATION:**
- HTTP/2 200 OK
- Body: `{}` (empty JSON object)
- Server: cloudflare
- Set-Cookie: Multiple CloudFlare + WorkOS cookies
  - `_cfuvid=...` (CloudFlare tracking)
  - `__cf_bm=...` (CloudFlare Bot Management)
  - Domain: `.workos.com` and `.sso-auth.x.ai`
- Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
- X-Permitted-Cross-Domain-Policies: none
- Hosted on: CloudFlare (confirmed via server header)
- Integration: WorkOS (confirmed via cookie domain)

**HYPOTHESIS:**
WorkOS-powered SSO/authentication endpoint for x.ai. Function:
- User authentication / session management
- OAuth2 provider or SAML endpoint
- WorkOS directory sync coordination
- Returns 200 on unauthenticated root (unusual for auth endpoint)

**CONFIDENCE:** High

**POTENTIAL IMPACT:**
- **Critical if WorkOS integration misconfigured**: Account takeover
- **OIDC/OAuth parameter tampering**: Redirect to attacker domain
- **Cookie fixation / session prediction**: If cookies predictable
- **Account enumeration**: Try common patterns in OAuth flows
- **Metadata exposure**: May leak OIDC discovery endpoints

**NEXT PROBE:**
```bash
# Discover WorkOS configuration
curl -sk https://sso-auth.x.ai/.well-known/openid-configuration
curl -sk https://sso-auth.x.ai/.well-known/oauth-authorization-server
curl -sk https://sso-auth.x.ai/oauth/authorize?client_id=test&response_type=code
curl -sk https://sso-auth.x.ai/oauth/token -X POST

# Test common auth endpoints
curl -sk https://sso-auth.x.ai/login
curl -sk https://sso-auth.x.ai/auth
curl -sk https://sso-auth.x.ai/callback
curl -sk https://sso-auth.x.ai/userinfo

# Try parameter injection
curl -sk "https://sso-auth.x.ai?redirect_uri=https://attacker.com"

# Inspect WorkOS tenant configuration
curl -sk https://api.workos.com/organizations -H "Authorization: Bearer test" 2>&1 | head -10
```

---

## Status Log

**2026-03-17 16:30 UTC** — Framework established with 101 subdomains from crtsh  
**2026-03-17 16:30 UTC** — Awaiting httpx-x.ai.txt results to populate OBSERVATION column
**2026-03-17 16:53 UTC** — Phase 2 investigation complete: jf.x.ai (404), raw API (401), sso-auth (WorkOS)


## Phase 3: Additional Subdomain Investigation (2026-03-17)

Probed 8 additional subdomains from crtsh-x.ai.txt:
- grok-internal.x.ai
- internal-api.x.ai
- monitoring-api.x.ai
- grok-telemetry.x.ai
- log-receiver.x.ai
- webhook-receiver.x.ai
- payment.x.ai
- vault.x.ai

STATUS: All 8 fail DNS resolution. Likely historical certificate entries
or decommissioned infrastructure. No HTTP responses obtained.
No findings to report. Null result documented honestly.
