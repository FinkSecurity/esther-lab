# Fink Security — Bug Bounty Operators Manual

A hands-on reference guide for executing security testing tasks from passive reconnaissance through HackerOne submission.

---

## 1. Passive Reconnaissance

Passive reconnaissance gathers intelligence without touching target infrastructure. Zero footprint.

### 1.1 theHarvester — Email & Subdomain Discovery

**What it does:** Aggregates data from public sources (Google, Bing, Yahoo, DNS brute-force dictionaries) to find subdomains and email addresses associated with a domain.

**Installation check:**
```bash
python3 -m theHarvester --version
```

**Basic usage:**
```bash
python3 -m theHarvester -d xiaomi.com -b all -l 500
```

**Flags explained:**
- `-d` — Domain to search
- `-b` — Data sources (all, google, bing, yahoo, baidu, etc.)
- `-l` — Result limit per source

**Expected output:** List of subdomains, IP addresses, email addresses discovered from public records.

**How to interpret:** Each subdomain is a potential attack surface. Look for:
- API endpoints (api.*, v1.*, v2.*)
- Admin/internal services (admin.*, internal.*, staging.*)
- Regional variants (cn.*, eu.*, us.*)
- Development/test systems (dev.*, test.*, qa.*)

---

### 1.2 Certificate Transparency — crt.sh

**What it does:** Queries the Certificate Transparency (CT) log — a public record of every SSL/TLS certificate issued. Reveals all subdomains that have ever been issued certificates.

**Installation check:** None needed — curl + Python built-in.

**Basic usage — xiaomi.com:**
```bash
curl -s "https://crt.sh/?q=%.xiaomi.com&output=json" | python3 -c "import json,sys; [print(d['name_value']) for d in json.load(sys.stdin)]" | sort -u
```

**Basic usage — mi.com:**
```bash
curl -s "https://crt.sh/?q=%.mi.com&output=json" | python3 -c "import json,sys; [print(d['name_value']) for d in json.load(sys.stdin)]" | sort -u
```

**What each part does:**
- `curl -s "https://crt.sh/?q=%.domain.com&output=json"` — Query CT logs for all subdomains (% = wildcard)
- `python3 -c "..."` — Parse JSON, extract certificate names
- `sort -u` — Deduplicate results

**Expected output:**
```
account.xiaomi.com
ai.xiaomi.com
api.xiaomi.com
market.xiaomi.com
...
```

**How to interpret:** Every entry here represents a host that was issuing HTTPS certificates at some point. Active = likely still running. Orphaned = decommissioned but may still resolve.

---

### 1.3 WHOIS & ASN Lookups

**What it does:** Retrieves domain registration and network ownership metadata.

**Basic usage:**
```bash
whois xiaomi.com
whois mi.com
```

**Key information to extract:**
- Registrar and registration date
- Name servers
- Administrative contact details (often redacted)
- Hosting provider ASN (Autonomous System Number)

**Example interpretation:**
```
Domain Name: XIAOMI.COM
Registrar: MarkMonitor Inc.
Name Server: ns1.xiaomi.com
Registrant Country: CN
```

This tells you:
- Domain registered with MarkMonitor (common for large enterprises)
- Uses custom nameservers (self-hosted DNS)
- Registrant in China (relevant for geolocation)

---

### 1.4 DNS Enumeration — dig, host, nslookup

**What it does:** Queries DNS servers to resolve subdomains and retrieve records.

**Basic usage — single lookup:**
```bash
dig api.xiaomi.com +short
host api.xiaomi.com
nslookup api.xiaomi.com
```

**Zone transfer attempt (may fail, but try):**
```bash
dig axfr xiaomi.com @ns1.xiaomi.com
```

**Reverse DNS lookup (IP to hostname):**
```bash
dig -x 1.2.3.4
```

**Expected output:**
```
api.xiaomi.com.        300     IN      A       202.120.2.5
```

**How to interpret:**
- Resolves = host is live
- NXDOMAIN = host doesn't exist (but might be in scope for takeover testing)
- Points to CDN (Cloudflare, Akamai) = WAF/DDoS protection in place

---

### 1.5 Wayback Machine — Historical Snapshots

**What it does:** Archives snapshots of websites over time. Reveals old endpoints, parameters, and functionality that may no longer be documented.

**Basic usage:**
```bash
curl -s "https://archive.org/wayback/available?url=xiaomi.com&output=json" | python3 -m json.tool
```

**Manual browsing:**
Visit https://web.archive.org/web/*/xiaomi.com/ and browse snapshots by year.

**How to interpret:**
- Old parameter names reveal API structure
- Archived endpoints may still respond
- Functionality may have moved but not been removed
- Version numbers in URLs indicate versioning schemes

---

### 1.6 Google Dorks

**What it does:** Uses Google's advanced search operators to find publicly indexed content.

**Examples:**
```bash
# Find subdomains indexed by Google
site:xiaomi.com filetype:pdf

# Find API endpoints
site:xiaomi.com/api

# Find exposed admin panels
site:xiaomi.com "admin" OR "login" OR "panel"

# Find database backups
site:xiaomi.com filetype:sql

# Find credentials or secrets
site:xiaomi.com "password" OR "api_key" OR "token"
```

**How to interpret:** Manual review required. Many results will be false positives, but even one exposed secret is a finding.

---

## 2. Subdomain Enumeration

Expand the subdomain list beyond CT logs. These tools are still passive — no network traffic to targets.

### 2.1 amass — Intelligent Subdomain Enumeration

**What it does:** Combines multiple data sources (DNS, certificates, APIs, Shodan) to discover subdomains. More comprehensive than theHarvester.

**Installation check:**
```bash
amass -version
```

**Basic usage (passive only):**
```bash
amass enum -passive -d xiaomi.com -o /tmp/amass-xiaomi.txt
```

**Flags:**
- `-passive` — Passive sources only (no active DNS queries)
- `-d` — Domain
- `-o` — Output file

**Expected output:** One subdomain per line.

**How to interpret:** Focus on patterns:
- API subdomains (`v1.api.xiaomi.com`, `api-staging.xiaomi.com`)
- Geographic regions (`cn.xiaomi.com`, `eu.xiaomi.com`)
- Service categories (`cloud.xiaomi.com`, `iot.xiaomi.com`)

---

### 2.2 httpx — Live Host Probing

**What it does:** Probes discovered subdomains for HTTP/HTTPS responses, titles, status codes, and technology stack.

**Installation check:**
```bash
httpx -version
```

**Basic usage:**
```bash
cat subdomains.txt | httpx -title -tech-detect -status-code -follow-redirects
```

**Flags:**
- `-title` — Extract page title
- `-tech-detect` — Identify web frameworks (WordPress, React, etc.)
- `-status-code` — HTTP response code
- `-follow-redirects` — Follow 30x redirects
- `-o` — Output file

**Example output:**
```
https://api.xiaomi.com [200] [title: Xiaomi API] [NextJS, Nginx]
https://admin.xiaomi.com [403] [title: Access Denied]
https://staging.xiaomi.com [200] [title: Xiaomi Staging] [Express, MongoDB]
```

**How to interpret:**
- 403/401 = authentication required (possible auth bypass)
- 200 with unexpected title = misconfigured or unintended endpoint
- Technology stack reveals known vulnerabilities (old Express versions, unpatched CMS)
- Redirects reveal internal structure

---

## 3. Active Scanning

Now we touch the targets. Stay in-scope per HackerOne rules.

### 3.1 nmap — Port Scanning & Service Detection

**What it does:** Discovers open ports, identifies running services, and detects OS/version information.

**Installation check:**
```bash
nmap -version
```

**Basic usage — SYN scan (default):**
```bash
nmap -sS -p- xiaomi.com
```

**Service detection:**
```bash
nmap -sV -p 80,443,8080,8443 xiaomi.com
```

**Aggressive scanning (version + OS detection):**
```bash
nmap -A -p- xiaomi.com
```

**Flags:**
- `-sS` — SYN scan (stealth, fast)
- `-p-` — All 65535 ports
- `-sV` — Service version detection
- `-A` — Aggressive (OS, version, script)
- `-o` — Output file

**Expected output:**
```
PORT    STATE  SERVICE VERSION
80/tcp  open   http    nginx 1.19.0
443/tcp open   https   nginx 1.19.0
8080/tcp open  http    Apache Tomcat 9.0.1
```

**How to interpret:**
- Old versions = known CVEs (nginx 1.19.0 is outdated)
- Unexpected ports (8080, 8443) = development/admin services
- All ports filtered = WAF in place

---

### 3.2 nuclei — Vulnerability Scanning

**What it does:** Runs templates against targets to detect known vulnerabilities, misconfigurations, and security issues.

**Installation check:**
```bash
nuclei -version
```

**Script wrapper for our engagements:**
```bash
python3 ~/esther-lab/scripts/nuclei-scan.py --targets targets.txt --output findings.md
```

**Direct usage:**
```bash
nuclei -l targets.txt -t ~/nuclei-templates/cves/ -o /tmp/nuclei-results.txt
```

**Flags:**
- `-l` — Target list file
- `-t` — Template directory
- `-o` — Output file
- `-severity` — Filter by severity (critical, high, medium, low)

**Expected output:**
```
[CVE-2021-XXXXX] https://api.xiaomi.com/endpoint [Critical]
[Nginx-Version-Disclosure] https://xiaomi.com [Low]
[SSL-Outdated-Protocol] https://xiaomi.com [Medium]
```

**How to interpret:**
- Critical/High findings are reportable
- Low findings (info disclosure) still have value
- Cluster results by endpoint to identify patterns

---

### 3.3 nikto — Web Server Scanning

**What it does:** Scans web servers for misconfigurations, outdated software, and known vulnerabilities.

**Installation check:**
```bash
nikto -version
```

**Basic usage:**
```bash
nikto -h https://api.xiaomi.com -o /tmp/nikto-results.txt
```

**Flags:**
- `-h` — Target host
- `-p` — Port
- `-o` — Output file
- `-Tuning` — Scan categories (1-9)

**Expected output:**
```
+ Server: Nginx/1.19.0
+ /admin/ — Directory indexing enabled
+ Outdated Apache detected
+ Cookies without HttpOnly flag
```

**How to interpret:** Similar to nuclei — focus on critical/high findings first.

---

### 3.4 ffuf — Directory & Parameter Fuzzing

**What it does:** Brute-forces URL paths and parameters to discover hidden endpoints and functionality.

**Installation check:**
```bash
ffuf -version
```

**Basic usage — directory fuzzing:**
```bash
ffuf -u https://api.xiaomi.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -o /tmp/ffuf-dirs.txt
```

**Parameter fuzzing:**
```bash
ffuf -u "https://api.xiaomi.com/user?FUZZ=test" -w /usr/share/wordlists/dirb/common.txt -o /tmp/ffuf-params.txt
```

**Flags:**
- `-u` — Target URL (FUZZ = variable to replace)
- `-w` — Wordlist
- `-o` — Output file
- `-mc` — Match HTTP codes (e.g., -mc 200,301)
- `-fc` — Filter HTTP codes (e.g., -fc 404)

**Expected output:**
```
/api/v1/users [200]
/api/v1/accounts [200]
/admin/panel [403]
```

**How to interpret:** 200 responses are interesting. 403 responses indicate protected but accessible paths.

---

## 4. Web Application Testing

Manual testing for logic flaws and auth bypass.

### 4.1 curl — Endpoint Probing & Request Manipulation

**What it does:** Sends custom HTTP requests to test authentication, authorization, and parameter handling.

**Basic GET request:**
```bash
curl -v https://api.xiaomi.com/user/profile
```

**POST with data:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  https://api.xiaomi.com/login
```

**Custom headers (auth bypass):**
```bash
curl -H "Authorization: Bearer fake-token" \
  -H "X-Admin-Override: true" \
  https://api.xiaomi.com/admin/users
```

**Cookie manipulation:**
```bash
curl -b "session_id=12345; admin=true" \
  https://api.xiaomi.com/admin/settings
```

**How to interpret:**
- If endpoints respond to fake tokens = auth bypass
- If admin=true cookie works = broken access control
- Errors reveal internal structure and technology

---

### 4.2 IDOR Testing — Insecure Direct Object References

**Pattern:** Sequential or predictable IDs in URLs.

**Example from Xiaomi:**
```bash
# User 1's profile
curl https://api.xiaomi.com/user/1/profile

# Try user 2
curl https://api.xiaomi.com/user/2/profile

# Try admin (common ID)
curl https://api.xiaomi.com/user/999/profile
```

**If user 2's data is returned:** IDOR vulnerability.

**Also try:**
- UUID modification (change last character)
- Base64 encoding (ID might be base64)
- Timestamp-based (use current timestamp ±1)

---

### 4.3 Authentication Bypass Techniques

**Default credentials:**
```bash
curl -u admin:admin https://api.xiaomi.com/admin
curl -u admin:password https://api.xiaomi.com/admin
curl -u admin:123456 https://api.xiaomi.com/admin
```

**JWT token manipulation:**
```bash
# Copy a valid JWT from response, modify payload, re-encode
# If server accepts it = weak validation
```

**Session fixation:**
```bash
# Set custom session ID in request
# If server accepts it = vulnerability
```

**Null byte injection:**
```bash
curl "https://api.xiaomi.com/admin%00.php"
```

---

## 5. Credential & Breach Intelligence

### 5.1 HaveIBeenPwned (HIBP) — Breach Database Checks

**What it does:** Searches a database of 12+ billion compromised credentials.

**Online check:**
Visit https://haveibeenpwned.com and search email addresses found during recon.

**Via API (requires key):**
```bash
curl -H "User-Agent: Fink-Security" \
  "https://haveibeenpwned.com/api/v3/breachedaccount/email@xiaomi.com"
```

**How to interpret:** If Xiaomi employee emails appear in breaches, credential stuffing is possible.

---

### 5.2 Password Cracking — hashcat & john

**hashcat — GPU-accelerated cracking:**
```bash
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt -o cracked.txt
```

**john the ripper — CPU cracking:**
```bash
john hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

Only use on passwords you've obtained with authorization (from a vuln you found, after HackerOne scope approval).

---

## 6. Exploitation Frameworks

### 6.1 Metasploit — Basic Workflow

**Check if service is vulnerable:**
```bash
msfconsole
> db_connect
> nmap -Pn -sV -p- 192.168.1.1 -oX output.xml
> db_import output.xml
> services
```

**Search for exploits:**
```bash
> search CVE-2021-XXXXX
> show options
> set RHOSTS 192.168.1.1
> exploit
```

**Only use on lab targets or explicitly in-scope HackerOne assets.**

---

### 6.2 Impacket Tools — Network Exploitation

Common tools for testing network services:

```bash
# SMB enumeration
smbclient -L //target

# Kerberos authentication
GetUserSPN.py domain/user:password
```

---

## 7. Finding Documentation

### 7.1 Finding Template

Every finding should follow this structure:

```markdown
## Vulnerability Title

**Severity:** [Critical/High/Medium/Low]  
**Type:** [XSS/SQLi/IDOR/Auth Bypass/etc.]  
**Endpoint:** [https://api.xiaomi.com/path]  

### Description
Clear explanation of the vulnerability. What it is, why it's bad, who can exploit it.

### Proof of Concept
```bash
curl -v https://api.xiaomi.com/vulnerable-endpoint \
  -H "Authorization: Bearer eyJhbGc..."
```

**Result:**
```
HTTP/1.1 200 OK
{
  "user_id": 2,
  "username": "other_user",
  "email": "other@xiaomi.com"
}
```

### Impact
What an attacker can do with this. Data theft? Account takeover? Service disruption?

### Remediation
How to fix it. Replace vulnerable library? Add input validation? Enable HTTPS-only cookies?

### Timeline
- 2026-04-04: Initial discovery
- 2026-04-05: HackerOne submission
- 2026-04-12: Xiaomi acknowledged
- [Pending remediation date]
```

---

### 7.2 CVSS Scoring

Use CVSS 3.1 calculator: https://www.first.org/cvss/calculator/3.1

**Quick reference:**
- **Critical:** 9.0–10.0 (e.g., unauthenticated RCE)
- **High:** 7.0–8.9 (e.g., auth bypass, privilege escalation)
- **Medium:** 4.0–6.9 (e.g., XSS, SQLi with auth required)
- **Low:** 0.1–3.9 (e.g., info disclosure, DoS on non-critical service)

---

### 7.3 Evidence Collection

Always include:
- Full request/response (curl -v output)
- Screenshots (if web app)
- Command syntax used
- Timestamps
- Tool versions

Paste everything verbatim. No fabrication.

---

## 8. HackerOne Submission Workflow

### 8.1 Pre-Submission Checklist

- [ ] Vulnerability confirmed and reproducible
- [ ] Proof of concept documented
- [ ] CVSS score calculated
- [ ] Impact assessment complete
- [ ] No sensitive data leaked in PoC
- [ ] Verification that finding is in-scope per program rules
- [ ] Remediation recommendation included

### 8.2 Submission Structure

1. **Title** — Clear, specific (e.g., "SQL Injection in User Search API")
2. **Summary** — 2-3 sentence overview
3. **Vulnerability Details** — Full description
4. **Proof of Concept** — Step-by-step reproduction
5. **Impact** — What attacker can do
6. **Remediation** — How to fix it
7. **Timeline** — Discovery date, submission date

### 8.3 Expected Response Timeline

- **Day 1–3:** Program triages and acknowledges
- **Day 3–7:** Security team validates finding
- **Day 7–14:** Fix development begins
- **Day 14–30:** Fix deployed to production
- **Day 30+:** Bounty paid, program publishes report

---

## Quick Reference: Command Cheat Sheet

```bash
# Certificate transparency
curl -s "https://crt.sh/?q=%.domain.com&output=json" | python3 -c "import json,sys; [print(d['name_value']) for d in json.load(sys.stdin)]" | sort -u

# DNS enumeration
dig domain.com +short
dig axfr domain.com @ns1.domain.com

# Subdomain enumeration
amass enum -passive -d domain.com

# Live host probing
cat subdomains.txt | httpx -title -tech-detect -status-code

# Port scanning
nmap -sS -p- domain.com

# Web vulnerability scanning
nuclei -l targets.txt -o findings.txt

# Directory fuzzing
ffuf -u https://domain.com/FUZZ -w wordlist.txt

# IDOR testing
curl https://api.domain.com/user/1/profile
curl https://api.domain.com/user/2/profile

# Auth bypass
curl -u admin:admin https://api.domain.com/admin
```

---

**Last Updated:** 2026-04-04  
**Author:** ESTHER  
**Status:** Live Reference Document
