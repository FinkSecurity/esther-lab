# Xiaomi Bug Bounty — Task Brief

**Engagement:** Xiaomi HackerOne Bug Bounty Program  
**Start Date:** Fri 2026-04-03 22:18 UTC  
**Status:** Active  
**Program Type:** Public Vulnerability Disclosure Program (VDP)  

## Program Overview

Xiaomi is a global consumer electronics company focused on smartphones, IoT devices, and cloud services. The HackerOne program covers:

- Web applications (xiaomi.com, mi.com, miui.com and subdomains)
- Cloud services (account management, storage, sync)
- Mobile applications (Mi Home, Mi Fit, others)
- Developer portals and APIs
- Regional service deployments

Bounties range from $100 (Low) to $5,000+ (Critical), with expedited payouts for high-severity vulnerabilities.

## Bounty Tiers (Estimated)

| Severity | Range | Example |
|----------|-------|---------|
| Critical | $1,000–$5,000+ | RCE, auth bypass, data breach |
| High | $500–$2,000 | Privilege escalation, SSRF |
| Medium | $200–$1,000 | XSS, SQLi, weak auth |
| Low | $100–$300 | Information disclosure, misconfiguration |
| Info | Up to $100 | Best practices, low-risk notes |

## Scope Summary

**In-Scope:** All Xiaomi-operated domains, APIs, cloud services, mobile apps  
**Out-of-Scope:** Third-party vendors, DoS, social engineering, physical testing, deprecated systems

## Phase 1: Passive Reconnaissance (This Phase)

**Objective:** Map the attack surface without active probing or engagement

### Deliverables

1. **Complete subdomain enumeration** (xiaomi.com, mi.com, miui.com, others)
2. **IP range discovery** via WHOIS and ASN lookups
3. **Service fingerprinting** via passive Shodan queries
4. **Technology stack identification** (frameworks, CMS, web servers)
5. **Historical data collection** (Wayback Machine, DNS history, certificate transparency)
6. **Initial vulnerability patterns** (known CVE patterns, misconfigurations)

### Tools & Commands

- **theHarvester** — Passive data gathering from public sources
- **amass** — Subdomain enumeration
- **crt.sh** — Certificate transparency logs
- **WHOIS / DNSrecon** — DNS and IP ownership data
- **Shodan** — Passive device/service discovery
- **Wayback Machine** — Historical snapshots

### Output

- `findings/phase-1-passive-recon.md` — Complete inventory of discovered assets, IPs, services, and vulnerabilities
- Git commit after each tool completion with real SHA verification

## Phase 2: Active Scanning (Pending)

- Port scanning and service enumeration
- Vulnerability scanning (nuclei templates)
- Application scanning for common misconfigurations
- API endpoint discovery and analysis

## Phase 3: Manual Testing (Pending)

- Web application penetration testing
- Authentication/authorization flaws
- Business logic vulnerabilities
- PoC development for high-impact findings

## Phase 4: Reporting & Submission (Pending)

- Vulnerability verification and impact assessment
- HackerOne submission workflow
- Timeline coordination with Xiaomi security team
- Remediation verification and bounty collection

## Success Criteria (Phase 1)

✅ Complete passive surface map without detection  
✅ Identify all major subdomains and services  
✅ Discover potential vulnerability vectors  
✅ Document baseline for active testing  
✅ No IDS/WAF alerts (passive-only)  

## Known Risks & Constraints

- **Rate limits:** Respect API rate limits on free OSINT tools
- **Passive-only:** Phase 1 must not trigger IDS/WAF alerts
- **Public data only:** Use only publicly available sources
- **Legal compliance:** All testing within HackerOne program rules

## Next Steps

1. Execute Phase 1 tools (theHarvester, amass, Shodan)
2. Document findings in phase-1-passive-recon.md
3. Commit with real SHA verification
4. Brief operator on discoveries before Phase 2
5. Proceed to active scanning if operator approves

---

**Engagement Directory:** ~/esther-lab/engagements/public/xiaomi/  
**Findings:** ~/esther-lab/engagements/public/xiaomi/findings/  
**Submissions:** ~/esther-lab/engagements/public/xiaomi/submissions/
