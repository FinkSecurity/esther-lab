# OPERATORS MANUAL — Security Research & Bug Bounty Reference

**For:** Manual security operators conducting reconnaissance, vulnerability assessment, and bug bounty work  
**Scope:** Hands-on command reference, not infrastructure/organizational commands  
**Updated:** Sat 2026-04-04  

---

## Table of Contents

1. [Passive Reconnaissance](#passive-reconnaissance)
2. [Active Scanning](#active-scanning)
3. [Web Application Testing](#web-application-testing)
4. [Network Analysis](#network-analysis)
5. [Credential & Breach Checking](#credential--breach-checking)
6. [Exploitation Frameworks](#exploitation-frameworks)
7. [Findings Documentation](#findings-documentation)
8. [HackerOne Submission Workflow](#hackerone-submission-workflow)
9. [Common Patterns & Troubleshooting](#common-patterns--troubleshooting)

---

## Passive Reconnaissance

Gather intelligence from public sources without triggering IDS/WAF alerts.

### theHarvester — Email & Host Enumeration

**Installation:**
```bash
pip install theHarvester
```

**Basic Usage:**
```bash
# Search for emails and hosts associated with a domain
python3 -m theHarvester -d example.com -l 500 -b google,bing,yahoo

# Common flags:
# -d DOMAIN          Target domain
# -l LIMIT           Max results per source (default: 500)
# -b SOURCES         Data sources (google,bing,yahoo,duckduckgo,etc)
# -f FILE            Save results to file (HTML, XML, JSON)
```

**Real Example — Xiaomi:**
```bash
python3 -m theHarvester -d xiaomi.com -l 500 -b google,bing,yahoo -f xiaomi-harvester.html
python3 -m theHarvester -d mi.com -l 500 -b google,bing,yahoo
python3 -m theHarvester -d miui.com -l 500 -b google,bing,yahoo
```

**What to Look For:**
- Email addresses (often reveal naming conventions)
- Employee names and roles
- Subdomains discovered through search results
- Service domains (api.*, dev.*, staging.*, etc)
- CDN/hosting providers mentioned in results

---

### AMASS — Advanced Subdomain Enumeration

**Installation:**
```bash
go install -v github.com/OWASP/Amass/v3/...@latest
```

**Passive Mode (No DNS Queries):**
```bash
# Passive enumeration using public data sources only
amass enum -d example.com -passive

# Common flags:
# -d DOMAIN          Target domain
# -passive           Passive mode (no active DNS queries)
# -o FILE            Output file
# -nocolor           Plain text output
```

**Real Example:**
```bash
amass enum -d xiaomi.com -passive -o xiaomi-amass.txt
amass enum -d mi.com -passive
amass enum -d miui.com -passive
```

**Active Mode (With DNS Resolution):**
```bash
# Only after scope approval and Phase 2 active testing authorization
amass enum -d example.com -active -json

# Requires DNS resolution — use only when explicitly approved
```

**Output Analysis:**
- Save results in structured format (JSON, text)
- Look for subdomain patterns (api-, dev-, test-, staging-)
- Note CDN providers and hosting infrastructure
- Track confirmed/unconfirmed subdomains for Phase 2

---

### Certificate Transparency (crt.sh)

**Web Interface Query:**
```bash
# Direct query for domain
curl -s "https://crt.sh/?q=example.com&output=json" | jq '.[] | .name_value' | sort -u

# Real example:
curl -s "https://crt.sh/?q=xiaomi.com&output=json" | jq '.[] | .name_value' | sort -u > xiaomi-certs.txt
```

**Pattern Analysis:**
```bash
# Extract unique subdomains from certificate data
cat xiaomi-certs.txt | tr ',' '\n' | sort -u | grep '*.xiaomi.com'

# Look for wildcard certificates (*.domain.com) — broader coverage
# Look for unusual subdomain patterns (internal naming conventions)
```

**Red Flags in Certificate Data:**
- Staging/test environments (*.staging.*, *.test.*, *.dev.*)
- Internal naming schemes (*.internal.*, *.vpn.*)
- Backup/archive domains (*.backup.*, *.old.*)
- Regional variants that might have weaker security

---

### WHOIS & DNS Enumeration

**WHOIS Lookup — Domain Registration:**
```bash
# Get domain registration and nameserver info
whois example.com

# Parse specific fields:
whois example.com | grep -i "registrar\|nameserver\|admin"

# Real example:
whois xiaomi.com | grep -i "registrar\|nameserver\|updated"
```

**DNS Enumeration:**
```bash
# Standard DNS records
nslookup example.com
dig example.com

# Nameserver query
dig example.com NS

# Mail exchange records
dig example.com MX

# All records
dig example.com ANY

# Reverse DNS lookup (IP to hostname)
dig -x 1.2.3.4
```

**AXFR Zone Transfer (rare but check):**
```bash
# DNS zone transfer attempt (usually fails on modern systems)
dig @ns1.example.com example.com AXFR

# If successful, returns all DNS records for the domain
# Modern systems reject this; failure is expected
```

**Real Pattern:**
```bash
# Identify all Xiaomi nameservers
dig xiaomi.com NS +short

# Query each nameserver for additional info
dig @ns1.xiaomi.com xiaomi.com ANY
```

---

### Shodan Queries — Passive Service Discovery

**Shodan CLI Installation:**
```bash
pip install shodan
shodan init [YOUR_API_KEY]
```

**IP/ASN Lookup:**
```bash
# Find company's IP ranges
shodan org "Xiaomi" --fields ip_str,port,os | head -50

# Search by domain
shodan search "xiaomi.com"

# Search by hostname
shodan search "hostname:xiaomi.com"
```

**Technology Fingerprinting:**
```bash
# Find specific services (Apache, Nginx, etc)
shodan search "xiaomi.com apache"

# Find cloud infrastructure
shodan search "xiaomi.com org:amazon"

# Find databases exposed
shodan search "xiaomi.com elasticsearch port:9200"
```

**Real Example:**
```bash
# Get IP ranges for Xiaomi
shodan org "Xiaomi Inc" --fields ip_str | head -20

# Search for web servers
shodan search "org:xiaomi.com http.title"

# Find exposed admin panels
shodan search "org:xiaomi.com /admin"
```

**Important Notes:**
- Free Shodan account is rate-limited (1 page = 100 results)
- Use filters to narrow results: `org:, country:, port:, os:`
- Paid API gives 10,000 results/month
- Always verify findings before reporting (many false positives)

---

### Wayback Machine & Historical Data

**Command-Line Access:**
```bash
# Query Wayback Machine for historical snapshots
curl -s "https://archive.org/wayback/available?url=example.com" | jq '.archived_snapshots'

# Get list of all snapshots
curl -s "https://api.github.com/repos/iipc/warc-specifications" 
```

**Web Access (Simpler):**
```
https://web.archive.org/web/*/example.com
```

**What to Look For:**
- Older versions of admin panels
- Exposed API documentation
- Historical subdomain listings
- Deprecated but still-running services
- Previous employee email addresses in old pages

---

## Active Scanning

Conduct active probing to identify live services and vulnerabilities.

### NMAP — Port Scanning & Service Enumeration

**Installation:**
```bash
# Already installed on most Linux systems
nmap --version
```

**Basic Port Scan:**
```bash
# Quick scan of top 1000 ports
nmap -sV example.com

# All ports (slow, takes 5-10 mins)
nmap -p- example.com

# Aggressive scan with service version detection
nmap -sV -sC -O example.com

# UDP scan
nmap -sU example.com
```

**Real Example — Xiaomi Subdomain Scan:**
```bash
# Scan discovered subdomains
nmap -sV api.xiaomi.com
nmap -p 80,443,8080,8443 -sV dev.xiaomi.com

# Range scan on discovered IPs
nmap -sV -p 1-10000 1.2.3.0/24
```

**Common Flags:**
```bash
-sV              Service version detection
-sC              Run default NSE scripts
-O               OS fingerprinting
-p PORT_LIST     Specific ports (80,443,8080 or 1-65535)
-p- --              All 65535 ports
-oX FILE         Save results as XML
-A               Aggressive (all options)
-T4              Timing template (faster, risk of missed services)
--script=SCRIPT  Run specific NSE script
```

**Useful NSE Scripts:**
```bash
# Web server enumeration
nmap --script http-title,http-methods,http-headers example.com

# SSL/TLS certificate info
nmap --script ssl-cert example.com

# Detect common vulnerabilities
nmap --script vuln example.com
```

---

### HTTPX — Web Server Probing

**Installation:**
```bash
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
```

**Usage:**
```bash
# Test HTTP connectivity on list of hosts
cat subdomains.txt | httpx -status-code -title -tech-detect

# Common flags:
# -status-code      Show HTTP status code
# -title            Extract page title
# -tech-detect      Detect technologies (frameworks, CMS)
# -ports LIST       Custom ports (80,443,8080)
# -o FILE           Output file
```

**Real Example:**
```bash
# Test all discovered Xiaomi subdomains
cat xiaomi-subdomains.txt | httpx -status-code -title -tech-detect -o xiaomi-http-results.txt

# Test specific ports
cat xiaomi-subdomains.txt | httpx -ports 80,443,8080,8443,3000,5000 -status-code
```

**What Status Codes Mean:**
- 200: OK (accessible)
- 301/302: Redirect (check destination)
- 401/403: Authentication required / Forbidden (potential IDOR)
- 404: Not found
- 500: Server error (potential injection point)
- 502/503: Gateway error (backend service down)

---

### Nuclei — Vulnerability Scanning

**Installation:**
```bash
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
```

**Usage:**
```bash
# Scan URL with default templates
nuclei -u https://example.com

# Scan file of URLs
nuclei -list urls.txt

# Use specific template category
nuclei -u https://example.com -tags cves,misconfig

# Common tags:
# cves               Known CVEs
# misconfig          Misconfiguration issues
# xss                Cross-site scripting
# sqli               SQL injection
# auth               Authentication bypass
```

**Real Example:**
```bash
# Scan all discovered Xiaomi URLs
nuclei -list xiaomi-urls.txt -o xiaomi-nuclei-results.txt

# Focus on specific vulnerability types
nuclei -u https://api.xiaomi.com -tags auth,xss,sqli,misconfig

# Scan with custom templates from engagement
nuclei -u https://xiaomi.com -t ~/esther-lab/nuclei-templates/
```

**Processing Results:**
```bash
# Extract only critical/high severity findings
grep "severity=critical\|severity=high" xiaomi-nuclei-results.txt

# Group by vulnerability type
sort xiaomi-nuclei-results.txt | uniq -c | sort -rn
```

---

### FFUF — Web Path Fuzzing

**Installation:**
```bash
go install -v github.com/ffuf/ffuf@latest
```

**Usage:**
```bash
# Fuzz common paths
ffuf -u https://example.com/FUZZ -w /path/to/wordlist.txt

# Filter results by status code
ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200,301,302

# Recursion (subdirectory fuzzing)
ffuf -u https://example.com/FUZZ -w wordlist.txt -recursion
```

**Real Example:**
```bash
# Find hidden admin panels
ffuf -u https://api.xiaomi.com/FUZZ -w ~/esther-lab/wordlists/api-paths.txt -mc 200,401,403

# API endpoint discovery
ffuf -u https://xiaomi.com/api/v1/FUZZ -w wordlist.txt

# Common wordlists:
# /usr/share/wordlists/dirb/common.txt (Kali Linux)
# ~/esther-lab/wordlists/api-paths.txt (custom)
```

---

### Nikto — Web Server Scanner

**Installation:**
```bash
# Usually pre-installed on Kali Linux
nikto -h
```

**Usage:**
```bash
# Basic scan
nikto -h example.com

# Specify port
nikto -h example.com -p 8080

# SSL/TLS scan
nikto -h https://example.com -ssl

# Output to file
nikto -h example.com -o scan.html -F htm
```

**Real Example:**
```bash
nikto -h https://api.xiaomi.com -o xiaomi-nikto.html -F htm
```

---

## Web Application Testing

Manual testing for application-level vulnerabilities.

### SQL Injection Testing

**SQLMap — Automated SQLi Detection:**
```bash
# Installation
sudo apt-get install sqlmap

# Basic scan on URL parameter
sqlmap -u "https://example.com/search?id=1" -p id

# Common flags:
# -u URL             Target URL
# -p PARAM           Vulnerable parameter
# --dbs              Enumerate databases
# --tables           List tables
# --dump             Extract data
# --risk=3           High risk (more aggressive)
# --level=5          Maximum testing level
```

**Real Example:**
```bash
# Test discovered parameter
sqlmap -u "https://xiaomi.com/search?id=1" -p id --dbs

# Authentication-required scan
sqlmap -u "https://xiaomi.com/account?id=1" -p id --cookie="session=xyz" --dbs
```

**Manual Testing:**
```bash
# Test basic SQLi syntax
curl "https://example.com/search?id=1' OR '1'='1"

# Time-based blind SQLi
curl "https://example.com/search?id=1' AND SLEEP(5)--"

# Boolean-based blind SQLi
curl "https://example.com/search?id=1' AND 1=1--"
curl "https://example.com/search?id=1' AND 1=2--"
```

---

### Cross-Site Scripting (XSS) Testing

**Reflected XSS:**
```bash
# Test input reflection
curl "https://example.com/search?q=<script>alert(1)</script>"

# Common XSS payloads
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<iframe src="javascript:alert(1)">
<body onload=alert(1)>
```

**Stored XSS:**
- Test user profile fields (name, bio, avatar)
- Submit comments or forum posts with XSS payloads
- Verify if payloads execute when page is reloaded

**DOM-Based XSS:**
```bash
# Test client-side JavaScript handlers
# Look for innerHTML, eval(), document.write() usage
# Try manipulating DOM via URL fragments or query strings
```

---

### Cross-Site Request Forgery (CSRF) Testing

**Manual Testing:**
```bash
# Identify state-changing operations (form submissions, API calls)
# Check for CSRF token validation
# Try removing token or using expired token
# Attempt cross-origin requests

# Example: Check if CSRF protection exists
curl -X POST "https://example.com/change-password" \
  -d "old_password=test&new_password=hacked" \
  -b "session=xyz"
# If accepted, CSRF vulnerability likely exists
```

---

### WFUZZ — Parameter Fuzzing

**Installation:**
```bash
pip install wfuzz
```

**Usage:**
```bash
# Fuzz URL parameters
wfuzz -z file,/path/to/wordlist -u "https://example.com?FUZZ=1"

# Fuzz POST parameters
wfuzz -z file,wordlist -X POST -d "user=FUZZ" https://example.com/login

# Hide false positives
wfuzz -z file,wordlist -u "https://example.com?FUZZ=1" --hc 404
```

---

## Network Analysis

### Network Reconnaissance

**Traceroute — Path to Target:**
```bash
traceroute example.com
# Shows hops between your machine and target
```

**Network Range Identification:**
```bash
# Use WHOIS to find ASN and IP ranges
whois -h whois.radb.net "as12345"

# Convert organization to IP ranges
whois "Xiaomi Inc" | grep -i "^inetnum\|^route:"
```

---

## Credential & Breach Checking

### Have I Been Pwned (HIBP) API

**Check for Exposed Credentials:**
```bash
# Check if email in breach database
curl -s "https://haveibeenpwned.com/api/v3/breachedaccount/user@example.com" \
  -H "User-Agent: MyApp"

# Check password strength
# Use pwnedpasswords.com (k-anonymity model)
```

**Command-Line Tool:**
```bash
# Install hibp-checker
pip install hibp-checker

# Check email
hibp-checker user@example.com
```

---

### Credential Stuffing Preparation

**Hashcat — Password Cracking:**
```bash
# Installation
sudo apt-get install hashcat

# Identify hash type
hashcat -a 0 -m 0 hash.txt wordlist.txt  # MD5
hashcat -a 0 -m 1400 hash.txt wordlist.txt  # SHA256
```

**John the Ripper:**
```bash
# Installation
sudo apt-get install john

# Crack password hash
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt

# Unshadow system files
unshadow /etc/passwd /etc/shadow > combined.txt
john combined.txt
```

---

## Exploitation Frameworks

### Metasploit — Vulnerability Exploitation

**Installation:**
```bash
# Pre-installed on Kali Linux
msfconsole
```

**Basic Workflow:**
```bash
# Search for exploit
search apache cve-2021-xxxx

# Use exploit
use exploit/linux/http/apache_xxxx
set LHOST 192.168.1.100
set RHOST target.com
run
```

---

### Impacket — Protocol-Based Attacks

**Installation:**
```bash
pip install impacket
```

**SMB Enumeration:**
```bash
# List shares
smbclient -L //target.com

# Enumerate users
python3 -m impacket.lookupsid target.com/user:pass@target.com
```

---

## Findings Documentation

### Recording Findings Format

**Standard Finding Template:**
```markdown
## Vulnerability: [Title]

**Severity:** Critical / High / Medium / Low  
**CVE:** CVE-2021-XXXXX (if applicable)  
**CVSS Score:** 9.8  

### Description
Clear explanation of what was found and why it matters.

### Proof of Concept
Step-by-step reproduction:
1. Navigate to: https://target.com/path
2. Enter payload: `<script>alert(1)</script>`
3. Observe: JavaScript executes in browser

### Impact
- Attacker can steal session cookies
- Access to authenticated user data
- Potential lateral movement

### Remediation
- Input validation and output encoding
- Implement CSP headers
- Use security.txt guidelines

### References
- CWE-79: Cross-site Scripting
- OWASP Top 10: A03:2021 – Injection
```

---

## HackerOne Submission Workflow

### Before Submission

1. **Verify the Vulnerability:**
   - Reproduce independently
   - Confirm it's within program scope
   - Check it's not already reported

2. **Create Proof of Concept:**
   - Screenshots or video recording
   - Step-by-step instructions
   - No sensitive data in PoC

3. **Check Program Rules:**
   - Read scope carefully
   - Verify severity tier alignment
   - Check bounty ranges

### Submission Steps

1. **Log into HackerOne** → Go to program
2. **Click "Submit Report"**
3. **Fill vulnerability details:**
   - Title: Clear, specific
   - Weakness Type: Select from dropdown
   - Severity: CVSS or program severity
   - URL/Endpoint: Exact location
   - Description: Clear explanation
   - PoC: Steps to reproduce
   - Impact: Business impact

4. **Upload attachments:**
   - Screenshots
   - PoC video (MP4)
   - Logs if relevant

5. **Submit and monitor:**
   - Response time varies (24h-7 days typically)
   - Respond to clarifying questions
   - Track bounty status

### Common Submission Mistakes

- ❌ Reporting already-patched CVEs
- ❌ Submitting findings outside scope
- ❌ Including personal data in PoC
- ❌ Making demands or threats
- ❌ Publicly disclosing before resolution

---

## Common Patterns & Troubleshooting

### API Reconnaissance Patterns

**Common API Paths:**
```
/api/v1/users
/api/v2/products
/api/v3/auth
/graphql
/rest/api/latest/
/jira/rest/api/2/
```

**API Endpoint Discovery:**
```bash
# Check JavaScript for API calls
curl -s https://example.com | grep -o "https://[^\"]*api[^\"]*" | sort -u

# Check network requests (use browser dev tools)
# Review OpenAPI/Swagger specs at /swagger, /api-docs, /openapi.json
```

**Common API Vulnerabilities:**
- Broken authentication (missing/weak token validation)
- IDOR (accessing other users' data via ID manipulation)
- Rate limiting bypass
- Mass assignment (setting unintended fields)
- Exposed API keys in responses

---

### False Positive Filtering

**High HTTP 403 Rate = WAF/IDS Active:**
```bash
# Many 403s indicate protective measures
# Switch to passive reconnaissance
# Use different IP/VPN if possible
# Reduce request rate
```

**Timeouts = Network Lag or Rate Limiting:**
```bash
# Increase timeout
curl -m 30 https://slow.example.com

# Reduce concurrent requests
# Add delays between requests
```

---

### Rate Limiting Management

**Identify Rate Limits:**
```bash
# Watch for 429 (Too Many Requests) responses
# Check response headers for Retry-After
curl -v https://api.example.com | grep -i "x-ratelimit\|retry-after"
```

**Bypass Techniques (Only if Authorized):**
```bash
# Rotate User-Agent
curl -H "User-Agent: Mozilla/5.0" https://api.example.com

# Add delays between requests
for i in {1..100}; do curl https://api.example.com; sleep 2; done

# Rotate IPs (VPN/proxy rotation)
```

---

## Real Engagement Reference Commands

**Xiaomi Engagement — Phase 1 Commands:**

```bash
# Subdomain enumeration
python3 -m theHarvester -d xiaomi.com -l 500 -b google,bing,yahoo
amass enum -d xiaomi.com -passive
curl -s "https://crt.sh/?q=xiaomi.com&output=json" | jq '.[] | .name_value' | sort -u

# IP range discovery
whois xiaomi.com | grep -i "nameserver\|updated"
shodan org "Xiaomi Inc" --fields ip_str | head -20

# Technology fingerprinting
cat xiaomi-subdomains.txt | httpx -status-code -title -tech-detect
```

---

## Tool Comparison Matrix

| Tool | Purpose | Speed | Passive/Active | Scope |
|------|---------|-------|---|---|
| theHarvester | Email/host gathering | Fast | Passive | Public sources |
| AMASS | Subdomain enumeration | Slow | Both | Multi-source |
| Shodan | Service discovery | Fast | Passive | Internet-wide |
| NMAP | Port scanning | Varies | Active | Network-level |
| Nuclei | Vulnerability scanning | Medium | Active | Web applications |
| FFUF | Web path fuzzing | Fast | Active | Single target |
| SQLMap | SQL injection testing | Varies | Active | Application-level |

---

**Last Updated:** Sat 2026-04-04  
**Maintained By:** ESTHER Security Research Agent  
**Repository:** FinkSecurity/esther-lab
