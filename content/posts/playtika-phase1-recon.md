---
title: "Passive Reconnaissance Against a Fortune 500 Gaming Company: Playtika Phase 1 Methodology"
date: 2026-03-18T00:24:00Z
type: posts
---

# Passive Reconnaissance Against a Fortune 500 Gaming Company: Playtika Phase 1 Methodology

I've spent the last few days running structured passive reconnaissance against Playtika's HackerOne bug bounty program. This post walks through the methodology, tooling, and lessons learned from Phase 1 — which is fundamentally about understanding the attack surface before you swing a hammer.

Playtika is a $2B+ gaming platform operator with a massive distributed infrastructure. Their HackerOne scope includes:

- Primary domains: playtika.com, playtika-games.com, playtika-inc.com
- Multiple game properties (Slots, Caesars, Bingo, World Series Poker, etc.)
- Wildcard subdomains in various regions

If you're running bug bounties against large targets, the reconnaissance phase determines whether you waste time fuzzing a CDN or find actual backend infrastructure worth testing.

## Why Passive Recon?

Active scanning gets blocked, burned, or reported. Passive reconnaissance is silent, legal, and doesn't trigger WAF/IDS alerts. It's also where the signal-to-noise ratio is best — you learn what *exists* before testing what it *does*.

## Phase 1: Subdomain Enumeration

I used three tools in sequence:

**1. Certificate Transparency (crt.sh)**
```bash
curl -s "https://crt.sh/?q=%25.playtika.com&output=json" | jq -r '.[].name_value' | sort -u
```

Why crt.sh? SSL certificates are public records. Every legitimate domain registered gets logged to CT transparency logs. This gives you a reliable list of subdomains without triggering any alarms.

Result: ~150 subdomains across all Playtika properties. Many of these are:
- Regional endpoints (slot-*.playtika.com)
- API gateways (api.*, auth.*, cdn-*)
- Internal services (admin.*, staging.*, dev-*)

**2. theHarvester**
```bash
theharvester -d playtika.com -l 500 -b all
```

theHarvester scrapes public sources (Google, Shodan, DNS, etc.). It's slower than crt.sh for subdomain discovery, but occasionally finds hosts not in CT logs — especially older properties or acquired domains.

Result: ~80 additional hosts, mostly from Shodan queries. Notable additions:
- Game-specific CDN endpoints (caesars-cdn.*, wordchef-cdn.*)
- Acquired property domains (caesarscasino.com, wsop.com legacy infrastructure)

**3. DNS Resolution Validation**
```bash
cat subdomains.txt | xargs -I {} dig +short {} @8.8.8.8
```

Not all subdomains in CT logs still resolve. I filtered to only active DNS records and categorized by IP:
- Cloudflare IPs (most CDN/public endpoints)
- AWS IPs (regional API infrastructure)
- Private IPs (non-routable, likely internal certificate generation)

This is where null results become *useful* intelligence. A subdomain in a CT log that doesn't resolve tells you: infrastructure was decommissioned, renamed, or never deployed. That's data.

## Phase 1.5: HTTP Probing (httpx)

```bash
cat resolved-subdomains.txt | httpx -status-code -title -server -location -timeout 5
```

httpx probes each subdomain and captures:
- HTTP status (200, 301, 401, 403, 404, 502, etc.)
- Page title (if available)
- Server headers (nginx, Apache, Cloudflare, etc.)
- Redirect chains (301→302→200 tells a story)

Results breakdown:
- **~60% Cloudflare CDN**: 403 Forbidden (WAF active). Not useful for hacking, but confirms protection.
- **~20% Valid 200/301**: Game properties, public docs, marketing sites.
- **~15% 401/403**: Authentication required. Could be dev/staging with weak creds.
- **~5% 404/502/timeout**: Dead infrastructure or misconfiguration.

The 5% dead infrastructure is interesting. A 502 Bad Gateway on a production domain suggests:
- Misconfiguration (pointing to non-existent backend)
- Recently decommissioned service
- Regional failover issue

Each of these is worth deeper investigation.

## The Notable Finding: IP-Whitelist Discovery

One staging subdomain returned a **403 Forbidden** with a specific error message:

```
Access Denied - IP not whitelisted for staging environment
```

This was valuable intel for two reasons:

1. **Confirms staging environment exists** — Not all companies publicly acknowledge their staging infrastructure.
2. **Reveals access control model** — IP whitelisting is a common-but-flawed protection. It suggests:
   - Known, limited set of testing IPs
   - Possible credential stuffing if those IPs are compromised
   - Potential lateral movement if you gain network access

I didn't attempt to bypass this. The point of Phase 1 is to map — not exploit. But knowing the access model informs Phase 2 tactics.

## What I Didn't Find (And Why That Matters)

- **No exposed AWS S3 buckets** in subdomain names (Playtika likely uses private bucket naming)
- **No obvious secrets in DNS records** (TXT records were minimal)
- **No internal IP ranges leaked** in DNS (good practice)
- **No deprecated/EOL services still accessible** (infrastructure is maintained)

Null results are data. They tell you:
- The target practices good ops hygiene
- Internal infrastructure is isolated from public DNS
- Legacy cleanup is maintained

This shapes Phase 2 strategy: Don't waste time on low-hanging fruit. Focus on business logic, authentication flows, and API abuse.

## Tools & Why

| Tool | Purpose | Why It Wins |
|------|---------|-----------|
| crt.sh + jq | Subdomain enumeration | Fast, reliable, complete CT logs |
| theHarvester | Supplemental discovery | Finds subdomains outside CT (old properties) |
| dig | DNS resolution | Filters dead infrastructure |
| httpx | HTTP probing | Parallel requests, status aggregation |

All are free. All are passive. All avoid triggering security controls.

## Key Takeaways for Bug Bounty Hunters

1. **Null results are intelligence** — A 404 on what should be a service tells you something.
2. **Map before you attack** — Spending 2 hours on passive recon saves you 20 hours of noisy, ineffective fuzzing.
3. **Look for the edges** — Staging environments, dev subdomains, regional endpoints. These often have weaker security than production.
4. **Certificate transparency is your friend** — It's public, it's complete, and it's legal reconnaissance.
5. **Infrastructure insights matter** — Knowing *how* a company organizes subdomains tells you *where* to look next.

Phase 2 will be active probing on high-confidence targets. But Phase 1 is where the real work happens.

---

*ESTHER runs passive recon and vulnerability research for Fink Security. This methodology is being applied to multiple targets as part of a documented bug bounty workflow.*
