# Juice Shop SQL Injection (CWE-89) — Intelligence Report

## Vulnerability Overview

**Type:** SQL Injection (CWE-89)  
**CVSS Score:** 9.8 (Critical)  
**MITRE ATT&CK:** T1190 (Exploit Public-Facing Application)  
**CWE:** CWE-89 (SQL Injection)  
**OWASP Top 10:** A03:2021 – Injection  

## Affected Endpoint

- **Path:** `/rest/user/login`
- **Method:** POST
- **Content-Type:** application/json
- **Vulnerability:** Authentication Bypass via SQL Injection

## Technical Details

### Vulnerability Chain

The Juice Shop login endpoint accepts a JSON payload with email and password fields. The email field is concatenated directly into a SQL query without parameterization, allowing an attacker to inject SQL commands.

**Vulnerable Code Pattern:**
```sql
SELECT * FROM users WHERE email = '<USER_INPUT>' AND password = '<PASSWORD>'
```

### Attack Vector

By injecting a SQL comment sequence (`--`), an attacker can:
1. Close the email string with a single quote (`'`)
2. Inject arbitrary SQL logic (`OR 1=1`)
3. Comment out the password check (`--`)

This transforms the query to:
```sql
SELECT * FROM users WHERE email = 'admin@juice-sh.op' OR 1=1--' AND password = 'anything'
```

The `OR 1=1` clause always evaluates to true, and the `--` comments out the password validation, allowing authentication bypass.

### Impact

- **Authentication Bypass:** Attacker gains admin-level access without valid credentials
- **Data Exfiltration:** Access to user account data (emails, hashes, personal info)
- **Privilege Escalation:** Admin account grants full application control
- **Lateral Movement:** Compromised admin account can create new backdoor accounts

## Proof of Concept

### Payload

```json
{
  "email": "admin@juice-sh.op' OR 1=1--",
  "password": "admin"
}
```

### Result

Authentication succeeds and returns a valid JWT token for the admin user.

**Extracted Admin User Data:**
```
User ID: 1
Email: admin@juice-sh.op
Role: admin
Status: active
```

## MITRE Mapping

| MITRE Technique | Description |
|-----------------|-------------|
| T1190 (Exploit Public-Facing Application) | SQL injection in web login endpoint |
| T1078 (Valid Accounts) | Authentication bypass grants legitimate admin account access |
| T1087 (Account Discovery) | Enumerates valid user accounts (admin exists) |

## Remediation

1. **Use Parameterized Queries:** Replace string concatenation with prepared statements
2. **Input Validation:** Validate email format and reject SQL metacharacters
3. **Stored Procedures:** Use database-level parameterization
4. **WAF Rules:** Deploy Web Application Firewall rules to detect/block SQL injection patterns
5. **Rate Limiting:** Implement failed login attempt throttling

## Detection Signatures

### WAF Pattern
```
Detects: ' OR ', ' AND ', --, /*, */, ';', UNION, SELECT, DROP
```

### Log Indicators
- Multiple failed login attempts from same IP
- Login with malformed email addresses (contains SQL keywords)
- Successful admin login without prior known credential change

---

**Report Date:** 2026-03-09  
**Analyst:** ESTHER  
**Status:** VERIFIED ✓
