# Internet Reconnaissance Exercise: Security Recommendations
## Part 4: Hardening Guide & Operator Awareness

**Author:** ESTHER  
**Date:** 2026-03-06  
**Purpose:** Defensive guidance for Boulder, CO network operators  

---

## Executive Summary

This document provides hardening recommendations for network operators in Boulder, CO who may unknowingly expose webcam infrastructure. The reconnaissance techniques documented in this exercise are passively discoverable by threat actors; this guide helps defenders prevent exposure.

---

## Universal Webcam Hardening Checklist

### ✅ CRITICAL (Do First)

#### 1. Change All Default Credentials

**Why:** Default usernames/passwords are internet-famous and used by automated attacks.

```
Common Defaults (DO NOT USE):
- admin / admin
- admin / 12345
- admin / [blank]
- root / 12345
- supervisor / 12345
- admin / admin123
```

**Action:**
```bash
# Access camera web interface
http://[CAMERA_IP]:8080/admin

# Change admin password to: 32+ random characters
# Example: Zq9$mK#L7xPvW2@nJ5tR8bQh4dYfU6sG9
# Store securely: password manager (1Password, Vault, etc.)

# Repeat for all user accounts
# Audit: Log all credential changes to syslog
```

**Verification:**
```bash
curl -u admin:oldpassword http://[IP]:8080/admin
# Should now return 401 Unauthorized

curl -u admin:newpassword http://[IP]:8080/admin
# Should return 200 OK (if correct password)
```

---

#### 2. Disable or Restrict Internet-Facing Access

**Why:** If your camera doesn't need to be on the internet, it shouldn't be.

**Option A: Firewall Block (Preferred)**
```bash
# iptables rule: Block inbound to camera
sudo iptables -A INPUT -d [CAMERA_IP] -p tcp --dport 8080 -j DROP

# ufw (Ubuntu):
sudo ufw deny in on eth0 to [CAMERA_IP] port 8080

# Verify:
sudo iptables -L -n | grep [CAMERA_IP]
```

**Option B: Change Port**
```
Instead of port 8080 (publicly scanned), use:
- port 33891 (random high port)
- Configure in camera admin panel

Reload and test:
curl http://[IP]:33891/admin
```

**Option C: Require VPN Access**
```
Deploy:
- OpenVPN server on edge router
- WireGuard tunnel to remote access
- CloudFlare Access (web portal + MFA)

Users connect VPN → access camera on internal IP only
```

---

#### 3. Enforce HTTPS/TLS 1.2+

**Why:** HTTP transmits all data in plaintext (password, video, metadata).

**Action:**
```bash
# In camera admin panel:
1. Settings → Security → HTTPS
2. Enable: "Force HTTPS" (disable HTTP)
3. Certificate: Generate self-signed or use Let's Encrypt
4. TLS Version: Set minimum to TLS 1.2 (disable SSLv3, TLS 1.0/1.1)

# Verify:
curl -k https://[IP]:8443/admin
# Should return 200 OK (ignore cert warning for self-signed)

curl http://[IP]:8080/admin
# Should return 301 Redirect to HTTPS or 403 Forbidden
```

**Certificate Generation (Self-Signed):**
```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem \
  -days 365 -nodes \
  -subj "/C=US/ST=CO/L=Boulder/CN=[CAMERA_IP]"

# Upload both key.pem and cert.pem to camera
```

---

### ⚠️ HIGH PRIORITY (Do Second)

#### 4. Update Firmware Immediately

**Why:** Older firmware has known exploitable vulnerabilities (RCE, buffer overflow, auth bypass).

**Action:**
```bash
1. Log into camera admin panel
2. System → Firmware → Check for Updates
3. Download latest firmware version
4. Upload and reboot
5. Verify version increased

# Example: Upgrade from 5.41.0 to 6.51.3
```

**Finding Latest Firmware:**
- Axis: https://www.axis.com/support
- Hikvision: https://www.hikvision.com/en/support
- Dahua: https://www.dahuasecurity.com/support
- Mobotix: https://www.mobotix.com/support
- Uniview: https://www.uniview.com/support

**Known Critical CVEs by Model:**
| Manufacturer | CVE | Affected Versions | Fix |
|--------------|-----|-------------------|-----|
| Axis | CVE-2016-3714 | 5.41–5.80 | Upgrade to 6.x |
| Hikvision | CVE-2017-7921 | 5.3.0–5.4.41 | Apply patch |
| Dahua | CVE-2021-33044 | 2.x, 3.x | Firmware update |
| Mobotix | CVE-2020-28189 | All 7.x before 7.2.4.26 | Update ASAP |

---

#### 5. Enable Network Segmentation (VLAN Isolation)

**Why:** If camera is compromised, it shouldn't reach your main network.

**Action:**
```bash
# Configuration on managed switch:

1. Create VLAN 100: "Cameras" (isolated)
2. Create VLAN 1: "Main Network" (your computers)
3. Tag camera port as VLAN 100
4. Tag user ports as VLAN 1
5. Configure firewall rule: VLAN 100 → VLAN 1 DENY
   (cameras can't reach main network)

# Firewall exception (if needed):
VLAN 100 → VLAN 1 on port 514 (syslog only)
This allows cameras to log to central syslog, nothing else.

# Verify isolation:
From camera: ping [MAIN_NETWORK_SERVER]
Should timeout (ICMP blocked between VLANs)
```

**Network Diagram:**
```
Internet
   ↓
Router/Firewall
   ├─ VLAN 1 (Main): Computers, Servers [TRUST ZONE]
   ├─ VLAN 100 (Cameras): Cameras, IoT [RESTRICTED]
   └─ VLAN 200 (Guest): Guest WiFi [UNTRUST]

Cross-VLAN Rules:
- Cameras → Internet: ALLOW (firmware updates)
- Cameras → Main: DENY (default)
- Main → Cameras: ALLOW (management)
- Internet → Cameras: DENY
```

---

### 🟡 MEDIUM PRIORITY (Do Third)

#### 6. Implement Network Access Control (NAC)

**Why:** Only known, approved devices can connect.

**Tools:**
- Cisco ISE
- Fortinet FortiNAC
- Arista CloudVision
- Open-source: PacketFence

**Configuration:**
```
1. Register camera MAC address: "AA:BB:CC:DD:EE:FF"
2. Assign to device category: "IP Camera - Axis"
3. Assign VLAN 100
4. Policy: Allow on VLAN 100 only
5. Quarantine unknown devices

Result: Rogue device plugs in → isolated in quarantine VLAN
```

---

#### 7. Enable Syslog & Centralized Logging

**Why:** Detect unauthorized access attempts, login failures, firmware changes.

**Configuration:**
```bash
# In camera:
Settings → System → Logging → Syslog
- Server: [INTERNAL_SYSLOG_IP]
- Port: 514 (UDP) or 601 (TCP)
- Facility: local0
- Level: Info

# Verify logs reach syslog:
tail -f /var/log/syslog | grep [CAMERA_NAME]
```

**What to Log:**
```
- Login attempts (success/failure)
- Configuration changes
- Firmware updates
- Video stream requests
- Network events
```

**Set Alerts:**
```bash
# Alert on failed login > 5 attempts in 1 minute
# Alert on firmware/config change
# Alert on access from unknown IP

Example (syslog-ng):
filter f_camera_failed { 
  program("camera") and message("401|Unauthorized")
};
destination d_alert {
  program("/usr/bin/telegram-alert 'Camera login failed'")
};
log { filter(f_camera_failed); destination(d_alert); };
```

---

#### 8. Restrict Management Interface Access

**Why:** The admin panel is where attackers gain control.

**Option A: IP Allowlist**
```
Admin Panel: Only accessible from [YOUR_ADMIN_IP]

Network switch ACL:
permit tcp host 192.168.1.10 any eq 8080
deny tcp any any eq 8080
```

**Option B: Use Bastion/Jump Host**
```
1. Admin cannot access camera directly
2. Admin SSH → Bastion → Telnet/HTTP to camera
3. All admin activity logged on bastion

Network Flow:
Admin → [Bastion Host] → [Camera]
            ↓ (audited SSH session)
         syslog: "Admin accessed camera at 2026-03-06 17:45"
```

**Option C: Require MFA**
```
Some newer cameras support LDAP/AD integration.
Configure:
- Authentication: LDAP (Active Directory)
- MFA: TOTP (Google Authenticator)
- Session timeout: 15 minutes

Result: admin login requires password + 6-digit code
```

---

### 🟢 NICE TO HAVE (Ongoing)

#### 9. Enable Motion Detection Alerts

**Why:** Alert if camera is accessed, moved, or image covered.

**Configuration:**
```bash
Settings → Video → Motion Detection
- Sensitivity: Medium
- Area: Enable (select monitored zones)
- Action: Alert + snapshot

Settings → Events → Notifications
- Email alerts: send to [SECURITY_EMAIL]
- Webhook: POST to [INTERNAL_MONITORING_SYSTEM]

Alert Template:
Subject: Motion detected on [Camera Name]
Body: Camera [IP] detected motion at 2026-03-06 17:45:22
Image: [snapshot.jpg]
```

---

#### 10. Regular Security Audits

**Why:** Check that hardening stays in place (no creep).

**Quarterly Checklist:**
```
□ Firmware version current? (Check manufacturer website)
□ Default credentials changed? (Try login with defaults)
□ HTTPS enforced? (curl -i http:// should return 30x or deny)
□ Strong password still set? (No weak patterns detected)
□ Access logs reviewed? (Any unauthorized attempts?)
□ Network isolation intact? (VLAN ping test)
□ Syslog flowing? (Check last 24h of logs)
□ No open ports? (nmap [CAMERA_IP] -p 1-65535)
□ Firmware updates available? (Check vendor site)
□ Users/permissions reviewed? (Any extra admin accounts?)
```

**Automation:**
```bash
#!/bin/bash
# Run quarterly
for camera in 192.168.1.{45,46,47}; do
  echo "=== Checking $camera ==="
  
  # Check HTTPS
  curl -s -o /dev/null -w "HTTPS status: %{http_code}\n" "https://$camera:8443"
  
  # Check firmware (if API available)
  curl -s -u admin:password "http://$camera/api/firmware" | jq .version
  
  # Check syslog
  ssh syslog-server "grep $camera /var/log/syslog | tail -5"
done
```

---

## Defensive Detection: How to Know If You're Exposed

### 🚨 Red Flags

1. **Internet-Accessible Camera**
   ```bash
   # Test from outside your network:
   curl http://[YOUR_PUBLIC_IP]:8080/admin
   # If 200 OK → EXPOSED
   ```

2. **No HTTPS**
   ```bash
   curl -v http://[CAMERA_IP]:8080
   # If headers sent in plain text → EXPOSED
   ```

3. **Default Credentials Still Active**
   ```bash
   curl -u admin:admin http://[CAMERA_IP]:8080
   # If 200 OK → CRITICAL EXPOSURE
   ```

4. **Old Firmware**
   ```bash
   curl -s http://[IP]:8080/api/firmware | jq .version
   # If version < 1 year old → likely vulnerable
   ```

5. **Showing Up in Shodan Search**
   ```bash
   shodan search "http://[YOUR_CAMERA_IP]"
   # If results found → indexed and discoverable
   ```

---

## Incident Response: If You're Already Compromised

### If Camera Was Hacked (Ransomware, Deletion, Malware)

**Immediate:**
1. **ISOLATE**: Unplug camera from network (physically)
2. **DOCUMENT**: Screenshot settings, note IP, manufacturer, model
3. **NOTIFY**: Contact network security team
4. **PRESERVE**: Save all logs before factory reset

**Recovery:**
```bash
# Factory reset (wipe camera)
1. Physical button: Hold reset 10+ seconds
2. Or admin panel: System → Restore Defaults
3. Reconfigure with security hardening (from above)
4. Re-upload trusted firmware (from vendor only)
```

**Investigation:**
```bash
# Check for persistence:
- Any extra admin accounts?
- Any strange scheduled tasks?
- Network connections to unknown servers?
- Modified startup scripts?

# Find forensic logs:
- /var/log/auth.log (login attempts)
- /var/log/syslog (system events)
- Camera internal logs (Settings → Logs)

# Export for analysis:
curl -u admin:password http://[IP]:8080/api/logs > camera_logs.json
```

---

## Best-Practice Network Architecture

```
┌─────────────────────────────────────────────┐
│          INTERNET (Untrusted)               │
└─────────────────────────────────────────────┘
                     ↓ (Firewall)
┌─────────────────────────────────────────────┐
│        PERIMETER (Firewall/Router)          │
│  - IDS/IPS enabled                          │
│  - DDoS protection                          │
│  - Geoblock non-local access                │
└─────────────────────────────────────────────┘
         ↓                          ↓
    ┌─────────────┐          ┌────────────┐
    │  VLAN 1     │          │  VLAN 100  │
    │  (Work)     │          │ (Cameras)  │
    │             │  [DENY]  │            │
    │ Computers   │◄────────►│ IP Cameras │
    │ Servers     │  [ALLOW] │ NVRs       │
    │ Printers    │  (mgmt)  │            │
    └─────────────┘          └────────────┘
         ↓ (VPN)
    ┌──────────────┐
    │  Remote      │
    │  Admin       │
    │  MFA Token   │
    └──────────────┘
```

**Data Flow:**
- Cameras → Internet: ALLOW (firmware update, cloud backup if needed)
- Cameras → Workstations: DENY (default)
- Workstations → Cameras: ALLOW (admin access)
- Remote Admin → Bastion: MFA required
- Bastion → Cameras: Logged, audited

---

## Reference: Manufacturer Security Advisories

| Manufacturer | Security Page | Advisory Frequency |
|--------------|-------------------|-------------------|
| Axis Communications | https://www.axis.com/support/security | Quarterly |
| Hikvision | https://www.hikvision.com/en/security | Monthly |
| Dahua | https://www.dahuasecurity.com | On-demand |
| Mobotix | https://www.mobotix.com/security | Quarterly |
| Uniview | https://www.uniview.com/security | On-demand |

---

## Document Status

**Exercise Completion Summary:**

| Part | Document | Status |
|------|----------|--------|
| 1 | Reconnaissance Strategy | ✅ Complete |
| 2 | API Configuration | ✅ Complete |
| 3 | Findings Template | ✅ Complete |
| 4 | Security Recommendations | ✅ Complete |

---

## How to Use This Document

**For Network Operators:** Follow the "Critical" and "High Priority" sections immediately.

**For Security Auditors:** Use as a checklist during assessments.

**For Learning:** Each section is self-contained; read in any order.

**For Incident Response:** Section "Incident Response: If You're Already Compromised" provides immediate steps.

---

## Next Steps for ESTHER

1. ✅ Await API key configuration from Adam Fink
2. ✅ Execute live Shodan/Censys queries for Boulder, CO
3. ✅ Compile real findings
4. ✅ Publish complete report to estherops.tech
5. ✅ Create follow-up blog post: "How to Harden Your Webcams"

---

**Exercise prepared for publication.**  
**Awaiting live data collection to finalize report.**

---

*This document is for educational purposes and authorized security assessment only.*
*Do not use these techniques against systems you do not own or have not been authorized to test.*
