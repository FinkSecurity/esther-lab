# ESTHER — Reconnaissance & Investigation Playbook
<!-- Commit to FinkSecurity/esther-lab as docs/RECON-PLAYBOOK.md -->
<!-- ESTHER reads this at the start of every bug bounty engagement -->
<!-- Last updated: 2026-03-17 -->

---

## CARDINAL RULES

1. **Never scan what you haven't scoped.** Read scope.md before any command.
2. **Never fire all nuclei templates.** Always use targeted categories. 3768 generic templates against `www.` is noise, not reconnaissance.
3. **Never trust harvester output raw.** It contains noise — clean it before probing.
4. **Never skip httpx probing.** You must know what is live before scanning it.
5. **Null results are valid findings.** Document honestly and move on.
6. **Every commit gets gh api verified before reporting.**
7. **Phase 3 (exploitation) requires explicit Operator APPROVE per finding.**

---

## PHASE 1 — PASSIVE RECON

### Goal
Build a subdomain list. Do not touch the target directly.

### Tools & Commands

#### theHarvester
```bash
theHarvester -d <domain> -b all -l 500 \
  -f ~/esther-lab/engagements/public/<program>/findings/harvester-<domain>
# Produces .json, .xml, .txt — all three get committed
```

#### amass (passive only)
```bash
amass enum -passive -d <domain> \
  -o ~/esther-lab/engagements/public/<program>/findings/amass-<domain>.txt
```

#### Certificate Transparency
```bash
curl -s "https://crt.sh/?q=%25.<domain>&output=json" \
  | jq -r '.[].name_value' | sort -u \
  | grep -v '^\*' \
  > ~/esther-lab/engagements/public/<program>/findings/crtsh-<domain>.txt
```

#### Consolidate & Clean
```bash
# Merge all subdomain sources into one clean list
cat \
  ~/esther-lab/engagements/public/<program>/findings/harvester-<domain>.txt \
  ~/esther-lab/engagements/public/<program>/findings/amass-<domain>.txt \
  ~/esther-lab/engagements/public/<program>/findings/crtsh-<domain>.txt \
  2>/dev/null \
  | grep -oP '[a-zA-Z0-9._-]+\.<domain>' \
  | sort -u > /tmp/<domain>-raw-subs.txt

# Remove harvester noise:
# - Pure numeric subdomains (2221.domain.com, 96586.domain.com)
# - Numeric-with-dash prefix (96586-.domain.com)  
# - Single character that isn't a real prefix
grep -v -P '^\d+[\-\.]' /tmp/<domain>-raw-subs.txt \
  | grep -v -P '^[0-9]+\.' \
  | grep -P '^[a-zA-Z][a-zA-Z0-9\-]*\.' \
  > /tmp/<domain>-clean-subs.txt

echo "Raw: $(wc -l < /tmp/<domain>-raw-subs.txt) | Clean: $(wc -l < /tmp/<domain>-clean-subs.txt)"
```

### Phase 1 Output
- `findings/harvester-<domain>.txt/.json/.xml`
- `findings/amass-<domain>.txt`
- `findings/crtsh-<domain>.txt`
- `/tmp/<domain>-clean-subs.txt` (working file, not committed)

### Commit
```bash
cd ~/esther-lab
git add engagements/public/<program>/findings/
git commit -m "Phase 1: passive recon <domain> — N subdomains discovered"
git push
# VERIFY before reporting:
gh api repos/FinkSecurity/esther-lab/commits?path=engagements/public/<program>/findings\&per_page=1 \
  --jq '.[0] | {sha: .sha[:9], message: .commit.message}'
```

---

## PHASE 2 — ACTIVE SCANNING

**Requires Operator APPROVE before starting each domain.**

### Step 1 — HTTP Probe (always first)

Never run nuclei against a raw subdomain list. Probe first.

```bash
# Install httpx if missing
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

httpx -l /tmp/<domain>-clean-subs.txt \
  -status-code \
  -title \
  -tech-detect \
  -follow-redirects \
  -rate-limit 10 \
  -timeout 10 \
  -o ~/esther-lab/engagements/public/<program>/findings/httpx-<domain>.txt

# Count live hosts
wc -l ~/esther-lab/engagements/public/<program>/findings/httpx-<domain>.txt

# Extract high-value targets immediately
grep -iE 'admin|api|dashboard|dev|staging|portal|internal|manage|login|auth|console' \
  ~/esther-lab/engagements/public/<program>/findings/httpx-<domain>.txt \
  > /tmp/<domain>-interesting.txt

cat /tmp/<domain>-interesting.txt
```

### Step 2 — nmap (live hosts only)

```bash
# Extract just the hostnames from httpx output
awk '{print $1}' ~/esther-lab/engagements/public/<program>/findings/httpx-<domain>.txt \
  | sed 's|https\?://||' | sort -u > /tmp/<domain>-live-hosts.txt

nmap -sV -sC -T3 -Pn --open \
  -iL /tmp/<domain>-live-hosts.txt \
  -oA ~/esther-lab/engagements/public/<program>/findings/nmap-<domain>
```

### Step 3 — Targeted Nuclei (NOT all templates)

**Template selection by target type:**

#### Gaming / Mobile App companies (Playtika, xAI etc.)
```bash
nuclei -l /tmp/<domain>-live-hosts.txt \
  -rate-limit 10 \
  -tags api,auth,cors,graphql,jwt,token,exposure,misconfig,takeover,cloud \
  -severity medium,high,critical \
  -o ~/esther-lab/engagements/public/<program>/findings/nuclei-<domain>.txt \
  -stats
```

#### Generic web targets
```bash
nuclei -l /tmp/<domain>-live-hosts.txt \
  -rate-limit 10 \
  -tags cve,sqli,xss,ssrf,xxe,rce,lfi,idor,misconfig,exposure \
  -severity medium,high,critical \
  -o ~/esther-lab/engagements/public/<program>/findings/nuclei-<domain>.txt \
  -stats
```

#### Specific high-value template categories to always include
| Category | Tag | Why |
|----------|-----|-----|
| Subdomain takeover | `takeover` | High value, easy win |
| Exposed credentials | `exposure` | API keys, tokens in responses |
| Misconfigured cloud | `cloud,aws,gcp,azure` | S3 buckets, metadata endpoints |
| CORS misconfiguration | `cors` | Common in API-heavy apps |
| JWT issues | `jwt,token` | Mobile apps use JWT heavily |
| GraphQL | `graphql` | Gaming APIs often use GraphQL |
| Auth bypass | `auth` | Login/SSO issues |
| Open redirects | `redirect` | Useful for phishing chain |
| SSRF | `ssrf` | High impact if confirmed |

#### Never use for initial scans
- `-tags wordpress` unless evidence of WordPress
- All 3768 templates (`-t` without filters) — too noisy, misses nothing useful
- Headless/code templates without `-headless -code` flags explicitly added

### Step 4 — ffuf (interesting endpoints only)

Only run against endpoints that showed interesting responses in httpx/nuclei.

```bash
# Directory fuzzing
ffuf -u https://<interesting-host>/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/api-endpoints.txt \
  -rate 10 \
  -mc 200,201,301,302,401,403 \
  -o ~/esther-lab/engagements/public/<program>/findings/ffuf-<host>.json \
  -of json

# Parameter fuzzing (if endpoint found)
ffuf -u https://<interesting-host>/api/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -rate 10 \
  -mc 200,201,400,401,403,500 \
  -o ~/esther-lab/engagements/public/<program>/findings/ffuf-params-<host>.json \
  -of json
```

### Phase 2 Commit
```bash
cd ~/esther-lab
git add engagements/public/<program>/findings/
git commit -m "Phase 2: active scan <domain> — httpx N live, nuclei results"
git push
gh api repos/FinkSecurity/esther-lab/commits?path=engagements/public/<program>/findings\&per_page=1 \
  --jq '.[0] | {sha: .sha[:9], message: .commit.message}'
```

---

## PHASE 2+ — DEEP INVESTIGATION

**Only triggered when Phase 2 surfaces interesting findings.**

### Triage checklist before going deeper
- [ ] Is the finding reproducible with a manual curl request?
- [ ] Is the affected host confirmed in scope (check scope.md)?
- [ ] Is this a real vulnerability or a false positive?
- [ ] What is the realistic impact?

### Manual verification
```bash
# Reproduce the nuclei finding manually
curl -sk -o /dev/null -w "%{http_code} %{url_effective}\n" \
  -H "User-Agent: Mozilla/5.0" \
  https://<target>/<path>

# Check response headers
curl -sI https://<target>/<path>

# Check CORS
curl -sk -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: GET" \
     -I https://<target>/api/endpoint \
  | grep -i "access-control"
```

### Subdomain takeover check
```bash
# Check if CNAME points to unclaimed service
dig CNAME <subdomain>.<domain>
# If points to *.github.io, *.s3.amazonaws.com, *.azurewebsites.net etc — check if claimed
```

### S3 / cloud storage check
```bash
# Check for public bucket
aws s3 ls s3://<bucket-name> --no-sign-request 2>/dev/null
curl -s https://<bucket-name>.s3.amazonaws.com/ | head -20
```

### JWT analysis
```bash
# Decode JWT (no library needed)
echo '<jwt_token>' | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
# Check for alg:none, weak secret, sensitive data in payload
```

---

## PHASE 3 — EXPLOITATION

**Requires explicit Operator APPROVE <finding-slug> per finding via Telegram.**

Only proceed after:
1. Finding is manually verified and reproducible
2. Operator has reviewed the finding summary
3. APPROVE <finding-slug> received

### After APPROVE received
```bash
# Generate H1 report draft
python3 ~/.openclaw/workspace/scripts/generate-h1-report.py \
  ~/esther-lab/engagements/public/<program>/findings/nuclei-<domain>.txt \
  --program <program>

# Review and complete the draft
cat ~/esther-lab/engagements/public/<program>/submissions/DRAFT-*.md
```

---

## FINDING SEVERITY QUICK REFERENCE

| Finding Type | Typical Severity | Notes |
|-------------|-----------------|-------|
| RCE | Critical | Always report immediately |
| SQLi (confirmed) | High–Critical | Depends on data accessible |
| Subdomain takeover | Medium–High | Easy win, report fast |
| Exposed API key | High | Depends on key scope |
| CORS misconfiguration | Medium | Needs auth bypass to be High |
| Open redirect | Low–Medium | Chains into phishing = Medium |
| Sensitive data exposure | Medium–High | Depends on data type |
| S3 bucket listing | Medium–High | Public write = Critical |
| JWT alg:none | High | Auth bypass = High |
| SSRF (confirmed) | High | Internal access = Critical |
| GraphQL introspection | Low–Medium | Info disclosure only |
| Missing security headers | Informational | Not reportable alone |

---

## ESTHER STARTUP SEQUENCE FOR EVERY ENGAGEMENT

```bash
# 1. Read this playbook
cat ~/esther-lab/docs/RECON-PLAYBOOK.md

# 2. Load scope
python3 ~/.openclaw/workspace/scripts/load-scope.py <program> <task_id>

# 3. Read active engagement context
cat ~/.openclaw/workspace/ACTIVE-ENGAGEMENT.md

# 4. Check what's already been done
ls ~/esther-lab/engagements/public/<program>/findings/
gh api repos/FinkSecurity/esther-lab/commits?path=engagements/public/<program>/findings\&per_page=5 \
  --jq '.[] | {sha: .sha[:9], message: .commit.message}'

# 5. Proceed from where you left off — never duplicate prior work
```

---

## GIT WORKING DIRECTORY

**ALWAYS run git commands from `~/esther-lab/`**

```bash
cd ~/esther-lab
git add engagements/...
git commit -m "..."
git push
```

**NEVER run git commands from `~/.openclaw/workspace/`** — that directory is
your local brain, not the FinkSecurity/esther-lab repo.

---

*ESTHER — Fink Security | Commit this file and read it at the start of every engagement.*
