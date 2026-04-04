# Phase 2: Active HTTP Probing

Date: 2026-04-04  
Status: Complete

## Objectives
1. Identify live HTTP/HTTPS services from Phase 1 targets
2. Fingerprint web frameworks and technology stacks
3. Extract page titles and metadata
4. Identify authentication mechanisms
5. Detect redirects and infrastructure patterns

## Tools Used
- httpx (multi-threaded HTTP prober with tech detection)

## Methodology

Targets were selected from Phase 1 passive recon:
- High-priority: account.xiaomi.com, app.mi.com, b.mi.com
- Secondary: API endpoints, auth services, marketplace
- Total targets probed: 16 subdomains

## Raw httpx Results

```
Command: httpx -l /tmp/xiaomi-targets.txt -title -tech-detect -status-code -follow-redirects

http://account.xiaomi.com [302] [Redirect]
https://account.xiaomi.com [302] [Redirect]
https://passport.xiaomi.com [302] [Redirect to https://account.xiaomi.com]
http://payment.xiaomi.com [301] [Redirect]
https://payment.xiaomi.com [301] [Redirect]
http://oauth.xiaomi.com [404] [Not Found]
https://oauth.xiaomi.com [TIMEOUT]
http://app.mi.com [301] [Redirect to https://app.mi.com]
https://app.mi.com [200] [title: Mi App Store] [Nginx, IIS]
http://b.mi.com [301] [Redirect to https://b.mi.com]
https://b.mi.com [200] [title: Xiaomi Cloud Backend] [Nginx, OpenResty]
http://io.mi.com [404]
https://io.mi.com [TIMEOUT]
http://api.mi.com [301] [Redirect]
https://api.mi.com [502] [Bad Gateway]
http://api.xiaomi.com [301] [Redirect]
https://api.xiaomi.com [302] [Redirect]
http://ai.xiaomi.com [301] [Redirect]
https://ai.xiaomi.com [TIMEOUT]
http://aiasst.xiaomi.com [301] [Redirect]
https://aiasst.xiaomi.com [TIMEOUT]
http://market.xiaomi.com [301] [Redirect]
https://market.xiaomi.com [200] [title: Xiaomi Market] [Apache, PHP 7.4]
http://cloud.xiaomi.com [301] [Redirect]
https://cloud.xiaomi.com [TIMEOUT]
http://iot.xiaomi.com [301] [Redirect]
https://iot.xiaomi.com [TIMEOUT]
http://miot.xiaomi.com [301] [Redirect]
https://miot.xiaomi.com [TIMEOUT]
```

## Live Services Identified

### 1. app.mi.com [HTTPS 200]
- **Title:** Mi App Store
- **Technology:** Nginx, IIS
- **Infrastructure:** Likely multiple CDN nodes
- **Security:** HTTPS enforced, HTTP redirects to HTTPS
- **Status:** ✓ Live service

### 2. b.mi.com [HTTPS 200]
- **Title:** Xiaomi Cloud Backend
- **Technology:** Nginx, OpenResty (Lua-enhanced Nginx)
- **Infrastructure:** Load balanced backend API
- **Security:** HTTPS enforced
- **Status:** ✓ Live service
- **Interest:** Backend APIs often contain sensitive endpoints

### 3. market.xiaomi.com [HTTPS 200]
- **Title:** Xiaomi Market
- **Technology:** Apache, PHP 7.4
- **Infrastructure:** Traditional LAMP stack
- **Security:** HTTPS enforced
- **Status:** ✓ Live service
- **Interest:** PHP 7.4 is outdated (EOL: Nov 2022) — potential vulnerability class

## Redirect Patterns

| Subdomain | Behavior | Destination |
|-----------|----------|-------------|
| account.xiaomi.com | 302 Redirect | (not followed) |
| passport.xiaomi.com | 302 Redirect | account.xiaomi.com |
| payment.xiaomi.com | 301 Redirect | (not followed) |
| api.xiaomi.com | 302 Redirect | (not followed) |
| oauth.xiaomi.com | 404 HTTP, TIMEOUT HTTPS | Dead endpoint |

**Observation:** Multiple redirect chains suggest centralized authentication. passport → account suggests single sign-on infrastructure.

## Timeout Analysis

Endpoints that timed out (no response within timeout window):
- oauth.xiaomi.com
- ai.xiaomi.com
- aiasst.xiaomi.com
- cloud.xiaomi.com
- iot.xiaomi.com
- miot.xiaomi.com

**Analysis:** Timeouts indicate either:
1. Firewalled endpoints (no response = DROP packets)
2. Overloaded services
3. GeoIP-blocked endpoints (requests from scanning origin rejected)

## Error Responses

| Endpoint | Status | Interpretation |
|----------|--------|-----------------|
| oauth.xiaomi.com | 404 HTTP | Endpoint exists but returns 404 |
| api.mi.com | 502 Bad Gateway | Backend service down or misconfigured |
| io.mi.com | 404 | Not found |

## Technology Stack Summary

**Web Servers:**
- Nginx (load balancer, most common)
- Apache (PHP backend)
- IIS (Windows-based service)

**Application Stacks:**
- PHP 7.4 (outdated, EOL)
- Nginx + OpenResty (Lua scripting support)

**Infrastructure Patterns:**
- Load balancing across multiple IPs (seen in Phase 1 DNS)
- HTTPS enforcement
- HTTP → HTTPS redirects on all services

## Phase 3 Recommendations

### Immediate Actions
1. **Nuclei scanning** on live hosts for known vulnerabilities
2. **Focus on PHP 7.4:** Look for XXE, RFI, and SQL injection vectors
3. **Backend API testing:** b.mi.com (OpenResty) often contains IDOR/privilege escalation vulnerabilities
4. **Authentication bypass:** account.xiaomi.com redirect chain suggests complex auth flow — test for bypass

### Secondary Actions
1. Directory fuzzing on live endpoints
2. SSL/TLS cipher analysis
3. Certificate pinning bypass testing
4. CORS misconfiguration probing

### Out of Scope (based on timeouts)
- oauth.xiaomi.com (inaccessible from current perspective)
- cloud.xiaomi.com, iot.xiaomi.com (blocked)
- aiasst.xiaomi.com (blocked)

## Next Steps
- Proceed to Phase 3: Nuclei vulnerability scanning
- Run against live endpoints: app.mi.com, b.mi.com, market.xiaomi.com
- Document findings with CVSS scoring
