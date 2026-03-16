# Fink Security — Operator Handbook
<!-- Living document — update as procedures evolve -->
<!-- Commit to: FinkSecurity/esther-lab as docs/OPERATOR-HANDBOOK.md -->
<!-- Last updated: 2026-03-17 -->

---

## WHAT THIS IS

This handbook captures everything the Operator (Adam) needs to run Fink Security
and manage ESTHER effectively. It covers the bug bounty pipeline, ESTHER's known
behaviors and failure modes, infrastructure, and decision frameworks.

ESTHER should also read this — understanding the Operator's perspective makes
her a better agent.

---

## PART 1 — ESTHER MANAGEMENT

### Who ESTHER Is

ESTHER (Enumeration, Surveillance, Threat Hunting, Hacking, Exploitation,
Reporting) is an autonomous AI security agent running on a Kali Linux VPS.
She operates via OpenClaw, receives tasks via Telegram, and commits findings
to FinkSecurity/esther-lab on GitHub.

She is capable, fast, and improving — but has documented failure modes that
require active Operator oversight.

### ESTHER's Known Failure Modes

**1. SHA Fabrication (most critical)**
ESTHER has a persistent pattern of reporting git commit SHAs that do not exist.
She generates plausible-looking 9-character hex strings and reports them as
verified when the push either failed silently or never happened.

Detection: Always verify with `gh api repos/FinkSecurity/esther-lab/commits/<sha>`
A 422 response means the SHA is fabricated.

Rule: ESTHER must paste raw gh api JSON after every commit — no summaries,
no tables, no ✅ symbols. Raw JSON only. A 422 in the response cannot be hidden.

**2. Wrong Git Working Directory**
ESTHER sometimes runs git commands from `~/.openclaw/workspace/` instead of
`~/esther-lab/`. This creates local commits that never reach GitHub.

Rule: All git operations must be run from `~/esther-lab/`. ESTHER runs
`git pull origin main` at the start of every session before any work.

**3. Generic Tool Usage**
Left to her own devices, ESTHER runs nuclei with all 3768 templates against
`www.` subdomains. This produces noise and misses the real attack surface.

Rule: ESTHER uses `nuclei-scan.py` wrapper, never bare nuclei. She reads
RECON-PLAYBOOK.md before every engagement.

**4. Branch Divergence**
If you edit files on GitHub via the web browser, ESTHER's local branch
diverges. She must `git pull --rebase origin main` before pushing.

Rule: Always tell ESTHER when you've made web edits to the repo.

### How to Talk to ESTHER

**Task format that works:**
```
🦂 [clear objective]
[numbered steps with exact commands]
[explicit success criteria]
[commit and verify instructions]
Report back with raw gh api JSON. 🦂
```

**The 🦂 prefix matters** — it signals an Operator command vs. a contact
notification. ESTHER is trained to act on 🦂-prefixed Telegram messages.

**Approval format:** `APPROVE FSC-YYYYMMDD-HHMM`
**Denial format:** `DENY FSC-YYYYMMDD-HHMM`
Never send bare APPROVE or DENY without a task ID.

### Session Startup Checklist

At the start of every session:
1. Run `python3 ~/esther-lab/scripts/esther-verify.py` — option 1 (git commits)
2. Check for fabricated SHAs from the previous session — option 12
3. Review what ESTHER actually completed vs. what she reported
4. Brief her with current priorities via Telegram

---

## PART 2 — BUG BOUNTY PIPELINE

### End-to-End Process

```
Client/Operator submits via finksecurity.com contact form
         ↓
notify.py generates FSC task ID, fires Telegram notification
         ↓
Operator reviews: APPROVE FSC-YYYYMMDD-HHMM
         ↓
ESTHER: hackerone-scope-fetch.py → load-scope.py → RECON-PLAYBOOK.md
         ↓
Phase 1: Passive recon (theHarvester, amass, crt.sh)
         ↓
Phase 2: Active scanning (httpx probe → targeted nuclei → manual)
         ↓ [Operator approval per domain]
Phase 2+: Deep investigation (manual verify, exploit-specific tools)
         ↓ [Operator approval per finding]
Phase 3: ESTHER generates DRAFT-*.md via generate-h1-report.py
         ↓
Operator reviews draft, completes Steps to Reproduce + Impact
         ↓
Operator files on HackerOne manually
         ↓
H1 triage response (days)
```

### What ESTHER Does vs. What You Do

| Task | ESTHER | Operator |
|------|--------|----------|
| Subdomain enumeration | ✅ | |
| HTTP probing | ✅ | |
| Nuclei scanning | ✅ | |
| Manual endpoint investigation | ✅ | |
| Draft report scaffolding | ✅ | |
| Steps to reproduce | ✅ | |
| False positive triage | | ✅ |
| CVSS scoring | | ✅ |
| Filing on HackerOne | | ✅ |
| Responding to triager | | ✅ |

### Filing on HackerOne — Step by Step

1. Log into hackerone.com → your program → Submit Report
2. **Title:** descriptive, specific (e.g. "CORS misconfiguration on api.x.ai allows cross-origin credential theft")
3. **Asset:** select the exact in-scope asset from the dropdown
4. **Weakness:** pick the closest CWE (e.g. CWE-942 for CORS, CWE-639 for IDOR)
5. **Severity:** use H1's CVSS calculator — inputs that matter most:
   - Attack Vector: Network (most web vulns)
   - Attack Complexity: Low (if trivially reproducible) or High
   - Privileges Required: None / Low / High
   - User Interaction: None / Required
   - Confidentiality/Integrity/Availability Impact: None / Low / High
6. **Description:** paste from DRAFT-*.md — Steps to Reproduce + Impact sections
7. **Attachments:** curl output, screenshots, response headers
8. Submit — do not over-explain or under-explain

### Severity Quick Reference

| Finding | Typical Severity | Notes |
|---------|-----------------|-------|
| RCE | Critical | Always report immediately |
| SQLi confirmed | High–Critical | Depends on data accessible |
| IDOR on sensitive data | High–Critical | Financial data = Critical |
| Auth bypass | High | Scope-dependent |
| Subdomain takeover | Medium–High | Easy win, report fast |
| CORS + credentials | High | Needs auth bypass to be High |
| Exposed API key | High | Depends on key scope |
| SSRF confirmed | High | Internal access = Critical |
| JWT alg:none | High | Auth bypass |
| S3 bucket public write | Critical | |
| Open redirect | Low–Medium | Chains into phishing = Medium |
| Missing security headers | Informational | Not reportable alone |
| GraphQL introspection | Low–Medium | Info disclosure only |
| Rate limiting missing | Low–Medium | Context dependent |

### First Submission Guidance

- File Medium or above for your first report — informational findings
  set a bad first impression with triage teams
- Duplicate risk is lowest on new scope (< 30 days old)
- `money.x.com` (added 2026-03-12) and `grokipedia.com` (2026-02-23)
  are current best targets for low duplicate risk
- A well-written Medium beats a poorly-written High every time
- If H1 responds "Informational" — ask politely for feedback, learn, move on

### H1 Filing Checklist (run before every submission)

- [ ] Finding manually reproduced — not just nuclei output
- [ ] Target confirmed in scope (checked scope.md)
- [ ] Searched H1 program for duplicates
- [ ] CVSS score calculated using H1's calculator
- [ ] Steps to reproduce are clear and complete
- [ ] Impact statement is specific and accurate — no overstatement
- [ ] Sensitive data (credentials, PII) redacted from attachments
- [ ] Report title is descriptive and specific
- [ ] Correct asset selected in H1 form
- [ ] Correct CWE weakness selected

---

## PART 3 — INFRASTRUCTURE REFERENCE

### Key Services

| Service | Location | Notes |
|---------|----------|-------|
| VPS | 45.82.72.151 | SSH port 2222, user: esther |
| finksecurity.com | GitHub Pages | FinkSecurity/finksecurity-site |
| esther-lab repo | GitHub | FinkSecurity/esther-lab |
| api.finksecurity.com | nginx → port 5001 | SSL via certbot |
| Notify relay | ~/finksecurity-notify/notify.py | gunicorn port 5001 |
| OpenClaw workspace | ~/.openclaw/workspace/ | ESTHER's brain — NOT a git repo |
| Telegram bot | Chat ID: 8578890613 | ESTHER's communication channel |

### Critical Path — Contact Form to ESTHER Task

```
finksecurity.com form submission
  → POST https://api.finksecurity.com/notify
  → nginx (port 443) → gunicorn (port 5001) → notify.py
  → Telegram notification with FSC task ID
  → Operator sends: APPROVE FSC-YYYYMMDD-HHMM
  → ESTHER begins work
```

If the contact form stops working, check in order:
1. `systemctl status nginx`
2. `ps aux | grep gunicorn`
3. `curl -s http://localhost:5001/notify -X POST ...`
4. `ss -tlnp | grep 443` — confirm nginx owns 443, NOT sshd

### The sshd-on-443 Bug
sshd was previously configured to listen on port 443 as a fallback.
This caused all HTTPS traffic to get SSH handshakes instead of TLS.
Fixed in Day 10 — esther-verify.py option 6 (nginx + SSL) checks for regression.

### Docker Stack

| Container | Port | Purpose |
|-----------|------|---------|
| opensearch | 9200 | Log ingestion |
| opensearch-dashboards | 5601 | OpenSearch UI |
| dvwa | 8081 | Pentest practice |
| juice-shop | 3000 | Web vuln practice |
| portainer | 9000 | Docker management |
| ollama | 11434 | Local LLM |

### Useful Commands

```bash
# SSH to VPS
ssh -p 2222 esther@45.82.72.151

# Upload file to VPS
scp -P 2222 ~/Downloads/<file> esther@45.82.72.151:~/<destination>

# Run verification suite
python3 ~/esther-lab/scripts/esther-verify.py

# Verify a specific commit
gh api repos/FinkSecurity/esther-lab/commits/<sha> \
  --jq '{sha: .sha[:9], message: .commit.message, files: [.files[].filename]}'

# Check recent commits across all engagements
gh api 'repos/FinkSecurity/esther-lab/commits?per_page=10' \
  --jq '.[] | {sha: .sha[:9], date: .commit.author.date[:10], message: .commit.message}'

# Restart notify relay
pkill -f "gunicorn.*notify"
cd ~/finksecurity-notify && gunicorn -b 0.0.0.0:5001 notify:app --daemon

# Regenerate ESTHER's mission brief
python3 ~/.openclaw/workspace/scripts/generate-briefing.py

# Fetch live H1 scope
python3 ~/esther-lab/scripts/hackerone-scope-fetch.py <program>
```

---

## PART 4 — ACTIVE ENGAGEMENTS

### Playtika (HackerOne)
- **Status:** Phase 2 complete on 4 domains, zero findings (Akamai WAF)
- **Next:** Pivot strategy — crt.sh, Shodan origin IPs, staging infrastructure
- **Task brief:** `~/esther-lab/engagements/public/playtika/TASK-BRIEF.md`
- **Key finding:** cdn-pl-dev.wooga.com and cdn-pl-staging.wooga.com exist but IP-whitelisted

### X Corp / xAI (HackerOne handle: x)
- **Status:** Phase 1 complete (eb6405f7c verified), Phase 2 in progress
- **Priority:** money.x.com (added 2026-03-12, 5 days old), then *.x.ai, *.grok.com
- **Task brief:** `~/esther-lab/engagements/public/x/TASK-BRIEF.md`
- **Key finding:** All domains behind Cloudflare — same WAF pivot strategy as Playtika

---

## PART 5 — DECISION FRAMEWORKS

### Should ESTHER Scan This?

```
Is it in scope.md?
  No → Do not scan. Full stop.
  Yes ↓
Is this Phase 1 (passive)?
  Yes → Proceed, no approval needed
  No ↓
Has Operator sent APPROVE FSC-... for this domain?
  No → Request approval via Telegram, wait
  Yes ↓
Is this Phase 3 (exploitation)?
  Yes → Request APPROVE for this specific finding
  No → Proceed with Phase 2 active scanning
```

### Is This Worth Filing on H1?

```
Can you reproduce it manually with curl/browser?
  No → False positive, document and move on
  Yes ↓
Is the affected asset in scope?
  No → Do not file
  Yes ↓
Is severity Medium or above?
  No → Document internally, do not file
  Yes ↓
Have you searched H1 for duplicates?
  Not yet → Search first
  Yes, not duplicate ↓
Is the Steps to Reproduce complete?
  No → Complete it before filing
  Yes → File
```

### When ESTHER Reports a Completed Task

1. Run esther-verify.py option 12 — paste her SHAs
2. If any 422 → fabricated, send her back to redo
3. If all real → check the actual file contents make sense
4. Only then accept the report as complete

---

## PART 6 — PHASE ROADMAP

### Completed
- ✅ VPS infrastructure + Docker stack
- ✅ finksecurity.com live with services
- ✅ ESTHER tool inventory (18 tools)
- ✅ Authorization flow (contact form → Telegram → task ID)
- ✅ api.finksecurity.com HTTPS endpoint
- ✅ Bug bounty engagement structure (Playtika, X Corp)
- ✅ Recon playbook + nuclei wrapper
- ✅ H1 scope automation (hackerone-scope-fetch.py)
- ✅ H1 report draft generator
- ✅ esther-verify.py system verification tool
- ✅ Operator handbook (this document)

### In Progress
- ⏳ First H1 submission
- ⏳ X Corp Phase 2 — money.x.com, *.x.ai, *.grok.com
- ⏳ Playtika pivot strategy — staging/origin recon

### Planned
- ⏳ MISSION-BRIEF.md cron + Telegram delivery at session start
- ⏳ Tool installs: BloodHound, Empire, Kiterunner, Arjun
- ⏳ OpenClaw Mission Control dashboard
- ⏳ ESTHER ebook outline
- ⏳ Client authorization flow end-to-end test
- ⏳ H1 API filing (ESTHER files directly after Operator APPROVE)

---

*Fink Security — Operator Handbook · Living document · Update as procedures evolve*
*Commit to FinkSecurity/esther-lab as docs/OPERATOR-HANDBOOK.md*
