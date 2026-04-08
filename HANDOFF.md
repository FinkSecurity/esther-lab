# HANDOFF.md — Session Briefing for Next Claude Instance

**Date Created:** 2026-04-08
**Previous Session:** Thumbnail pipeline, SOUL.md cleanup, Xiaomi Phase 3 published
**Context Window:** 32,000 tokens
**Compaction Buffer:** reserveTokensFloor: 20000
**Memory System:** LanceDB + nomic-embed-text (Ollama) initialized

---

## 0. INTRODUCTIONS

Hello Claude, we've been working on an ongoing project across multiple chat sessions. Due to those chats growing too large we use a HANDOFF.md file and frequent chat sessions to maintain productivity. The project includes two OpenClaw agents — ESTHER on a cloud VPS and Ezra on a local MacBook — and four GitHub repos:

- esther-lab
- ezra-lab
- finksecurity-site
- estherops-site

ESTHER performs bug bounty engagements and automated consumer services, then publishes blog posts and tweets. She now generates thumbnails autonomously on the VPS via fal.ai — no Ezra involvement needed for publishing.

---

## 1. CURRENT ENGAGEMENT STATUS

### Xiaomi (HackerOne Bug Bounty)

**Status:** Phases 1-3 complete + published, Phase 4 ready to start

**Completed Work:**
- **Phase 1:** 90+ subdomains, 5 live hosts confirmed, blog live, tweet posted
- **Phase 2:** 16 subdomains probed, 3 live services confirmed, blog published
  - https://app.mi.com (200, Nginx/IIS, Mi App Store)
  - https://b.mi.com (200, Nginx+OpenResty, Cloud Backend — IDOR risk)
  - https://market.xiaomi.com (200, Apache+PHP 7.4 EOL — high priority)
- **Phase 3 (Nuclei):** 0 CVEs matched, WAF blocking confirmed (22% error rate), blog published
  - Blog: estherops.tech/reports/xiaomi-phase3/
  - Tweet: https://x.com/finksecurity/status/2041925715642478811

**Phase 4 Ready (Manual Web App Testing):**
- [ ] API endpoint discovery on b.mi.com (IDOR on /api/user/*, integer ID enumeration)
- [ ] PHP 7.4 info disclosure + deserialization on market.xiaomi.com
- [ ] Authentication bypass on account.xiaomi.com redirect chain
- [ ] Business logic flaws (payment flow, account management)

**Phase 5:** File on HackerOne once findings confirmed

---

### x.ai (Suspended)

**Status:** SUSPENDED — API credits exhausted
- 14 vulnerabilities identified (2 critical, 8 high, 4 medium)
- Resume condition: budget replenished + operator approval

### Playtika — CANCELLED

---

## 2. INFRASTRUCTURE STATE

### Thumbnail Pipeline (NEW - 2026-04-08)
ESTHER generates thumbnails directly on VPS via fal.ai:
```bash
python3 ~/esther-lab/scripts/generate_image.py \
  --prompt "dark cyberpunk, [topic], cyan #22d3ee accent, dark background #0a0a12, Fink Security branding, no warm tones, no orange" \
  --title "[Post Title]" \
  --subtitle "[Subtitle]" \
  --out ~/estherops-site/static/thumbnails/<slug>.png
```
- `generate_image.py` is deployed to `/home/esther/esther-lab/scripts/`
- `FAL_API_KEY` is set in ESTHER's `.bashrc`
- No Ezra, no SCP, no Telegram bridge needed

### OpenClaw Config
- **exec.ask:** off (verified working)
- **compaction.reserveTokensFloor:** 20000
- **contextTokens:** 32,000
- **Model:** claude-haiku-4.5 via OpenRouter

### APIs
- OpenRouter: $5 daily / $50 monthly cap
- HackerOne API: **AUTH FAILING (401) — needs investigation**
- GitHub CLI: working
- Telegram: working
- X/Twitter: working

### Cron Jobs
- `update-featured-posts.py` — 1st and 15th at 9am UTC
- `poll-tasks.py` — every 5 minutes
- `generate-briefing.py` — 8am daily
- `ingest-openclaw-logs.py` — hourly
- `write-journal.py` — 11pm nightly
- `read-journal.py` — 8am daily

---

## 3. EZRA STATUS

Ezra's role is under review. He is currently not involved in the publishing pipeline.
Potential future uses: local model tasks via Ollama, report formatting, offline RAG research.
The Telegram group bridge attempt was abandoned — Telegram blocks bot-to-bot messages in groups.
The Fink Security Ops group chat exists with all bots added but is not actively used.

---

## 4. OPEN ITEMS / NEXT SESSION

### Critical
- [ ] **Xiaomi Phase 4** — manual web app testing (see section 1) — THIS IS NEXT
- [ ] **HackerOne API 401** — investigate token in ~/.config/h1/config.yml

### Infrastructure
- [ ] **SendGrid** — end-to-end test (send findings notification email)
- [ ] **Stripe prices** — update to $39 (Privacy Essentials) and $55 (Full Shield)
- [ ] **update-stats.py** — restore weekly cron (currently disabled)

### Content
- [ ] **Old blog posts** — migrate remaining `image:` fields to `cover:`
- [ ] **finksecurity.com blog** — auto-updates on 1st/15th via cron

---

## 5. GIT COMMITS (This Session) — All Verified Real

### estherops-site
- `8ec3211` — Xiaomi Phase 3 blog post + thumbnail (single commit ✅)

### esther-lab
- `7b0fc57` — group chat scripts added
- `9085b5d` — SOUL.md cleaned + generate_image.py deployed

---

## 6. KEY RULES

### Git Commit Verification
- After every push: `gh api repos/FinkSecurity/<repo>/commits/<sha>`
- 422 = fabricated SHA (trust violation)
- Always paste raw JSON, never paraphrase

### Publishing Checklist
- Generate thumbnail first with generate_image.py
- Use `cover:` field (not `image:`)
- Stage thumbnail BEFORE committing post — single commit always
- Verify commit SHA after push
- Verify URL returns 200 before tweeting
- Post tweet autonomously — no approval needed

### Exec Gate
- `"ask": "off"` in openclaw.json — verified working
- ESTHER executes commands autonomously without approval prompts

---

**End of HANDOFF.md**
