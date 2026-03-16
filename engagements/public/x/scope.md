# Scope: x
<!-- AUTO-GENERATED from HackerOne CSV export — DO NOT EDIT MANUALLY -->
<!-- Source: scopes_for_x_at_2026-03-16_02_18_27_UTC.csv -->
<!-- Imported: 2026-03-17 -->

## Program

- **Handle:** x
- **Platform:** HackerOne
- **H1 URL:** https://hackerone.com/x
- **Account:** esther-lab (Fink Security)
- **Program type:** X Corp — covers X (Twitter), xAI, Grok

---

## IN SCOPE

### Wildcard domain 💰 (max severity: CRITICAL)

- `*.twitter.com` 💰
- `*.vine.co` 💰
- `*.twimg.com` 💰 — Note: availability=high, confidentiality=medium, integrity=high
- `*.x.ai` 💰 — **xAI / Grok API surface** (added 2024-10-09)
- `*.x.com` 💰 — (added 2024-12-18)
- `*.grok.com` 💰 — (added 2025-04-08)
- `*.twitter.biz` 💰 — (added 2025-06-17)

### URL (bounty eligible, max severity: CRITICAL)

- `gnip.com` 💰
- `x.com` 💰
- `grok.com` 💰
- `chat.x.com` 💰 — availability=high, confidentiality=high, integrity=high (added 2026-01-04)
- `grokipedia.com` 💰 — availability=high, confidentiality=high, integrity=high (added 2026-02-23)
- `money.x.com` 💰 — availability=high, confidentiality=high, integrity=high (added 2026-03-12)

### URL (submission eligible, NO bounty)

- `t.co` — No bounty. Note: actively being fixed, not accepting t.co reports currently
- `xadsacademy.com` — No bounty, max severity: medium

### Mobile Apps 💰

- `com.twitter.android` (Google Play) 💰
- `com.atebits.Tweetie2` (Apple App Store) 💰
- `ai.x.GrokApp` (Apple App Store) 💰 — Grok iOS app (added 2025-04-08)
- `ai.x.grok` (Google Play) 💰 — Grok Android app (added 2025-04-28)

---

## OUT OF SCOPE — NEVER SCAN THESE

- `status.twitter.com` — third party hosted (status.io), not eligible for submission
- Any target not explicitly listed above

---

## PRIORITY TARGETS FOR ESTHER

### Tier 1 — Highest value (new, high CIA requirements)
- `chat.x.com` — chat interface, confidentiality=high
- `money.x.com` — financial feature, all requirements=high (added 2026-03-12, very new)
- `grokipedia.com` — new product surface (added 2026-02-23)
- `*.grok.com` — entire Grok subdomain space
- `*.x.ai` — xAI API surface (Grok API, internal services)

### Tier 2 — Established but large attack surface
- `*.x.com` — main platform
- `*.twitter.com` — legacy but still in scope
- `grok.com` — main Grok domain

### Tier 3 — Lower priority
- `*.twimg.com` — CDN/media, limited attack surface
- `gnip.com` — data API, enterprise
- `*.vine.co` — legacy, likely limited surface
- `*.twitter.biz` — business/ads

---

## ESTHER OPERATING RULES FOR THIS ENGAGEMENT

- Max rate: **10 req/sec** on all active scanning
- Phase 1 (passive recon): ✅ Authorized — no approval needed
- Phase 2 (active scanning): ⏳ Request Operator approval per domain
- Phase 3 (exploitation): ⏳ Request Operator approval per finding
- Always commit findings to `engagements/public/x/findings/` and verify with `gh api`
- Never scan OUT OF SCOPE assets under any circumstances
- `t.co` — do not report issues even if found, they are known and being fixed
- `status.twitter.com` — do not scan, third party hosted
- Null results are valid findings — document honestly

## NUCLEI PROFILE FOR THIS ENGAGEMENT

Use `--profile ai-llm` for `*.x.ai` and `*.grok.com` targets.
Use `--profile web` for `*.x.com` and `*.twitter.com` targets.
Use `--profile gaming` (API-focused) for `chat.x.com` and `money.x.com`.

## MANUAL TESTING PRIORITIES

For AI/LLM surfaces (`*.x.ai`, `*.grok.com`, `grok.com`):
- Prompt injection via API parameters
- Conversation ID IDOR (can you access other users' chats?)
- API key exposure in responses
- CORS misconfiguration on API endpoints
- Rate limiting bypass on Grok API
- System prompt extraction attempts
- `chat.x.com` — session handling, auth flow
- `money.x.com` — payment flow, IDOR on transaction IDs

---

_Imported from HackerOne CSV · Fink Security / esther-lab · 2026-03-17_
