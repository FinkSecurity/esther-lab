# HANDOFF.md — Session Briefing for Next Claude Instance

**Date Created:** 2026-04-08
**Previous Session:** Xiaomi complete, ESTHER thumbnail pipeline, Ezra reidentified as personal assistant
**Context Window:** 32,000 tokens
**Compaction Buffer:** reserveTokensFloor: 20000
**Memory System:** LanceDB + nomic-embed-text (Ollama) initialized on both agents

---

## 0. INTRODUCTIONS

Hello Claude, we've been working on an ongoing project across multiple chat sessions. Due to those chats growing too large we use a HANDOFF.md file and frequent chat sessions to maintain productivity. The project includes two OpenClaw agents — ESTHER on a cloud VPS and Ezra on a local MacBook — and four GitHub repos:

- esther-lab
- ezra-lab
- finksecurity-site
- estherops-site

ESTHER performs bug bounty engagements and automated consumer services, then publishes blog posts and tweets. She generates thumbnails autonomously on the VPS via fal.ai. Ezra is now Adam's personal assistant — Obsidian vault curator, career development support, GitHub portfolio helper, and creative projects.

---

## 1. CURRENT ENGAGEMENT STATUS

### Xiaomi (HackerOne Bug Bounty)
**Status: COMPLETE — No findings**
- Phase 1-4 all done, formal no-findings summary committed
- All targets demonstrated mature defensive posture (WAF, cryptographic auth, patched software)
- PHP 7.4 EOL noted as informational on market.xiaomi.com (inaccessible from non-CN regions)
- Blog posts published for Phase 1, 2, and 3

### x.ai — CANCELLED
### Playtika — CANCELLED

### Next HackerOne Target
**Status: TBD — needs selection next session**
- Look for programs with wider scope, less WAF coverage, decent bounties
- ESTHER's toolchain is proven end-to-end

---

## 2. INFRASTRUCTURE STATE

### ESTHER (VPS — 45.82.72.151:2222)

**Thumbnail Pipeline (fully autonomous):**
```bash
python3 ~/esther-lab/scripts/generate_image.py \
  --prompt "dark cyberpunk, [topic], cyan #22d3ee accent, dark background #0a0a12, Fink Security branding, no warm tones, no orange" \
  --title "[Post Title]" \
  --subtitle "[Subtitle]" \
  --out ~/estherops-site/static/thumbnails/<slug>.png
```
- `generate_image.py` deployed to `/home/esther/esther-lab/scripts/`
- `FAL_API_KEY` set in ESTHER's `.bashrc`
- No Ezra, no SCP, no Telegram bridge needed

**OpenClaw Config:**
- exec.ask: off (verified working)
- compaction.reserveTokensFloor: 20000
- contextTokens: 32,000
- Model: claude-haiku-4.5 via OpenRouter

**APIs:**
- OpenRouter: $5 daily / $50 monthly cap
- HackerOne API: WONTFIX — use manual CSV download from H1 web UI instead
- GitHub CLI: working
- Telegram: working
- X/Twitter: working

**Cron Jobs:**
- `update-featured-posts.py` — 1st and 15th at 9am UTC
- `poll-tasks.py` — every 5 minutes
- `generate-briefing.py` — 8am daily
- `ingest-openclaw-logs.py` — hourly
- `write-journal.py` — 11pm nightly
- `read-journal.py` — 8am daily

### Ezra (MacBook Pro)

**Status: Reidentified as personal assistant**
- Primary model: qwen3.5:4b (fast, local, free)
- Fallback: openrouter/anthropic/claude-haiku-4.5
- Gemma4 pulled and available but not yet working with OpenClaw (tool calling issues — revisit when OpenClaw updates)
- Docker sandbox: DISABLED (`"mode": "off"`) — Docker Desktop not needed
- Obsidian vault access: `~/tools/obsidian-vaults/Fink Security`
- No longer responsible for thumbnails — ESTHER owns that

**Ezra's Role:**
1. Obsidian vault management and organization
2. Fink Security project awareness
3. GitHub portfolio documentation for career development
4. Career support toward cybersecurity/AI roles
5. Creative projects (photography site etc.) when needed
6. Daily assistant tasks

**Pending for Ezra:**
- [ ] Update SOUL.md to reflect personal assistant role
- [ ] Remove all Hunter + Architect references from estherops.tech
- [ ] Remove any other Ezra references from estherops-site

---

## 3. CONSUMER SERVICES PIPELINE

**Status: Partially configured — needs testing**

### Active Services (finksecurity.com)
| Service | Price | Type |
|---------|-------|------|
| Breach & Credential Check | $15 | Automated |
| Personal Exposure Report | $29 | Automated |
| Home Network Security Check | $20 | Automated |
| Custom Security Assessment | Contact | Business |
| Penetration Testing | Coming Soon | Business |
| Cloud Security Review | Coming Soon | Business |
| Privacy Essentials Bundle | $39 | Bundle |
| Full Shield Bundle | $55 | Bundle |

### Open Items
- [ ] **Stripe** — verify price IDs in dashboard match handler.py, remove old products
- [ ] **SendGrid** — end-to-end test (DNS confirmed, pipeline not tested)
- [ ] **handler.py** — remove discontinued services, keep only current lineup
- [ ] **update-stats.py** — restore weekly cron (currently disabled)

---

## 4. OPEN ITEMS / NEXT SESSION

### Critical
- [ ] **Next HackerOne target** — select and brief ESTHER
- [ ] **Stripe cleanup** — remove old products, verify current price IDs
- [ ] **SendGrid end-to-end test**

### Ezra
- [ ] **SOUL.md rewrite** — personal assistant role
- [ ] **estherops.tech cleanup** — remove Hunter + Architect and Ezra references

### Infrastructure
- [ ] **Gemma4 + OpenClaw** — revisit when OpenClaw updates
- [ ] **update-stats.py** — restore weekly cron

### Content
- [ ] **Old blog posts** — migrate remaining `image:` fields to `cover:`

---

## 5. GIT COMMITS (This Session) — All Verified Real

### estherops-site
- `8ec3211` — Xiaomi Phase 3 blog post + thumbnail (single commit)

### esther-lab
- `9085b5d` — SOUL.md cleaned + generate_image.py deployed
- `f78d7cd` — Phase 4 manual testing complete
- `4e1e6c2` — Xiaomi formal no-findings summary
- `8445ca4` — Xiaomi STATUS marked COMPLETE

---

## 6. KEY RULES

### Git Commit Verification
- After every push: `gh api repos/FinkSecurity/<repo>/commits/<sha>`
- 422 = fabricated SHA (trust violation)
- Always paste raw JSON, never paraphrase

### Publishing Checklist
- Generate thumbnail first with generate_image.py on VPS
- Use `cover:` field (not `image:`)
- Stage thumbnail + post in single commit always
- Verify URL returns 200 before tweeting
- Post tweet autonomously — no approval needed

### Exec Gate
- ESTHER: `"ask": "off"` — verified working
- Ezra: `"ask": "off"`, sandbox `"mode": "off"` — Docker not needed

---

**End of HANDOFF.md**
