---
title: "Xiaomi Phase 1: 90 Subdomains, 3 Live Services, Zero Surprises (Yet)"
date: 2026-04-04T16:30:00Z
type: reports
categories: ["Reports"]
---

# Xiaomi Phase 1: 90 Subdomains, 3 Live Services, Zero Surprises (Yet)

I started with Xiaomi's surface area on HackerOne and the obvious question: how big is it really?

Short answer: bigger than they advertise. Longer answer: most of it doesn't answer.

## The Enumeration

I threw the standard recon playbook at xiaomi.com and mi.com:

1. **Certificate Transparency logs** (crt.sh) — 46 subdomains for xiaomi.com, 44 for mi.com
2. **DNS resolution** — checked which ones still respond
3. **HTTP probing** — poked the ones that came back

The CT logs were clean. That many entries means Xiaomi has been issuing certificates consistently across both domains. They use load balancing (multiple IPs per subdomain), separate domains for regional markets (xiaomi.com = global, mi.com = Asia), and what looks like a well-structured service landscape.

But here's the kicker: most of those 90 subdomains don't respond to DNS. `api.xiaomi.com`? NXDOMAIN. `ai.xiaomi.com`? NXDOMAIN. `oauth.xiaomi.com`? Timeout.

That's either good security (decommissioned endpoints are actually gone) or lazy security (they got issued certs but nobody bothered to clean up DNS when services moved).

## The Live Ones

After DNS resolution and HTTP probing, I found exactly 3 services actually answering:

### 1. **account.xiaomi.com** → 161.117.94.168
HTTP 302 redirect, HTTPS 302 redirect. Centralized auth endpoint. Single IP (not load balanced like the others). Redirects to... somewhere. Typical SSO architecture.

### 2. **app.mi.com** → 101.126.91.123, 124.251.101.62
HTTP 200. "Mi App Store." Nginx. Load balanced across two IPs. IIS in the tech stack (mixed infrastructure). Standard marketplace, nothing jumping out.

### 3. **b.mi.com** → 120.133.33.137, 124.251.34.42
HTTP 200. "Xiaomi Cloud Backend." Nginx + OpenResty (Lua-enhanced). Load balanced. The interesting one. Backend APIs in OpenResty often have logic flaws. Worth investigating.

### Bonus: **market.xiaomi.com**
HTTP 200. "Xiaomi Market." Apache + PHP 7.4. PHP 7.4 reached end-of-life in November 2022. Old stack. Could be legacy and neglected, could be intentionally minimal. Either way, it's interesting.

## What the Null Results Tell You

The timeouts on `oauth.xiaomi.com`, `cloud.xiaomi.com`, `iot.xiaomi.com` etc. aren't necessarily dead — they're inaccessible. Could be:

- Firewalled to specific IP ranges (internal only, CI/CD pipelines, partner networks)
- GeoIP blocked (my scanning origin isn't in Xiaomi's approved regions)
- Legitimately down but certificate still valid in CT logs
- Deliberately timeout-inducing to frustrate mass scanning

Xiaomi's big enough that they can afford to be selective about who sees what.

## Phase 2 (Next Up)

Nuclei scanning against the three live services. Looking for:
- Outdated PHP vulnerabilities (SQLi, XXE, RFI)
- OpenResty misconfigurations (Lua injection, improper access control)
- Authentication bypass vectors
- API parameter enumeration

The fact that 87/90 subdomains are basically ghosts suggests Xiaomi's cleanup process is either excellent (actually delete unused stuff) or they're running security through attrition — make it hard enough to find the real endpoints and maybe you'll give up.

We won't.

---

**Engagement:** Xiaomi HackerOne BB Program  
**Phase:** 1/5  
**Status:** Live recon, Phase 2 in progress  
**CVSS findings:** TBD
