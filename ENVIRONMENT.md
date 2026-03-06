# ENVIRONMENT.md — API Keys & Configuration

## Status: 2026-03-06

### API Keys Configured

#### Shodan API
- **Status:** ✅ Active
- **Key Location:** `~/.openclaw/.env` → `SHODAN_API_KEY`
- **Verification:** Successfully authenticated and executed 8 queries (2026-03-06)
- **Last Used:** 2026-03-06 19:20 UTC
- **Capabilities:** Internet-wide host search, filtering, geolocation queries

#### GitHub CLI (gh)
- **Status:** ✅ Active
- **Configuration:** `~/.gitconfig` + system Git
- **User:** ESTHER / esther@finksecurity.com
- **Verification:** Successfully pushed to FinkSecurity org repositories
- **Last Used:** 2026-03-06 19:35 UTC

#### Brave Search API
- **Status:** ❌ Not Configured
- **Location:** Would be `~/.openclaw/.env` → `BRAVE_API_KEY`
- **Action Required:** Configure when available

#### Tavily Search API
- **Status:** ❌ Not Configured
- **Location:** Would be `~/.openclaw/.env` → `TAVILY_API_KEY`
- **Action Required:** Configure when available

### Git Configuration

**User:** ESTHER  
**Email:** esther@finksecurity.com  
**Remote Repos:**
- esther-lab: https://github.com/FinkSecurity/esther-lab.git
- estherops-site: https://github.com/FinkSecurity/estherops-site.git

**Verified Pushes (2026-03-06):**
- esther-lab: OSINT exercise (real data, honest findings)
- estherops-site: OpenClaw VPS setup guide

### Environment Variables (Checked 2026-03-06)

**Active:**
```
SHODAN_API_KEY=<configured>
```

**Available but Not Active:**
```
(None at this time)
```

**Recommended Setup:**
```
BRAVE_API_KEY=<pending>
TAVILY_API_KEY=<pending>
HIBP_API_KEY=<pending>
CENSYS_API_KEY=<pending>
```

---

**Last Updated:** 2026-03-06 19:45 UTC  
**Next Review:** Monday 2026-03-10
