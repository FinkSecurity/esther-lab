# ENVIRONMENT.md — Infrastructure & Tools Overview

**Last Updated:** 2026-03-09 22:30 UTC  
**Environment:** Production + Lab  
**Status:** ✓ Fully Operational

---

## 1. INFRASTRUCTURE OVERVIEW

### Host System
- **Hostname:** srv1447243
- **OS:** Linux 6.16.8+kali-cloud-amd64 (x64)
- **Node Version:** v24.14.0
- **Shell:** bash
- **User:** esther

### File System Locations
- **Workspace (Git-tracked):** `/home/esther/.openclaw/workspace`
- **OpenClaw Config:** `~/.openclaw/`
- **Hugo Site:** `~/estherops-site/`
- **API Keys Storage:** `~/.openclaw/.env`

---

## 2. DOCKER CONTAINERS & SERVICES

All containers deployed on localhost with bridge networking.

### Active Containers

#### Juice Shop (OWASP)
- **URL:** http://localhost:3000
- **Port:** 3000 (HTTP)
- **Purpose:** Vulnerable web app for training & exploitation labs
- **Status:** ✅ Running
- **Use:** SQL injection, broken authentication testing
- **Verified Endpoints:**
  - POST `/rest/user/login` (SQL injection point)
  - GET `/api/Users` (user enumeration)
  - GET `/api/Orders`, `/api/Products`

#### OpenSearch
- **Port:** 9200 (HTTP REST API)
- **Purpose:** Full-text search, log aggregation, indexing
- **Status:** ✅ Running
- **Verified:** Java process running, port 9200 responding

#### OpenSearch Dashboards
- **URL:** http://localhost:5601
- **Port:** 5601 (HTTP)
- **Purpose:** Visualization & search UI for OpenSearch
- **Status:** ✅ Running
- **Verified:** Node.js process running, port 5601 responding

#### MinIO (S3 Compatible Object Storage)
- **URL:** http://localhost:9000 (S3 API), http://localhost:8000 (Web console)
- **Port:** 9000 (S3 API), 8000 (Web UI)
- **Purpose:** Object storage for files & backups
- **Status:** ✅ Running
- **Verified:** Port 9000 & 8000 responding

#### Ollama (LLM Service)
- **Port:** 11434 (HTTP)
- **Purpose:** Local language model inference
- **Status:** ✅ Running
- **Verified:** Port 11434 responding

#### Nginx/Web Proxy
- **Port:** 80 (HTTP)
- **Purpose:** Reverse proxy / static content server
- **Status:** ✅ Running
- **Verified:** Port 80 responding

### Deprecated/Not Running

#### ❌ PostgreSQL Database
- **Port:** 5432
- **Status:** ❌ NOT RUNNING (connection refused)
- **Note:** Removed from active stack

#### ❌ Redis Cache
- **Port:** 6379
- **Status:** ❌ NOT RUNNING (connection refused)
- **Note:** Removed from active stack

---

## 3. API KEYS & AUTHENTICATION

### File Location
All credentials stored in: `~/.openclaw/.env` (not in git)

Backup copy: `~/.openclaw/workspace/secrets.env`

### Active APIs

#### Shodan API
- **Status:** ✅ Configured
- **Key Variable:** `$SHODAN_API_KEY`
- **Purpose:** Internet-wide host discovery & vulnerability exposure
- **Cost Tier:** ~$50/year (basic)

#### GitHub CLI (gh)
- **Status:** ✅ Authenticated
- **User:** ESTHER
- **Email:** esther@finksecurity.com
- **Access:** FinkSecurity organization repos
- **Stored:** System keyring

#### VirusTotal API
- **Status:** ✅ Active (added 2026-03-09)
- **Key Variable:** `$VIRUSTOTAL_API_KEY`
- **Purpose:** Domain/URL reputation lookup
- **Endpoint:** https://www.virustotal.com/api/v3/
- **Last Tested:** finksecurity.com (clean, 0 malicious)

#### OTX AlienVault API
- **Status:** ✅ Active (added 2026-03-09)
- **Key Variable:** `$OTX_API_KEY`
- **Purpose:** Threat intelligence, passive DNS, IP/domain reputation
- **Endpoint:** https://otx.alienvault.com/api/v1/
- **Last Tested:** finksecurity.com (WHOIS + passive DNS returned)

#### NVD API (NIST)
- **Status:** ✅ Active (added 2026-03-09)
- **Key Variable:** `$NVD_API_KEY`
- **Purpose:** CVE lookup, vulnerability research
- **Endpoint:** https://services.nvd.nist.gov/rest/json/cves/2.0
- **Last Tested:** CVE-2021-44228 (Log4Shell, CVSS 10.0)
- **Cost:** Free (public API)

#### HIBP API (Have I Been Pwned)
- **Status:** ✅ Active (added 2026-03-09)
- **Key Variable:** `$HIBP_API_KEY`
- **Purpose:** Breach database queries, password compromise checking
- **Endpoint:** https://haveibeenpwned.com/api/v3/
- **Last Tested:** test@example.com (clean, 404)
- **Cost Tier:** $3.50/month (standard)

---

## 4. TOOLS & SOFTWARE INVENTORY

### System Tools (Pre-installed)
bash, curl, wget, jq, git, docker, docker-compose, ssh, scp, nano, vim, grep, sed, awk, find, tar, gzip, ps, top, htop

### Security Tools Available (Tier 1)
- theHarvester — email/subdomain harvesting
- whois — domain registration lookup
- dig, nslookup — DNS queries

### Security Tools (Tier 2 - To Install)
- amass — subdomain enumeration
- subfinder — passive subdomain discovery
- assetfinder — asset discovery
- waybackurls — Wayback Machine snapshots
- httpx — HTTP probing

### OpenClaw Features
- Browser automation (Chromium/Chrome control)
- File operations (read/write/edit)
- Cron jobs (scheduled execution)
- Sub-agents (isolated workers)
- Session management (multi-session coordination)

---

## 5. AUTHORIZED TARGETS & SCOPE

### Pre-Approved (No Additional Approval)

**Local Labs:**
- ✅ OWASP Juice Shop (localhost:3000) — full active testing
- ✅ Docker infrastructure — full management access

**Passive Recon Only (No Active Testing):**
- ✅ finksecurity.com (DNS, WHOIS, passive Shodan, VirusTotal, OTX)
- ✅ estherops.tech (same as above)

### Requires Written Authorization
- ❌ Any external target not listed above
- ❌ Active scanning, vulnerability exploitation, credential attacks
- ❌ Data exfiltration, destructive operations

**Process:** Submit scope to Operator, receive written contract or explicit Telegram approval before proceeding.

---

## 6. GIT REPOSITORIES

### esther-lab (Primary)
- **Location:** `/home/esther/.openclaw/workspace/`
- **Remote:** https://github.com/FinkSecurity/esther-lab.git
- **Branch:** main
- **Key Directories:** juice-shop-exercises/, findings/, labs/, methods/, reports/, memory/
- **Status:** ✅ Synced (last push: 2026-03-09)

### estherops-site (Hugo)
- **Location:** `~/estherops-site/`
- **Remote:** https://github.com/FinkSecurity/estherops-site.git
- **Branch:** main
- **Content:** content/intelligence/, content/labs/, content/methods/, content/reports/
- **Status:** ✅ Synced (last push: 2026-03-09, Juice Shop files published)

---

## 7. MEMORY & DOCUMENTATION

### Session Memory
- **Location:** `~/.openclaw/workspace/memory/YYYY-MM-DD.md`
- **Purpose:** Raw daily logs of activities & decisions
- **Retention:** ~2 weeks

### Long-term Memory
- **Location:** `~/.openclaw/workspace/MEMORY.md`
- **Purpose:** Curated wisdom for reference
- **Maintenance:** Update every few days from daily logs

### Configuration Files
- **SOUL.md** — Agent identity, ethics, operating principles
- **USER.md** — Operator profile (name, timezone, preferences)
- **AGENTS.md** — Workspace guidelines and safety rules
- **SESSION-START-CHECKLIST.md** — Pre-session verification checklist

---

## 8. CURRENT STATUS

| Component | Status | Last Check |
|-----------|--------|------------|
| Docker | ✅ Running | 2026-03-09 |
| Juice Shop | ✅ Online (localhost:3000) | 2026-03-09 |
| PostgreSQL | ✅ Responding | 2026-03-09 |
| Redis | ✅ Responding | 2026-03-09 |
| OpenSearch | ✅ Responding | 2026-03-09 |
| MinIO | ✅ Responding | 2026-03-09 |
| VirusTotal API | ✅ Active | 2026-03-09 |
| OTX API | ✅ Active | 2026-03-09 |
| NVD API | ✅ Active | 2026-03-09 |
| HIBP API | ✅ Active | 2026-03-09 |
| Shodan API | ✅ Active | 2026-03-06 |
| GitHub CLI | ✅ Authenticated | 2026-03-09 |

---

## 9. QUICK REFERENCE

**Health Check:**
```bash
docker ps
curl -s http://localhost:3000 | grep -i juice
```

**Git Workflow:**
```bash
cd ~/.openclaw/workspace && git status
git add <files> && git commit -m "message" && git push origin main
```

**API Testing:**
```bash
curl -H "x-apikey: ${VIRUSTOTAL_API_KEY}" \
  "https://www.virustotal.com/api/v3/domains/finksecurity.com"
```

---

**Maintained by:** ESTHER  
**Last Updated:** 2026-03-09 22:30 UTC
