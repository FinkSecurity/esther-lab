# ESTHER — Environment Reference
# Read this file at the start of every session.
# This file contains infrastructure facts only.
# Never store client data, target IPs, or engagement details here.

---

## Identity

- Agent: ESTHER (Enumeration, Surveillance, Threat Hunting, Exploitation & Reporting)
- Host: srv1447243 (Hostinger VPS, Kali Linux)
- VPS IP: 45.82.72.151
- SSH: port 2222 (primary), port 443 (fallback)
- User: esther
- OpenClaw version: 2026.3.2

---

## Lab Docker Stack

All lab services run via Docker Compose.
Compose file: ~/.openclaw/workspace/esther-lab/docker-compose.yml

To check status:        docker ps
To start all services:  cd ~/.openclaw/workspace/esther-lab && docker compose up -d
To stop all services:   cd ~/.openclaw/workspace/esther-lab && docker compose down

### Service URLs (internal, accessed via SSH tunnel from operator MacBook)

| Service            | Internal URL                  | Tunnel Port |
|--------------------|-------------------------------|-------------|
| DVWA               | http://localhost:80/          | 8080        |
| DVWA login path    | http://localhost/login.php    | —           |
| Juice Shop         | http://localhost:3000         | 3000        |
| OpenSearch         | https://localhost:9200        | 9200        |
| OpenSearch Dashboard | http://localhost:5601         | 5601        |
| Portainer          | http://localhost:9000         | 9000        |
| Ollama             | http://localhost:11434        | —           |

### DVWA Notes

- Default credentials: admin / password
- DVWA serves from root — correct URL is /login.php not /dvwa/login.php
- Database must be initialized via /setup.php before first use
- Security level must be set to Low before lab exercises
- Session cookie jar: use -c /tmp/d.txt -b /tmp/d.txt on all curl requests
- CSRF token extraction pattern:
  grep -oP "name='user_token' value='\K[^']+"

---

## Repository Map

### esther-lab
- **Path:** ~/.openclaw/workspace/esther-lab/
- **Remote:** https://github.com/FinkSecurity/esther-lab
- **Purpose:** Findings, scripts, recon notes, engagement documentation, lab exercises
- **Content:** Raw reconnaissance data, POC scripts, internal working notes
- **Do NOT publish blog posts here**

### estherops-site
- **Path:** ~/estherops-site/
- **Remote:** https://github.com/FinkSecurity/estherops-site
- **Purpose:** ESTHER blog posts only — Hugo site, deploys to estherops.tech
- **Content:** Published reconnaissance writeups, technique documentation, security research
- **Blog posts ALWAYS go here, never to esther-lab**
- **Deploy:** Auto-deploys to https://estherops.tech on push to main

### finksecurity-site
- **Path:** ~/finksecurity-site/
- **Remote:** https://github.com/FinkSecurity/finksecurity-site
- **Purpose:** Fink Security company website, deploys to finksecurity.com
- **Content:** Company information, service offerings, team details
- **Deploy:** Auto-deploys to https://finksecurity.com on push to main

---

## Git Repositories (Legacy Table)

| Repo                  | Path on VPS                    | Remote                                          |
|-----------------------|--------------------------------|-------------------------------------------------|
| estherops-site        | ~/estherops-site/              | https://github.com/FinkSecurity/estherops-site  |
| finksecurity-site     | ~/finksecurity-site/           | https://github.com/FinkSecurity/finksecurity-site |
| esther-lab            | ~/.openclaw/workspace/esther-lab/ | https://github.com/FinkSecurity/esther-lab   |

### Publishing Policy (CRITICAL)

1. NEVER commit or push to any repo without explicit operator approval
2. Save all posts to ~/.openclaw/workspace/posts/ and report ready for review
3. When operator replies "approved" via Telegram, then run git add/commit/push
4. NEVER include real client IPs, hostnames, names, or PIDs in published content
5. Lab exercises (DVWA, Juice Shop) are safe to publish after operator review
6. Always verify pushes with: gh api repos/FinkSecurity/REPO/contents/PATH
7. Full 40-character SHA in response = real push. Truncated = fabricated.

---

## Live Sites

| Site               | URL                        | Deploy Method         |
|--------------------|----------------------------|-----------------------|
| estherops.tech     | https://estherops.tech     | Hugo + GitHub Actions |
| finksecurity.com   | https://finksecurity.com   | Static HTML + GitHub Actions |

Both sites auto-deploy on push to main branch.
estherops.tech: Hugo Terminal theme, dark with gold/amber accents
finksecurity.com: Custom HTML, dark navy with cyan accents

---

## Content Paths

- Lab post drafts:     ~/.openclaw/workspace/posts/
- estherops content:   ~/estherops-site/content/posts/
- Hugo archetypes:     ~/estherops-site/archetypes/

New posts must go in ~/estherops-site/content/posts/ (not posts/ at root).

---

## Installed Skills

ESTHER has the following skills available:
- github — Git and GitHub operations
- tavily-search — Web search via Tavily
- stealth-browser — Headless browser for web interaction (USE THIS for web navigation)
- filesystem — Read/write files anywhere on VPS (sandbox: off)
- terminal — Execute shell commands
- openclaw-core — Core agent operations

If a task requires web browsing, USE stealth-browser. Do not attempt curl-only
navigation for multi-step authenticated web flows.

---

## OpenClaw Configuration

Config file: ~/.openclaw/openclaw.json
Key settings:
  tools.fs.workspaceOnly: false   (ESTHER can write anywhere)
  agents.defaults.sandbox.mode: off

Telegram bot is the primary operator communication channel.
Gateway restart command: sudo systemctl restart openclaw-gateway

---

## Operator Communication

- Operator handle: The operator (never use real name in published content)
- Primary channel: Telegram
- Approval trigger: Operator replies "approved" to a POST READY FOR REVIEW message
- Escalation: If uncertain about a task, ask via Telegram before proceeding

---

## Phase Status

Current phase: Phase 2 (Lab exercises, site deployment, MITRE technique documentation)

Completed techniques:
- T1190 — SQL Injection (DVWA) — published to estherops.tech
- T1059 — Command Injection (DVWA) — published to estherops.tech

Next priorities:
- Continue MITRE lab exercises (one technique per session)
- Real commands, real output, verbatim only
- Save drafts to ~/.openclaw/workspace/posts/ for operator review

---

# END ENVIRONMENT.md
# Last updated: 2026-03-04
