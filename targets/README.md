# Lab Targets Overview

Active vulnerable web applications for hands-on security training and exploitation research.

---

## Current Active Targets

| Target | Type | Port | Status | URL | Purpose |
|--------|------|------|--------|-----|---------|
| **Juice Shop** | Node.js Web App | 3000 | ✅ Running | http://localhost:3000 | OWASP Top 10 training |
| **DVWA** | PHP Web App | 8080 | ✅ Running | http://localhost:8080 | Beginner penetration testing |

Each target has a dedicated README with:
- Access credentials & setup instructions
- Completed exercises linked to published posts
- Known vulnerabilities (with CVSS scores)
- MITRE ATT&CK technique mappings
- SQL injection, authentication bypass, API abuse, command injection, etc.

---

## Detailed Target Guides

### 🔴 [OWASP Juice Shop](juice-shop/)

**What it is:** Modern, intentionally vulnerable Node.js web application.  
**Focus:** OWASP Top 10, API vulnerabilities, business logic flaws  
**Difficulty:** Medium  
**Exercises:** [Complete list](juice-shop/README.md)

```bash
docker run -d -p 3000:3000 -e NODE_ENV=development --name juice-shop bkimminich/juice-shop:latest
```

### 🟠 [DVWA](dvwa/)

**What it is:** Classic PHP-MySQL vulnerable application.  
**Focus:** SQL injection, file inclusion, CSRF, command execution  
**Difficulty:** Beginner-friendly  
**Exercises:** [Complete list](dvwa/README.md)

```bash
docker run -d -p 8080:80 -e MYSQL_ROOT_PASSWORD=root --name dvwa vulnerables/web-dvwa:latest
```

---

## Adding a New Target

Follow this template to add a new target:

### Step 1: Create Target Directory

```bash
mkdir -p targets/new-target-name
touch targets/new-target-name/README.md
```

### Step 2: Populate Target README

Use this template for `targets/new-target-name/README.md`:

```markdown
# [Target Name]

## Overview

**What it is:** Brief description (1-2 sentences)  
**Technology:** Framework/language  
**Difficulty Level:** Beginner / Intermediate / Advanced  
**Primary Focus:** Main vulnerability categories  
**Maintenance:** Last verified: YYYY-MM-DD

## Access

**URL:** http://localhost:PORT  
**Default Credentials:** username / password (if applicable)  
**Setup Command:** Docker run or docker-compose snippet

## Environment

- Framework: [X]
- Language: [Y]
- Database: [Z] (if applicable)
- Authentication: [Type]

## Known Vulnerabilities

| CVE / ID | Title | Severity | CVSS | MITRE Technique |
|----------|-------|----------|------|-----------------|
| CVE-XXXX-XXXXX | Vulnerability Title | CRITICAL | 9.0 | T1234.567 |

## Completed Exercises

- [Exercise Name](../../posts/exercise-name.md) — Description — Status: ✅ Complete
- [Another Exercise](../../findings/exercise-id.md) — Description — Status: ✅ Complete

## MITRE ATT&CK Mapping

**Techniques Covered:**
- T1234: [Technique Name] — SQLi exploitation
- T5678: [Technique Name] — Privilege escalation
- T9012: [Technique Name] — Data exfiltration

## Notes & Observations

- Key findings from exploitation
- Patch recommendations
- Best practices for mitigation

---

**Last Updated:** YYYY-MM-DD  
**Status:** Active
```

### Step 3: Document & Commit

```bash
git add targets/new-target-name/
git commit -m "Add new target: new-target-name"
git push origin main
```

---

## Planned Future Targets

These targets are planned for Phase 4+ expansion:

### 📋 WebGoat (OWASP)
- **Focus:** Secure coding principles, web vulnerability education
- **Difficulty:** Beginner
- **ETA:** Q2 2026

### 📋 Metasploitable 2
- **Focus:** Linux exploitation, privilege escalation, post-exploitation
- **Difficulty:** Intermediate
- **ETA:** Q2 2026

### 📋 HackTheBox Lab (Community)
- **Focus:** Real-world scenarios, Active Directory, cloud security
- **Difficulty:** Advanced
- **ETA:** Q3 2026

### 📋 PortSwigger WebAcademy (Online)
- **Focus:** Burp Suite integration, API testing, advanced web vulnerabilities
- **Difficulty:** Intermediate-Advanced
- **ETA:** Q3 2026

---

## Repository Integration

Each target exercise produces:

1. **Finding Document** — `findings/target-exercise-001.md` (CVSS, remediation)
2. **Blog Post** — `posts/target-exercise-name.md` (walkthrough, learnings)
3. **Exercise Link** — Updated in target README with status & link

---

## Health Checks

Verify all targets are running:

```bash
# Juice Shop
curl -s http://localhost:3000 | grep -q "Juice Shop" && echo "✅ Juice Shop" || echo "❌ Juice Shop"

# DVWA
curl -s http://localhost:8080 | grep -q "DVWA" && echo "✅ DVWA" || echo "❌ DVWA"
```

---

**Last Updated:** 2026-03-10  
**Maintained By:** ESTHER 🦂
