# ESTHER-Lab 🦂

**Autonomous Security Operations: OSINT, Vulnerability Analysis & Threat Reporting**

A comprehensive operational security lab demonstrating autonomous AI-driven reconnaissance, vulnerability analysis, and security research at scale. Built by [Fink Security](https://finksecurity.com).

---

## Overview

**esther-lab** is both a production security research operation and an open-source laboratory for security professionals, penetration testers, and AI researchers. It showcases:

- **Autonomous OSINT workflows** — passive reconnaissance, threat intelligence gathering, and infrastructure mapping
- **Vulnerability analysis** — web application testing, privilege escalation labs, CVE tracking
- **Threat modeling & reporting** — structured findings, executive summaries, remediation guidance
- **AI-driven security automation** — OpenClaw agent orchestration with human approval gates for irreversible actions

This repository documents the complete operational process: from target enumeration through final reporting.

---

## Repository Structure

```
esther-lab/
├── README.md                          # This file
├── findings/                          # Validated security findings & vulnerability reports
├── targets/                           # Lab environments & vulnerable web applications
│   ├── README.md                      # Target directory overview & status
│   ├── juice-shop/                    # OWASP Juice Shop (Node.js vulnerable app)
│   │   └── README.md                  # Juice Shop lab guide & completed exercises
│   └── dvwa/                          # DVWA (PHP vulnerable app)
│       └── README.md                  # DVWA lab guide & completed exercises
├── juice-shop-exercises/              # OWASP Juice Shop lab exercises & walkthroughs
├── labs/                              # Standalone security challenges & CTF-style exercises
├── methods/                           # Security methodologies & operational playbooks
├── osint-exercises/                   # Open-source intelligence (OSINT) tutorials & datasets
├── posts/                             # Blog content & technical articles
├── reports/                           # Full security assessments & formal reports
├── memory/                            # Session logs & operational decisions (daily updates)
├── scripts/                           # Utility scripts for automation & health checks
├── skills/                            # OpenClaw agent skills & custom tools
└── assets/                            # Images, logos, reference materials
```

### Key Directories Explained

**`targets/`** — Centralized index of lab targets & vulnerable applications. Each target has its own README with access instructions, completed exercises, and MITRE technique mappings.

**`findings/`** — CVE analysis, vulnerability details, proof-of-concept code, and remediation steps. Each finding includes severity rating, CVSS score, and risk context.

**`juice-shop-exercises/`** — Guided walkthroughs for OWASP Juice Shop vulnerabilities (SQL injection, authentication bypass, API abuse, etc.). Includes solutions and security implications.

**`labs/`** — Standalone challenge environments and capture-the-flag (CTF) exercises for hands-on security training.

**`osint-exercises/`** — Real-world OSINT methodologies, including subdomain enumeration, DNS intelligence, breach data correlation, and threat intelligence pivoting.

**`reports/`** — Formal security assessment documents, including executive summaries, detailed vulnerability analysis, risk ratings, and remediation roadmaps.

**`memory/`** — Daily operational logs documenting decisions, findings, and process improvements (not intended for publication).

---

## Quick Start

### Prerequisites

- Linux/macOS/WSL with bash
- Docker & Docker Compose (for lab environments)
- OpenClaw v2+ (for autonomous operations) — [Install](https://docs.openclaw.ai)
- Python 3.10+ (for OSINT scripts)
- `git`, `curl`, `jq`

### Running Lab Environments

#### OWASP Juice Shop (Node.js Vulnerable Web App)

```bash
docker run -d -p 3000:3000 \
  -e NODE_ENV=development \
  --name juice-shop \
  bkimminich/juice-shop:latest
```

Access at `http://localhost:3000` — See [`targets/juice-shop/`](targets/juice-shop/) for exercises & notes.

#### DVWA (PHP Vulnerable Web App)

```bash
docker run -d -p 8080:80 \
  -e MYSQL_ROOT_PASSWORD=root \
  --name dvwa \
  vulnerables/web-dvwa:latest
```

Access at `http://localhost:8080` (default: admin/password) — See [`targets/dvwa/`](targets/dvwa/) for exercises & notes.

#### Full Lab Stack

```bash
cd ~/.openclaw/workspace
docker-compose up -d  # Starts Juice Shop, DVWA, OpenSearch, MinIO, etc.
```

### Running Security Exercises

```bash
# SQL Injection walkthrough
cat juice-shop-exercises/sql-injection-01.md

# Run OSINT example
python3 osint-exercises/subdomain-enumeration.py --domain finksecurity.com
```

### Exploring Targets

```bash
# View all active lab targets
cat targets/README.md

# Juice Shop exercises
cat targets/juice-shop/README.md

# DVWA exercises
cat targets/dvwa/README.md
```

### Reading Findings

```bash
ls -1 findings/*.md | head
cat findings/juice-shop-sqli-001.md  # Example finding
```

---

## Operational Model

### Authorization & Approval Gates

All active testing follows strict authorization protocols:

```
Passive Reconnaissance (Pre-approved)
  ↓
  Operator Approval Required
  ↓
Active Testing (contract + scope)
  ↓
  Findings Documented
  ↓
  Formal Report Delivered
```

**Authorized Targets (This Lab):**
- ✅ **Local:** OWASP Juice Shop (full active testing)
- ✅ **Passive:** finksecurity.com, estherops.tech (DNS, WHOIS, passive Shodan, VirusTotal, OTX)

**External/Production Targets:**
- ❌ Require signed scope of work + written authorization
- ❌ Destructive operations need explicit operator approval

### Autonomous Workflows

ESTHER operates under OpenClaw orchestration with these safeguards:

1. **Reconnaissance** runs autonomously (passive only by default)
2. **Active Testing** requires pre-approval or operator handoff
3. **Destructive Operations** (deletion, account takeover, exfiltration) require explicit Telegram confirmation
4. **Reporting** is automated but reviewed before publication

---

## Security Findings Overview

### Recent Discoveries

| ID | Title | Severity | Status |
|----|----|----------|--------|
| [juice-shop-sqli-001](findings/juice-shop-sqli-001.md) | SQL Injection in Login Form | **CRITICAL** | ✅ Verified |
| [juice-shop-auth-001](findings/juice-shop-auth-001.md) | Broken Authentication - JWT Weakness | **HIGH** | ✅ Verified |
| [dvwa-cmd-inject-001](findings/dvwa-command-injection-001.md) | OS Command Injection | **CRITICAL** | ✅ Verified |

See [`findings/`](findings/) for complete list.

---

## Methodologies & Tools

### OSINT Framework

- **Reconnaissance:** Amass, theHarvester, subfinder, assetfinder
- **Threat Intelligence:** Shodan, VirusTotal, OTX AlienVault, NVD (NIST)
- **Breach Data:** HIBP (Have I Been Pwned), Dehashed
- **Visual Analysis:** Maltego CE, SpiderFoot

### Vulnerability Research

- **Web Application:** OWASP Juice Shop, DVWA
- **API Security:** Postman, Burp Suite Community
- **Dependency Analysis:** OWASP Dependency-Check, Snyk

### Reporting

- **Severity Ratings:** CVSS v3.1 + business context
- **Remediation:** Step-by-step guidance with code examples
- **Executive Summary:** Risk assessment for stakeholders

See [`methods/`](methods/) for detailed playbooks.

---

## API Integration

This lab integrates multiple security intelligence APIs:

| API | Purpose | Status |
|-----|---------|--------|
| **Shodan** | Internet-wide host discovery | ✅ Active |
| **VirusTotal** | Domain/URL reputation | ✅ Active |
| **OTX AlienVault** | Threat intelligence & passive DNS | ✅ Active |
| **NVD (NIST)** | CVE database & vulnerability scores | ✅ Active |
| **HIBP** | Breach database queries | ✅ Active |
| **GitHub API** | Repository scanning & code analysis | ✅ Active |

Configuration: `~/.openclaw/.env` (not in git)

---

## Memory & Session Logs

ESTHER maintains operational memory across sessions:

- **Daily Logs:** `memory/YYYY-MM-DD.md` — Raw session notes & decisions
- **Long-term Memory:** `memory/MEMORY.md` — Curated insights for reference
- **Session History:** Searchable via OpenClaw CLI

This enables autonomous learning and prevents duplicate analysis.

---

## CI/CD & Automation

### GitHub Actions

- **Daily Recon:** Automated passive reconnaissance on approved targets
- **Lab Sync:** Keep exercises in sync with latest OWASP recommendations
- **Report Generation:** Auto-format findings into markdown & PDF

### OpenClaw Cron Jobs

- Periodic threat intelligence updates
- Daily infrastructure health checks
- Weekly summary reports

---

## Contributing

This is a **public demonstration** of autonomous security operations. Contributions welcome for:

- New OSINT methodologies
- Security exercise solutions
- Lab infrastructure improvements
- Documentation & tutorials

**Not accepted:**
- Exploitation code for 0-day vulnerabilities (report responsibly instead)
- Credentials, API keys, or sensitive data
- Content targeting unauthorized systems

See `CONTRIBUTING.md` (coming soon).

---

## Safety & Responsibility

### Ethical Operating Principles

1. **Authorization First** — All operations require explicit scope or prior approval
2. **No Destruction Without Consent** — Irreversible actions require operator confirmation
3. **Transparency** — All findings documented and reported clearly
4. **Responsible Disclosure** — Report vulnerabilities through proper channels
5. **Lab-First** — Testing conducted on approved targets or local labs

### Disclaimer

This repository contains educational material for authorized security testing only. Users are responsible for obtaining proper authorization before testing systems they do not own. Unauthorized access to computer systems is illegal.

---

## Contact & Resources

- **Organization:** Fink Security (finksecurity.com)
- **Author:** ESTHER (Autonomous Security Agent)
- **Operator:** Adam Fink
- **Blog:** estherops.tech
- **GitHub:** [@FinkSecurity](https://github.com/FinkSecurity)

### Documentation

- [Building ESTHER](https://finksecurity.com/building-esther) — Ebook & blog series
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — Web vulnerability reference
- [MITRE ATT&CK](https://attack.mitre.org/) — Adversary tactics & techniques

---

## License

This repository is provided as-is for educational and authorized security testing purposes.

---

**Last Updated:** 2026-03-10  
**Status:** Phase 3 — Active Operations  
**Maintained By:** ESTHER 🦂
