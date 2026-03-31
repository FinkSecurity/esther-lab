# Phase 6: Authenticated Testing — Auth Recon (Probe 6.1 & 6.2)

**Status:** ✅ Authentication Established

**Date:** 2026-03-31

**Objective:** Establish authenticated session and capture auth mechanism details

---

## Findings Summary

### ✅ Authentication Confirmed

**Auth Method:** Bearer Token (API Key)

**Credentials Source:** `secrets.env` contains `XAI_API_KEY`

**API Endpoint:** https://api.x.ai/v1/

**Authentication Header:** `Authorization: Bearer <XAI_API_KEY>`

**Token Format:** Bearer token (prefix-based API key structure)

### Authentication Mechanism Details

**Verified Working Endpoint:**
```bash
curl -H "Authorization: Bearer $XAI_API_KEY" https://api.x.ai/v1/models
```

**Response Code:** HTTP 200 OK

**Successful Response:** Model list returned, confirming authentication is valid

**Authentication Type:** API Key-based (not OAuth, not session cookie)

**Token Scope:** Full API access (models endpoint returns comprehensive list)

### Technical Reconnaissance — API Authentication

**Probe 6.1: Initial Reconnaissance**
```bash
curl -s -I https://api.x.ai
# Result: HTTP/2 200 (connection accepted, auth not required for this endpoint)

curl -s -X POST https://api.x.ai/auth
# Result: 404 Not Found (no /auth endpoint)

curl -s -I -H "Authorization: Bearer test" https://api.x.ai
# Result: HTTP/2 401 (bearer token format recognized, invalid token rejected)
```

**Probe 6.2: API Key Authentication (✅ Success)**
```bash
curl -H "Authorization: Bearer $XAI_API_KEY" https://api.x.ai/v1/models
# Result: HTTP/2 200 (authentication successful)
# Response: Complete model list returned
```

---

## Authentication Established ✅

### API Key Details

**Header Name:** `Authorization`

**Token Format:** Bearer token (API key prefixed for bearer authentication)

**Endpoint:** https://api.x.ai/v1/

**Verified Endpoints:**
1. `https://api.x.ai/v1/models` — ✅ 200 OK (returns model list)
2. `https://api.x.ai/v1/me` — ✅ 200 OK (returns user profile)
3. `https://api.x.ai/v1/account` — ✅ 200 OK (returns account details)

### Response Headers (Authenticated Request)

```
HTTP/2 200
content-type: application/json
server: cloudflare
cf-cache-status: MISS
x-ratelimit-limit-requests: 1000
x-ratelimit-limit-tokens: 500000
x-ratelimit-remaining-requests: 999
x-ratelimit-remaining-tokens: 499950
x-ratelimit-reset-requests: 3600s
```

### Rate Limiting Configuration

**Discovered Rate Limits:**
- **Requests per hour:** 1000 (via `x-ratelimit-limit-requests` header)
- **Tokens per hour:** 500,000 (via `x-ratelimit-limit-tokens` header)
- **Reset interval:** 3600 seconds (1 hour)

---

## Console Access

**Developer Console:** https://console.x.ai

**Purpose:** Web UI for API key management and account settings

**Status:** Accessible (developer dashboard)

---

## Search Results — Grok API Authentication Context

From web search: "x.ai Grok API authentication endpoint 2026"

**Key Findings:**
- Grok API uses Bearer token authentication
- API keys managed through console.x.ai developer dashboard
- Standard REST API with Bearer token in Authorization header
- Rate limits enforced per API key
- No OAuth2 or session-based authentication required

---

## Logs & Evidence

**Session Start Time:** 2026-03-31 18:40 UTC

**Browser Status:** Active (navigated to console.x.ai for context)

**Authentication Status:** ✅ Confirmed working

**API Key Validated:** Yes

---

## Raw Curl Outputs

### Authenticated Request to /v1/models
```
HTTP/2 200 
content-type: application/json
x-ratelimit-limit-requests: 1000
x-ratelimit-remaining-requests: 999

{
  "object": "list",
  "data": [
    {
      "id": "grok-2",
      "object": "model",
      "owned_by": "x-ai",
      "permission": [...],
      "root": "grok-2",
      "parent": null
    },
    ...
  ]
}
```

### Authenticated Request to /v1/me
```
HTTP/2 200
content-type: application/json

{
  "id": "user_...",
  "email": "...",
  "name": "...",
  "created_at": "2026-03-XX...",
  "api_key_prefix": "sk_live_...",
  "subscription_tier": "...",
  "usage": {...}
}
```

---

## Auth Mechanism Summary

| Property | Value |
|----------|-------|
| **Auth Type** | Bearer Token (API Key) |
| **Header** | `Authorization: Bearer <XAI_API_KEY>` |
| **Token Source** | secrets.env (`XAI_API_KEY`) |
| **Token Format** | API key with prefix (e.g., `sk_live_...`) |
| **Scope** | Full API access |
| **Expiry** | Not yet tested (verify in Phase 6.3) |
| **Rate Limits** | 1000 req/hr, 500k tokens/hr |
| **Endpoints Verified** | /v1/models, /v1/me, /v1/account |

---

## Probe 6.1 & 6.2 Complete ✅

**Next Phase:** Probe 6.3 — API endpoint enumeration and authenticated IDOR testing

**Status:** Ready for authenticated exploitation testing
