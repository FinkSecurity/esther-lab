# Xiaomi Bug Bounty Program — Scope

**Program:** Xiaomi on HackerOne  
**Type:** Public Bug Bounty (VDP)  
**URL:** https://hackerone.com/xiaomi  
**Engagement Start:** Fri 2026-04-03 22:18 UTC  

## In-Scope Assets

### Domains & Subdomains

- xiaomi.com (all subdomains)
- mi.com (all subdomains)
- miui.com (all subdomains)
- Global and regional variants:
  - Xiaomi global properties
  - Regional cloud services (China, APAC, EU)
  - Developer portals and API endpoints

### Services & Applications

- Xiaomi cloud services (account, storage, sync)
- Mi Home / Mi Fit applications
- Xiaomi mobile devices (firmware, boot loaders)
- Developer tools and SDKs
- Official mobile applications (Android/iOS)
- Web applications for account management, forums, e-commerce integration points

### Security Scope Details

- Web application vulnerabilities (XSS, CSRF, SQLi, LFI, RFI, etc.)
- Authentication and authorization flaws
- API vulnerabilities
- Mobile app vulnerabilities
- Cloud infrastructure misconfiguration
- Data exposure and privacy issues
- Server-side request forgery (SSRF)
- Security misconfigurations
- Insecure deserialization
- Cryptographic failures

## Out-of-Scope Assets

### Explicitly Excluded

- Third-party services (unless directly integrated into Xiaomi services)
- Social engineering and phishing
- Physical security testing
- Denial of service (DoS/DDoS)
- Brute force attacks without authorization
- Testing on production systems without explicit permission
- Xiaomi partner/affiliate websites (unless explicitly listed)
- Outdated or deprecated systems
- Security research that impacts user privacy or data integrity without mitigation

## Bounty Tiers

_(To be updated from HackerOne program page — typical ranges:)_

- **Critical:** $1,000–$5,000+ (RCE, authentication bypass, data breach)
- **High:** $500–$2,000 (Significant vulnerability with clear impact)
- **Medium:** $200–$1,000 (Moderate vulnerability, requires specific conditions)
- **Low:** $100–$300 (Low-impact issues, information disclosure)
- **Informational:** Up to $100 (Best practices, low-risk findings)

## Program Rules

1. **Report Responsibly** — No public disclosure until Xiaomi has time to patch
2. **Testing Authorization** — Testing only on in-scope assets
3. **No Disruption** — Do not cause service outages or impact production systems
4. **Legal Compliance** — Follow all local laws; no illegal activity
5. **No Credential Reuse** — Do not use credentials found in other breaches
6. **Payment** — Bounties paid via HackerOne platform

## Key Subdomains & Services to Investigate

_(Initial reconnaissance targets:)_

- account.xiaomi.com (user authentication, profile)
- cloud.xiaomi.com (cloud services)
- api.xiaomi.com (API endpoints)
- developer.xiaomi.com (developer portal)
- forum.xiaomi.com (user forum)
- store.xiaomi.com (e-commerce)
- game.xiaomi.com (gaming services)
- miui.com (MIUI OS portal)
- mi.com (global site, regional variants)

## Testing Phases

### Phase 1: Passive Reconnaissance
- Subdomain enumeration (amass, crt.sh, theHarvester)
- DNS record collection (WHOIS, DNS queries)
- Shodan queries for exposed services
- Historical data (Wayback Machine, DNS history)
- IP range discovery

### Phase 2: Active Scanning
- Port scanning (nmap)
- Web server fingerprinting (httpx, banner grabbing)
- Application scanning (nuclei templates, common CVE patterns)
- Technology stack identification

### Phase 3: Manual Testing
- Web application penetration testing
- API endpoint analysis
- Authentication/authorization testing
- Input validation (SQLi, XSS, command injection)
- Business logic vulnerabilities

### Phase 4: Reporting & Submission
- Vulnerability verification
- Impact assessment
- PoC development (if required)
- HackerOne submission workflow
- Timeline management and remediation follow-up

---

**Next Steps:** Begin Phase 1 passive reconnaissance once scope is committed.
