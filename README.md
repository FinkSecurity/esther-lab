# esther-lab

**Fink Security** — AI-first cybersecurity research lab.

ESTHER (Enumeration, Surveillance, Threat Hunting, Hacking, Exploitation, Reporting) is an autonomous AI security agent built to think like an attacker. This repository is her operational workspace — findings, tools, engagement docs, and lab exercises committed in real time.

> "Your friendly neighborhood threat hunter. She's built to think like an attacker so you don't have to face one unprepared. And most importantly: she's on your side."

---

## Repository Structure

```
esther-lab/
├── SOUL.md                        # ESTHER's operating rules, ethics, and methodology
├── ENVIRONMENT.md                 # VPS infrastructure and tool inventory
├── AUTHORIZATION-PROTOCOL.md     # Client authorization framework
├── docker-compose.yml             # Lab Docker stack (OpenSearch, DVWA, Juice Shop, etc.)
├── LICENSE                        # AGPL-3.0
│
├── engagements/                   # Active bug bounty & client engagements
│   ├── public/                    # HackerOne and public program work
│   │   ├── playtika/              # Playtika HackerOne program
│   │   │   ├── scope.md           # In-scope targets and operating rules
│   │   │   ├── findings/          # Recon output, scan results, nuclei logs
│   │   │   ├── submissions/       # H1 report drafts (DRAFT-*.md)
│   │   │   └── TASK-BRIEF.md      # Current phase status and next steps
│   │   └── x/                     # X Corp / xAI HackerOne program
│   │       ├── scope.md           # In-scope targets (twitter, x.ai, grok, money)
│   │       ├── findings/          # Recon output and investigation notes
│   │       ├── submissions/       # H1 report drafts
│   │       └── TASK-BRIEF.md      # Current phase status and next steps
│   └── private/                   # Paid client work (gitignored)
│
├── docs/                          # Reference documentation
│   ├── OPERATOR-HANDBOOK.md       # How to run Fink Security and manage ESTHER
│   ├── RECON-PLAYBOOK.md          # Full recon methodology — read before every engagement
│   ├── CLIENT-ENGAGEMENT-TEMPLATE.md  # Template for paid client engagements
│   ├── LAB-INFRASTRUCTURE.md      # Docker stack and VPS service reference
│   ├── OPENSEARCH-LOG-INTEGRATION.md  # OpenSearch audit log setup
│   ├── esther-tool-audit.md       # Verified tool inventory
│   └── openclaw-vps-guide.md      # OpenClaw workspace configuration
│
├── scripts/                       # Automation and utility scripts
│   ├── esther-verify.py           # Interactive system verification tool (11 checks)
│   ├── generate-briefing.py       # Auto-generates MISSION-BRIEF.md from repo state
│   ├── generate-report.py         # Security report generator
│   ├── hackerone-scope-fetch.py   # Pulls live scope from HackerOne API
│   ├── nuclei-scan.py             # Targeted nuclei wrapper (enforces profile/rate limits)
│   └── setup-engagement.py        # Creates engagement directory structure
│
├── targets/                       # Lab environments and vulnerable applications
│   ├── README.md                  # Target index and access instructions
│   ├── dvwa/                      # DVWA — PHP vulnerable web app (port 8081)
│   │   └── README.md
│   └── juice-shop/                # OWASP Juice Shop (port 3000)
│       ├── README.md
│       └── exercises/             # Completed walkthroughs (SQLi, auth bypass, API abuse)
│
├── posts/                         # Blog content published to estherops.tech
│   ├── intelligence/              # Threat intelligence reports
│   ├── labs/                      # Lab writeups and exercises
│   ├── methods/                   # Methodology articles
│   └── reports/                   # Formal assessment reports
│
├── osint-exercises/               # OSINT tutorials and completed exercises
│   └── INDEX-WEBCAM-EXERCISE.md   # Boulder webcam OSINT exercise index
│
└── logs/                          # Operational logs (not for publication)
    ├── execution.log
    ├── auth-failures.log
    └── overrides.log
```

---

## Key Directories

**`engagements/`** — Active bug bounty and client work. Each program has its own directory with a `scope.md` (auto-fetched from HackerOne API), `findings/` for raw recon output, `submissions/` for H1 report drafts, and a `TASK-BRIEF.md` tracking current phase and next steps. Private client engagements live in `engagements/private/` which is gitignored.

**`docs/`** — Permanent reference documentation. Start with `OPERATOR-HANDBOOK.md` for a full picture of how Fink Security operates, and `RECON-PLAYBOOK.md` before any engagement — it covers the full investigation methodology from passive recon through WAF bypass thinking, AEM/LLM-specific techniques, and H1 filing guidance.

**`scripts/`** — Automation tools ESTHER uses on every engagement. `esther-verify.py` runs 11 system health checks including a SHA fabrication detector. `nuclei-scan.py` enforces targeted template selection — ESTHER never runs all 3768 templates. `hackerone-scope-fetch.py` pulls live scope directly from the H1 API before each engagement begins.

**`targets/`** — Local lab environments for practice and tool validation. DVWA and Juice Shop run in Docker on the VPS. Completed exercises are mapped to MITRE ATT&CK techniques.

**`posts/`** — Technical content published live to [estherops.tech](https://estherops.tech). Includes real findings, lab writeups, and security methodology articles.

---

## Active Engagements

| Program | Platform | Phase | Status |
|---------|----------|-------|--------|
| Playtika | HackerOne | Phase 2 | Active scanning complete, pivot to staging recon |
| X Corp / xAI | HackerOne | Phase 1→2 | Passive recon complete, Phase 2 in progress |

---

## Infrastructure

| Component | Details |
|-----------|---------|
| VPS | Kali Linux — 45.82.72.151, SSH port 2222 |
| Website | [finksecurity.com](https://finksecurity.com) (GitHub Pages) |
| API | [api.finksecurity.com](https://api.finksecurity.com) (nginx → notify relay) |
| Research blog | [estherops.tech](https://estherops.tech) (Hugo) |
| Docker stack | OpenSearch, DVWA, Juice Shop, Portainer, Ollama |

---

## Authorization

All external scanning requires explicit authorization:

1. **Client authorizes** via [finksecurity.com](https://finksecurity.com) contact form — digital checkbox, WHOIS logged, task ID generated
2. **Operator approves** via Telegram (`APPROVE FSC-YYYYMMDD-HHMM`) before ESTHER is tasked
3. **Bug bounty** — HackerOne safe harbor = written authorization for in-scope targets

ESTHER operates under a strict phase gate model. See `SOUL.md` and `AUTHORIZATION-PROTOCOL.md` for full details.

---

*Fink Security — AI-first cybersecurity. Built in public.*
