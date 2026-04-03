# esther-lab

**ESTHER** is an autonomous AI security research agent built and operated by [Fink Security](https://finksecurity.com). She runs 24/7 on a hardened Kali Linux VPS, conducts authorized bug bounty research, delivers commercial security reports, and publishes findings to [estherops.tech](https://estherops.tech).

This repository is ESTHER's operational brain — scripts, findings, engagement documentation, and the behavioral rules that govern her autonomy.

---

## What ESTHER Does

- **Bug Bounty Research** — Multi-phase reconnaissance and vulnerability research against HackerOne targets (X Corp/xAI). Phases include passive OSINT, subdomain enumeration, active probing, and authenticated endpoint testing.
- **Commercial Security Services** — Automated delivery of Personal Exposure Reports, Breach & Credential Checks, and Home Network Security Checks triggered by Stripe payments.
- **Autonomous Publishing** — Writes and publishes security research to estherops.tech via Git commits. Posts to @finksecurity on X after every publication.
- **Threat Intelligence** — Integrates Shodan, HaveIBeenPwned, VirusTotal, AlienVault OTX, and NVD for real-time intelligence.

---

## Architecture

```
Operator (Telegram) ←→ OpenClaw Gateway ←→ Claude Haiku (OpenRouter)
                              │
                    ┌─────────┴──────────┐
                    │                    │
              LanceDB Memory        Tool Execution
              (nomic-embed-text     (shell, git, web,
               via Ollama)           file system)
                    │
              Kali Linux VPS
              ├── Docker Stack (DVWA, Juice Shop, OpenSearch, Ollama, Portainer)
              ├── nginx + SSL (api.finksecurity.com)
              ├── Stripe payment pipeline
              └── GitHub Actions (estherops.tech, finksecurity.com)
```

**Stack:**
- **Agent Runtime:** [OpenClaw](https://openclaw.ai) 2026.4.1
- **Primary Model:** Claude Haiku 4.5 via OpenRouter
- **Memory:** LanceDB vector memory (nomic-embed-text embeddings via Ollama)
- **Communication:** Telegram bot (operator channel)
- **Infrastructure:** Kali Linux VPS (Hostinger), Docker, nginx, Let's Encrypt SSL
- **Languages:** Python 3, Bash
- **CI/CD:** GitHub Actions → GitHub Pages

---

## Repository Structure

```
esther-lab/
├── engagements/
│   └── public/
│       └── x/                    # X Corp/xAI HackerOne engagement
│           ├── findings/          # Phase-by-phase recon findings
│           ├── submissions/       # HackerOne submission drafts
│           └── scope.md           # Program scope
├── scripts/
│   ├── esther-verify.py          # System health check (14 checks)
│   ├── esther-commit.sh          # Verified git commit helper
│   ├── generate-exposure-report.py  # PDF Personal Exposure Report generator
│   ├── home-network-check.py     # Shodan-based network security report
│   ├── hibp-check.py             # HaveIBeenPwned breach check
│   ├── post-tweet.py             # Autonomous tweet posting
│   ├── generate-briefing.py      # Daily mission brief generator
│   ├── load-scope.py             # HackerOne scope loader
│   ├── poll-tasks.py             # Stripe task dispatcher
│   ├── write-journal.py          # Nightly session journal
│   └── nuclei-scan.py            # Scoped nuclei wrapper
├── docs/
│   ├── CHEATSHEET.md             # Operations reference
│   └── RECON-PLAYBOOK.md         # Engagement methodology
├── SOUL.md                       # Agent behavioral rules
└── HANDOFF.md                    # Session continuity document
```

---

## Key Technical Highlights

### Integrity System
ESTHER has a documented pattern of SHA fabrication (reporting plausible but non-existent git commits). The integrity system addresses this directly:
- `esther-verify.py` runs 14 automated checks including real-time GitHub API SHA verification
- `esther-commit.sh` enforces a pre-commit gate before every push
- All commits verified against GitHub API — 422 responses flagged immediately
- SOUL.md contains explicit fabrication rules with consequences documented

### Payment Pipeline
Fully automated service delivery:
```
Stripe checkout → webhook → handler.py → task file → poll-tasks.py (every 5min)
→ script execution → PDF generation → SendGrid email → client inbox
```
Zero operator involvement after initial Stripe configuration.

### Vector Memory
LanceDB semantic memory allows ESTHER to recall past work across sessions without re-establishing context. Built on nomic-embed-text embeddings running locally in Ollama Docker.

### Verification Script
`esther-verify.py` checks:
- Git commit authenticity (via GitHub API)
- HackerOne submission draft status
- Telegram/notify pipeline health
- SSL certificate expiry
- Scope file freshness
- Tool inventory (18 security tools)
- Docker stack health
- LanceDB memory initialization
- Cron job presence
- Disk space
- SHA fabrication detection (interactive)

---

## Companion Projects

| Project | Description |
|---------|-------------|
| [estherops.tech](https://estherops.tech) | ESTHER's published research — bug bounty findings, methodology writeups, lab exercises |
| [finksecurity.com](https://finksecurity.com) | Commercial security services platform |
| [ezra-lab](https://github.com/FinkSecurity/ezra-lab) | Ezra — autonomous media agent (Mac), generates AI thumbnails via fal.ai FLUX.1 |

---

## Operational Stats (Last 30 Days)

Live stats available at [finksecurity.com/building-esther](https://finksecurity.com/building-esther)

---

## Security & Ethics

All bug bounty research is conducted under HackerOne program authorization. ESTHER operates under strict ethical constraints defined in SOUL.md — no unauthorized scanning, no destructive actions without explicit operator approval, no credential theft or data exfiltration.

Findings are disclosed responsibly through HackerOne's coordinated disclosure process.

---

## About

Built by [Adam Fink](https://finksecurity.com) — solo founder of Fink Security. ESTHER is an experiment in autonomous security research: what happens when you give an AI agent real tools, real targets, and real accountability?

Follow the build at [estherops.tech](https://estherops.tech) and [@finksecurity](https://x.com/finksecurity).
