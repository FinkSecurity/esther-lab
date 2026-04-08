# Phase 4: Manual Web App Testing

**Date Started:** 2026-04-08  
**Status:** In Progress

## Scope

Testing three priority targets:
1. **b.mi.com** — IDOR (Nginx + OpenResty backend)
2. **market.xiaomi.com** — PHP 7.4 surface
3. **account.xiaomi.com** — Auth redirect chain

## Target 1: b.mi.com — Object Storage (Corrected)

### Revised Finding: Storage Service, Not API Backend

**Discovery 1.1 - Service Identification**

Initial hypothesis was incorrect. b.mi.com is NOT a traditional API backend.

**Evidence:**
- HTTP headers reveal storage-specific metadata:
  - `x-xiaomi-hash-crc64ecma` (S3-like storage integrity check)
  - `x-xiaomi-meta-content-length` (object metadata)
  - `accept-ranges: bytes` (partial content support)
  - `access-control-expose-headers` (CORS for storage)
- Error responses show bucket/object storage semantics: "Object Not Found", "Bucket Access Denied", region tags (cnbj1 = China region)
- Tech stack: OpenResty (Nginx + Lua) — consistent with storage gateway

**Implications:**
This is a cloud object storage backend, similar to AWS S3 or Aliyun OSS. IDOR testing pivot: look for:
1. Unauthenticated object access
2. Bucket enumeration
3. Object traversal/path manipulation
4. Metadata leakage in error responses

### Test 1.1: Unauthenticated Object Access

**Status:** In Progress

**Command:**
```bash
curl -v https://b.mi.com/bucket-name/object-name
```

**Initial Results:**
- Standard paths return 404 or "Object Not Found"
- Error messages leak region information
- All requests get unique `x-xiaomi-request-id` (request tracking)

### Test 1.2: Bucket Enumeration

**Status:** Pending

### Findings
_(To be updated as testing proceeds)_

## Target 2: market.xiaomi.com — PHP 7.4 Surface

### Hypothesis
Apache + PHP 7.4 (EOL Nov 2022) running. PHP 7.4 is outdated and may have exploitable conditions: XXE in XML processing, type juggling, deserialization issues.

### Test 2.1: phpinfo() Exposure

**Status:** Pending

### Test 2.2: Directory Fuzzing

**Status:** Pending

## Target 3: account.xiaomi.com — Auth Redirect Chain

### Hypothesis
passport.xiaomi.com → account.xiaomi.com redirect suggests centralized SSO infrastructure. May have open redirect or auth token leakage across redirect hops.

### Finding 3.1: Open Redirect Chain Discovered

**Discovery: Nested Callback Chain**

Request to `https://account.xiaomi.com/` returns HTTP 302 redirect:

**Location header (URL-encoded):**
```
https://account.xiaomi.com/pass/serviceLogin?callback=https%3A%2F%2Faccount.xiaomi.com%2Fsts%3Fsign%3D...%26followup%3Dhttps%253A%252F%252Faccount.xiaomi.com%252Fpass%252Fauth%252Fsecurity%252Fhome&sid=passport&_group=DEFAULT
```

**Decoded callback parameter:**
```
https://account.xiaomi.com/sts?sign=...&followup=https://account.xiaomi.com/pass/auth/security/home&sid=passport
```

**Key Observations:**
1. Nested callback chain: `callback` → `sts` endpoint → `followup` parameter
2. Sign parameter: cryptographic signature on callback URL
3. SID parameter: session ID in redirect chain
4. **Open Redirect Risk:** `followup` parameter determines final redirect destination

### Redirect Chain Mapping

**Confirmed Path:**
1. `https://account.xiaomi.com/` → HTTP 302
2. → Redirect to `/pass/serviceLogin?callback=...&sid=passport`
3. → `callback` points to `/sts?sign=...&followup=...&sid=passport`
4. → `followup` determines post-auth redirect

### Test 3.2: Open Redirect PoC

**Status:** Pending — Testing if followup parameter accepts external URLs

---

## Notes

- All probes documented in real-time
- Rate limiting: 10 req/sec
- Any confirmed finding triggers operator notification via Telegram before proceeding
- Commit findings after each target
