# HANDOFF.md — Session Briefing for Next Claude Instance

**Date Created:** 2026-04-06
**Previous Session:** Major site updates, ESTHER/Ezra workflow test, Xiaomi Phase 2 published
**Context Window:** 32,000 tokens
**Compaction Buffer:** reserveTokensFloor: 20000 (set last session)
**Memory System:** LanceDB + nomic-embed-text (Ollama) initialized

---

## 0. INTRODUCTIONS

Hello, Claude, we've been working on an on-going project in other chat sessions and due to those chats growing too large we decided to leverage a handoff.md file and more frequent chat sessions to increase our productivity together.  The project includes two OpenClaw agents, one running on a cloud VPS and the other on my local MacBook.  There are a total of four Github repos we have so far, one for each OpenClaw Agent and the one for each website.  

- esther-lab
- ezra-lab
- finksecurity-site
- estherops-site

The workflow is Esther performs a task, typically a Bug Bounty engagement but we offer severeal automated services for individuals, and then tweets and creates a blog post.  Before tweeting or posting to the blog Esther requests an image from Ezra who generates the image on my local Macbook and uploads it to the VPS so Esther can use it.  Cost efficiency is always the priority until we're able to recoup some of the operating costs.  


## 1. CURRENT ENGAGEMENT STATUS

### Xiaomi (HackerOne Bug Bounty)

**Status:** Phases 1-3 complete, Phase 2 blog published, Phase 4 ready to start

**Completed Work:**
- **Phase 1:** 90+ subdomains, 5 live hosts confirmed, blog live, tweet posted
- **Phase 2:** 16 subdomains probed, 3 live services confirmed, blog published
  - https://app.mi.com (200, Nginx/IIS, Mi App Store)
  - https://b.mi.com (200, Nginx+OpenResty, Cloud Backend — IDOR risk)
  - https://market.xiaomi.com (200, Apache+PHP 7.4 EOL — high priority)
  - Blog: estherops.tech/reports/xiaomi-phase2/
  - Tweet: https://x.com/finksecurity/status/2040926292963684388
- **Phase 3 (Nuclei):** 0 CVEs matched, WAF blocking confirmed (22% error rate)

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

### OpenClaw Config
- **exec.ask:** off (verified working via live test)
- **compaction.reserveTokensFloor:** 20000 (set 2026-04-05)
- **contextTokens:** 32,000
- **Model:** claude-haiku-4.5 via OpenRouter

### APIs
- OpenRouter: $5 daily / $50 monthly cap
- HackerOne API: **AUTH FAILING (401) — needs investigation**
- GitHub CLI: working
- Telegram: working
- X/Twitter: working (post-tweet.py verified end-to-end)

### Cron Jobs
- `update-featured-posts.py` — 1st and 15th at 9am UTC (NEW)
- `poll-tasks.py` — every 5 minutes
- `generate-briefing.py` — 8am daily
- `ingest-openclaw-logs.py` — hourly
- `write-journal.py` — 11pm nightly
- `read-journal.py` — 8am daily

---

## 3. SITE UPDATES (2026-04-05 Session)

### finksecurity.com (finksecurity-site repo)
- Blog section rebuilt — RSS replaced with static `featured-posts.json`
- `update-featured-posts.py` fetches top 3 posts from estherops.tech RSS
- Dead RSS code cleaned out (parseRSS, stripHtml, getCategory, FEED)
- Building ESTHER page: Week 5 timeline entry added
- Building ESTHER page: hero image added (esther-hero-v4.png, two-column layout)
- stats.json: critical_findings updated to 2 (x.ai engagement)
- Terminal block in About section extended with delivery + status bar
- Nav alignment fixed (align-items: center restored)
- Footer width fix attempted (scrollbar-gutter: stable)

### estherops.tech (estherops-site repo)
- Terminal theme orange → Fink Security cyan palette (#0a0a12 bg, #0ea5e9 accent)
- 12 missing Ezra thumbnails committed to repo
- Xiaomi Phase 2 post published with thumbnail

---

## 4. ESTHER/EZRA WORKFLOW

### Current Workflow
1. ESTHER completes bug bounty phase + writes findings
2. Operator sends Ezra thumbnail request via Telegram (manual step)
3. Ezra generates image, SCPs to VPS: `~/estherops-site/static/thumbnails/<slug>.png`
4. Ezra confirms upload via Telegram
5. Operator tells ESTHER to publish post + commit thumbnail + tweet

### Known Gap (fix next session)
- ESTHER must `git add static/thumbnails/<slug>.png` BEFORE committing post
- Currently thumbnail and post land in separate commits — causes missing image on deploy
- Add to SOUL.md: **PUBLISHING RULE:** Always stage thumbnail with post in single commit

### Ezra SCP Command Template
scp -i /Users/afink/tools/ezra-lab/ezra-vps.key -P 2222 
/Users/afink/tools/ezra-lab/media/thumbnails/<slug>.png 
esther@45.82.72.151:~/estherops-site/static/thumbnails/<slug>.png

### Thumbnail Style Prompt
> dark cyberpunk, cyan #22d3ee accent color, dark background #0a0a12, [topic] visualization, Fink Security branding, no warm tones, no orange

---

## 5. OPEN ITEMS / NEXT SESSION

### Critical
- [ ] **HackerOne API 401** — investigate token in ~/.config/h1/config.yml
- [ ] **SOUL.md publishing rule** — add thumbnail staging requirement
- [ ] **Xiaomi Phase 4** — manual web app testing (see section 1)

### Infrastructure
- [ ] **SendGrid** — end-to-end test (send findings notification email)
- [ ] **Stripe prices** — update to $39 (Privacy Essentials) and $55 (Full Shield)
- [ ] **update-stats.py** — restore weekly cron (currently disabled)

### Content
- [ ] **Xiaomi Phase 3 blog post** — write + publish (nuclei findings, WAF analysis)
- [ ] **Old blog posts** — migrate remaining `image:` fields to `cover:`
- [ ] **finksecurity.com blog** — will auto-update on 1st/15th via cron

### Automation
- [ ] **ESTHER/Ezra Telegram bridge** — wire agents so ESTHER can request thumbnails directly
- [ ] **Publishing rule in SOUL.md** — thumbnail must be staged before post commit

---

## 6. GIT COMMITS (Last Session) — All Verified Real

### finksecurity-site
- `2cfd72e` — RSS → static featured-posts.json
- `49687dc` — dead RSS code removed
- `2795b7f` — 3 posts populated from RSS
- `fadba34` — Week 5 timeline + critical_findings = 2
- `69c7587` — ESTHER hero image added
- `68dffe3` — hero image v4 + positioning fix
- Various nav/terminal/footer fixes

### estherops-site
- `6019e1c` — cyan theme override
- `a9ac50a` — accent color tuned to #0ea5e9
- `691db61` — 12 missing thumbnails added
- `8a2f34c` — Xiaomi Phase 2 blog post

---

## 7. KEY RULES

### Git Commit Verification
- After every push: `gh api repos/FinkSecurity/<repo>/commits/<sha>`
- 422 = fabricated SHA (trust violation)
- Always paste raw JSON, never paraphrase

### Publishing Checklist
- Use `cover:` field (not `image:`)
- Stage thumbnail BEFORE committing post
- Verify commit SHA after push
- Post tweet after deploy confirmed

### Exec Gate
- `"ask": "off"` in openclaw.json — verified working
- ESTHER executes commands autonomously without approval prompts

---

**End of HANDOFF.md**
