---
title: "T1083: File and Directory Discovery — DVWA Case Study"
date: 2026-03-05
author: ESTHER
tags:
  - MITRE ATT&CK
  - Reconnaissance
  - File Discovery
  - DVWA
  - Command Injection
categories:
  - Intelligence
  - Threat Analysis
---

## Overview

**MITRE ATT&CK Technique:** T1083 — File and Directory Discovery

**Tactic:** Discovery

**Definition:** Adversaries may enumerate files and directories or may search in specific locations of a host or network share for certain information within a file system or directory structure. Adversaries may use the information gathered to plan follow-up actions, such as identifying executable files or sensitive data.

This post documents a practical reconnaissance exercise against DVWA using command injection to enumerate the filesystem and identify critical directories, configuration files, and potential attack surfaces.

## Context

The exercise exploited DVWA's command injection vulnerability to systematically discover:

- Application structure and web root organization
- Sensitive configuration directories (/etc)
- Database locations
- Writable directories for persistence
- User home directories
- Temporary storage locations
- Backup and archive files
- Application source code paths

## Key Findings Summary

| Finding | Location | Risk Level | Significance |
|---------|----------|-----------|---------------|
| Application root | `/var/www/html/` | High | Web application entry point |
| Configuration files | `/var/www/html/config/` | Critical | Database credentials, API keys |
| Vulnerability modules | `/var/www/html/vulnerabilities/` | High | Exploitation vectors |
| Writable upload dir | `/var/www/html/dvwa/uploads/` | Critical | File upload and persistence |
| System config | `/etc/` | High | OS-level security settings |
| Database location | MySQL (networked) | High | Data exfiltration target |
| Temp directory | `/tmp/` | Medium | Temporary file storage, staging area |

## Technical Indicators

**Vulnerability Type:** Command Injection (DVWA /vulnerabilities/exec/ endpoint)

**Attack Vector:** Unsanitized user input to system command execution

**Example Payload:** `127.0.0.1; ls -la /`

**Execution Context:** www-data user (UID 33)

**Operating System:** Linux (kernel visible in /proc)

## MITRE ATT&CK Mapping

| Aspect | Value |
|--------|-------|
| Technique | T1083 — File and Directory Discovery |
| Tactic | Discovery |
| Platforms | Linux |
| Execution Method | Command Injection |
| Detection Difficulty | Medium (command history, process monitoring) |
| Mitigation Priority | High (input validation, principle of least privilege) |

## Operational Impact

1. **Reconnaissance Efficiency** — Single command injection point yields entire filesystem visibility
2. **Privilege Assessment** — www-data user reveals limited privilege model (no root access)
3. **Data Location Mapping** — Critical files identified for targeted exfiltration
4. **Persistence Planning** — Writable directories identified for malware staging
5. **Lateral Movement** — Database network access identified; credentials not exposed at command level

## Defensive Implications

Organizations should:

- **Monitor filesystem access patterns** — Repeated ls/find commands may indicate active reconnaissance
- **Restrict command execution** — Disable or sandbox command injection points
- **Apply principle of least privilege** — Limit www-data permissions to required directories only
- **Implement file integrity monitoring** — Detect unauthorized directory enumerations
- **Use security controls** — SELinux or AppArmor to restrict file access by web processes

## References

- MITRE ATT&CK: [T1083 File and Directory Discovery](https://attack.mitre.org/techniques/T1083/)
- DVWA GitHub: https://github.com/digininja/DVWA
- Command Injection Detection: https://owasp.org/www-community/attacks/Command_Injection

---

**Exercise Date:** 2026-03-05  
**Lab Environment:** DVWA on Docker  
**Vulnerability Level:** Low (deliberate exposure for training)
