#!/usr/bin/env python3
"""
esther-verify.py — ESTHER System Verification Tool
Interactive menu to verify all Fink Security / ESTHER components.

Deploy to: ~/esther-lab/scripts/esther-verify.py
Run with:  python3 ~/esther-lab/scripts/esther-verify.py

Also commit to FinkSecurity/esther-lab as the canonical verification reference.
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path

# ── Colours ────────────────────────────────────────────────────────────────────
R  = '\033[91m'   # red
G  = '\033[92m'   # green
Y  = '\033[93m'   # yellow
C  = '\033[96m'   # cyan
B  = '\033[1m'    # bold
DIM = '\033[2m'   # dim
RST = '\033[0m'   # reset

def ok(msg):   print(f"  {G}✅ {msg}{RST}")
def fail(msg): print(f"  {R}❌ {msg}{RST}")
def warn(msg): print(f"  {Y}⚠️  {msg}{RST}")
def info(msg): print(f"  {C}ℹ️  {msg}{RST}")
def head(msg): print(f"\n{B}{C}{'━'*54}\n  {msg}\n{'━'*54}{RST}")

def run(cmd: str, timeout=15) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, '', '(timeout)'
    except Exception as e:
        return -1, '', str(e)

# ── Paths ──────────────────────────────────────────────────────────────────────
HOME        = Path.home()
LAB         = HOME / 'esther-lab'
WORKSPACE   = HOME / '.openclaw' / 'workspace'
SCRIPTS     = WORKSPACE / 'scripts'
ENGAGEMENTS = LAB / 'engagements' / 'public'
OLD_FINDINGS = LAB / 'findings'          # legacy — should be empty eventually
NOTIFY_DIR  = HOME / 'finksecurity-notify'

TOOLS = [
    'nmap', 'theHarvester', 'nikto', 'nuclei', 'ffuf', 'amass',
    'aws', 'az', 'gcloud',
    'sqlmap', 'wfuzz', 'john', 'hashcat',
    'crackmapexec', 'msfconsole', 'hydra',
]

# Tools with non-standard paths checked separately
TOOLS_NONSTANDARD = [
    ('scout (ScoutSuite)', [
        Path.home() / '.local/bin/scout',
        Path('/usr/local/bin/scout'),
    ]),
    ('impacket', [
        Path('/usr/share/impacket'),
        Path('/usr/lib/python3/dist-packages/impacket'),
    ]),
]

SCRIPTS_EXPECTED = [
    WORKSPACE / 'scripts' / 'generate-briefing.py',
    WORKSPACE / 'scripts' / 'load-scope.py',
    WORKSPACE / 'scripts' / 'generate-h1-report.py',
    WORKSPACE / 'scripts' / 'generate-report.py',
    WORKSPACE / 'scripts' / 'update-stats.py',
    LAB / 'scripts' / 'hackerone-scope-fetch.py',
    LAB / 'scripts' / 'esther-verify.py',
]

DOCKER_EXPECTED = [
    'opensearch', 'opensearch-dashboards',
    'dvwa', 'juice-shop', 'portainer', 'ollama'
]

SOUL_PATH        = LAB / 'SOUL.md'
BRIEF_PATH       = WORKSPACE / 'MISSION-BRIEF.md'
ACTIVE_ENG_PATH  = WORKSPACE / 'ACTIVE-ENGAGEMENT.md'
SCOPE_CACHE_PATH = WORKSPACE / 'SCOPE-CACHE.json'


# ════════════════════════════════════════════════════════════════════════════════
# 1 — GIT COMMITS
# ════════════════════════════════════════════════════════════════════════════════

def verify_commits():
    head("GIT COMMIT VERIFICATION")

    # Static paths always checked
    static_checks = [
        ("posts",    "posts"),
        ("scripts",  "scripts"),
    ]

    # Dynamic — detect all programs under engagements/public/
    engagement_checks = []
    if ENGAGEMENTS.exists():
        for prog in sorted(ENGAGEMENTS.iterdir()):
            if prog.is_dir():
                engagement_checks += [
                    (f"{prog.name}/findings",     f"engagements/public/{prog.name}/findings"),
                    (f"{prog.name}/scope",        f"engagements/public/{prog.name}/scope.md"),
                    (f"{prog.name}/submissions",  f"engagements/public/{prog.name}/submissions"),
                ]

    all_checks = engagement_checks + static_checks

    print(f"\n  {DIM}Checking FinkSecurity/esther-lab recent commits per path...{RST}\n")
    print(f"  {DIM}Programs detected: {', '.join(p.name for p in ENGAGEMENTS.iterdir() if p.is_dir()) if ENGAGEMENTS.exists() else 'none'}{RST}\n")

    for label, path in all_checks:
        code, out, err = run(
            f"gh api 'repos/FinkSecurity/esther-lab/commits?path={path}&per_page=3' "
            f"--jq '.[] | \"  \" + .sha[:9] + \"  \" + .commit.author.date[:10] + "
            f"\"  \" + (.commit.message | split(\"\\n\")[0][:60])'",
            timeout=20
        )
        print(f"  {B}{label.upper()} ({path}){RST}")
        if code == 0 and out:
            for line in out.splitlines():
                print(f"  {G}{line}{RST}")
        elif 'timeout' in err:
            warn(f"gh api timed out for {path}")
        else:
            warn(f"No commits found or gh api error: {err[:80]}")
        print()

    # Structure checks
    print(f"  {B}STRUCTURE CHECK{RST}")
    if OLD_FINDINGS.exists() and any(OLD_FINDINGS.iterdir()):
        warn(f"Legacy findings/ directory still has content: {OLD_FINDINGS}")
        warn("These are duplicated in engagements/public/. Consider cleaning up.")
    else:
        ok("No duplicate findings/ — engagements/public/ is canonical")

    nested = LAB / 'esther-lab'
    if nested.exists():
        warn(f"Nested esther-lab/esther-lab/ directory exists — likely accidental")
    else:
        ok("No nested esther-lab/ directory")


# ════════════════════════════════════════════════════════════════════════════════
# 2 — H1 SUBMISSION DRAFTS
# ════════════════════════════════════════════════════════════════════════════════

def verify_h1_drafts():
    head("H1 SUBMISSION DRAFT VERIFICATION")

    submissions_root = ENGAGEMENTS
    found_any = False

    for program_dir in sorted(submissions_root.iterdir()):
        if not program_dir.is_dir():
            continue
        sub_dir = program_dir / 'submissions'
        if not sub_dir.exists():
            info(f"{program_dir.name}: no submissions/ directory yet")
            continue

        drafts   = sorted(sub_dir.glob('DRAFT-*.md'))
        summary  = sub_dir / 'FINDINGS-SUMMARY.md'
        found_any = True

        print(f"\n  {B}{program_dir.name.upper()}{RST}  ({sub_dir})")

        if summary.exists():
            age_h = (datetime.now(timezone.utc).timestamp() - summary.stat().st_mtime) / 3600
            ok(f"FINDINGS-SUMMARY.md exists — last modified {age_h:.1f}h ago")
        else:
            warn("FINDINGS-SUMMARY.md missing — run generate-h1-report.py")

        if not drafts:
            info("No DRAFT-*.md files — either no reportable findings or report not yet generated")
        else:
            print(f"  {G}  {len(drafts)} draft(s) found:{RST}")
            for d in drafts:
                # Check if Steps to Reproduce placeholder is still present
                content = d.read_text()
                has_placeholder = '_(describe the exact request' in content or \
                                  'OPERATOR REVIEW REQUIRED' in content
                status = f"{Y}⚠️  needs Operator review{RST}" if has_placeholder \
                         else f"{G}✅ review complete{RST}"
                print(f"    {DIM}{d.name}{RST}  →  {status}")

    if not found_any:
        warn("No engagement submissions found. Run generate-h1-report.py after nuclei scans.")


# ════════════════════════════════════════════════════════════════════════════════
# 3 — NOTIFY RELAY + TELEGRAM
# ════════════════════════════════════════════════════════════════════════════════

def verify_notify():
    head("NOTIFY RELAY + TELEGRAM PIPELINE")

    # Check gunicorn process
    code, out, _ = run("ps aux | grep 'gunicorn.*notify' | grep -v grep")
    if code == 0 and out:
        ok(f"gunicorn process running: {out.split()[1]} (PID)")
    else:
        fail("gunicorn notify process not found — relay may be down")
        info("Restart: cd ~/finksecurity-notify && gunicorn -b 0.0.0.0:5001 notify:app --daemon")

    # Check port 5001 locally
    code, out, _ = run("ss -tlnp | grep :5001")
    if code == 0 and out:
        ok("Port 5001 is listening")
    else:
        fail("Nothing listening on port 5001")

    # Check HTTPS endpoint
    print(f"\n  {DIM}Testing https://api.finksecurity.com/notify ...{RST}")
    code, out, err = run(
        "curl -s -o /dev/null -w '%{http_code}|%{ssl_verify_result}|%{time_total}' "
        "-X POST https://api.finksecurity.com/notify "
        "-H 'Content-Type: application/json' "
        "-d '{\"first_name\":\"Verify\",\"last_name\":\"Check\","
        "\"email\":\"verify@finksecurity.com\",\"service\":\"Test\","
        "\"authorization_confirmed\":true}'",
        timeout=15
    )
    if code == 0 and out:
        parts = out.split('|')
        http_code = parts[0] if parts else '000'
        ssl_ok    = parts[1] == '0' if len(parts) > 1 else False
        latency   = parts[2] if len(parts) > 2 else '?'
        if http_code == '200':
            ok(f"HTTPS endpoint returned 200 in {latency}s")
            ok("SSL verification passed" if ssl_ok else "SSL not verified (check cert)")
            info("Check Telegram — a test notification should have arrived")
        else:
            fail(f"HTTPS endpoint returned {http_code} — check nginx and gunicorn")
    else:
        fail(f"curl failed: {err[:80]}")

    # Check SSL cert expiry
    print(f"\n  {DIM}Checking SSL cert expiry for api.finksecurity.com ...{RST}")
    code, out, _ = run(
        "echo | openssl s_client -connect api.finksecurity.com:443 -servername api.finksecurity.com 2>/dev/null "
        "| openssl x509 -noout -enddate 2>/dev/null"
    )
    if code == 0 and 'notAfter' in out:
        expiry_str = out.split('=')[-1].strip()
        ok(f"SSL cert expires: {expiry_str}")
    else:
        warn("Could not retrieve SSL cert expiry — check manually")

    # Check nginx
    code, _, _ = run("sudo nginx -t 2>/dev/null")
    if code == 0:
        ok("nginx config syntax OK")
    else:
        warn("nginx -t returned non-zero — check config")


# ════════════════════════════════════════════════════════════════════════════════
# 4 — SCOPE FILES
# ════════════════════════════════════════════════════════════════════════════════

def verify_scope():
    head("SCOPE FILE VERIFICATION")

    if not ENGAGEMENTS.exists():
        fail(f"Engagements directory not found: {ENGAGEMENTS}")
        return

    for program_dir in sorted(ENGAGEMENTS.iterdir()):
        if not program_dir.is_dir():
            continue

        scope_file = program_dir / 'scope.md'
        print(f"\n  {B}{program_dir.name.upper()}{RST}")

        if not scope_file.exists():
            fail(f"scope.md missing — run: python3 ~/esther-lab/scripts/hackerone-scope-fetch.py {program_dir.name}")
            continue

        content  = scope_file.read_text()
        age_h    = (datetime.now(timezone.utc).timestamp() - scope_file.stat().st_mtime) / 3600
        age_days = age_h / 24

        # Check if auto-generated
        is_autogen = 'AUTO-GENERATED by hackerone-scope-fetch.py' in content
        if is_autogen:
            ok("Auto-generated scope (hackerone-scope-fetch.py)")
        else:
            warn("Manually written scope — consider migrating to auto-fetch")

        # Staleness check
        if age_days > 7:
            warn(f"Scope is {age_days:.0f} days old — consider refreshing from H1 API")
        else:
            ok(f"Scope last updated {age_h:.1f}h ago")

        # Count in-scope assets
        in_scope_count  = content.count('\n- `')
        oos_section     = '## OUT OF SCOPE' in content
        ok(f"~{in_scope_count} asset entries found")

        if oos_section:
            ok("Out-of-scope section present")
        else:
            warn("No OUT OF SCOPE section — add one")

        # Check SCOPE-CACHE.json
        if SCOPE_CACHE_PATH.exists():
            try:
                cache = json.loads(SCOPE_CACHE_PATH.read_text())
                loaded_program = cache.get('handle', '')
                loaded_at      = cache.get('loaded_at', '')[:16]
                if loaded_program == program_dir.name:
                    ok(f"SCOPE-CACHE.json loaded for {loaded_program} at {loaded_at}")
                else:
                    warn(f"SCOPE-CACHE.json is for '{loaded_program}', not '{program_dir.name}' — reload needed")
            except json.JSONDecodeError:
                warn("SCOPE-CACHE.json is malformed")
        else:
            warn(f"SCOPE-CACHE.json missing — run: python3 {SCRIPTS}/load-scope.py {program_dir.name}")


# ════════════════════════════════════════════════════════════════════════════════
# 5 — TOOL INVENTORY
# ════════════════════════════════════════════════════════════════════════════════

def verify_tools():
    head("TOOL INVENTORY")

    present = []
    missing = []

    for tool in TOOLS:
        path = shutil.which(tool)
        if path:
            present.append((tool, path))
        else:
            missing.append(tool)

    # Check non-standard path tools
    for label, paths in TOOLS_NONSTANDARD:
        found = next((p for p in paths if p.exists()), None)
        if found:
            present.append((label, str(found)))
        else:
            missing.append(label)

    total = len(TOOLS) + len(TOOLS_NONSTANDARD)
    print(f"\n  {G}Present ({len(present)}/{total}):{RST}")
    for tool, path in present:
        print(f"    {G}✅ {tool:<25}{RST}  {DIM}{path}{RST}")

    if missing:
        print(f"\n  {R}Missing ({len(missing)}):{RST}")
        for tool in missing:
            print(f"    {R}❌ {tool}{RST}")
    else:
        print(f"\n  {G}All {total} tools present ✅{RST}")


# ════════════════════════════════════════════════════════════════════════════════
# 6 — NGINX + SSL
# ════════════════════════════════════════════════════════════════════════════════

def verify_nginx():
    head("NGINX + SSL VERIFICATION")

    # nginx running?
    code, out, _ = run("systemctl is-active nginx")
    if out.strip() == 'active':
        ok("nginx is active")
    else:
        fail(f"nginx status: {out or 'unknown'}")

    # Config test
    code, out, err = run("sudo nginx -t 2>&1")
    combined = (out + err).lower()
    if 'syntax is ok' in combined and 'successful' in combined:
        ok("nginx config syntax OK")
    else:
        fail(f"nginx config error: {(out + err)[:120]}")

    # Port 80 and 443
    for port, label in [('80', 'HTTP'), ('443', 'HTTPS')]:
        code, out, _ = run(f"ss -tlnp | grep :{port}")
        if code == 0 and out:
            proc = 'nginx' if 'nginx' in out else out.split('(')[-1].split(',')[0]
            ok(f"Port {port} ({label}) listening — {proc}")
        else:
            fail(f"Port {port} ({label}) not listening")

    # Confirm sshd is NOT on 443 (the Day 10 bug)
    code, out, _ = run("ss -tlnp | grep :443")
    if 'sshd' in out:
        fail("sshd is bound to port 443 — this breaks HTTPS! See Day 10 fix notes.")
    else:
        ok("sshd not on port 443")

    # api.finksecurity.com resolves to correct IP
    code, out, _ = run("dig +short api.finksecurity.com")
    if '45.82.72.151' in out:
        ok(f"DNS: api.finksecurity.com → 45.82.72.151")
    else:
        warn(f"DNS returned: {out or 'no result'} (expected 45.82.72.151)")


# ════════════════════════════════════════════════════════════════════════════════
# 7 — DOCKER STACK
# ════════════════════════════════════════════════════════════════════════════════

def verify_docker():
    head("DOCKER STACK VERIFICATION")

    code, out, err = run("docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}'")
    if code != 0:
        fail(f"docker ps failed: {err[:80]}")
        return

    running = {}
    for line in out.splitlines():
        parts = line.split('|')
        if len(parts) >= 2:
            name   = parts[0].strip()
            status = parts[1].strip()
            ports  = parts[2].strip() if len(parts) > 2 else ''
            running[name] = (status, ports)

    print()
    matched = set()
    for expected in DOCKER_EXPECTED:
        # fuzzy match — container names may have prefixes
        match = next((k for k in running if expected in k and k not in matched), None)
        if match:
            matched.add(match)
            status, ports = running[match]
            if 'Up' in status:
                ok(f"{match:<35} {DIM}{status}{RST}")
            else:
                warn(f"{match:<35} {Y}{status}{RST}")
        else:
            fail(f"{expected:<35} not running")

    # Show any unexpected containers
    unexpected = [k for k in running if not any(e in k for e in DOCKER_EXPECTED)]
    if unexpected:
        print()
        info(f"Additional containers running: {', '.join(unexpected)}")


# ════════════════════════════════════════════════════════════════════════════════
# 8 — SCRIPTS INVENTORY
# ════════════════════════════════════════════════════════════════════════════════

def verify_scripts():
    head("SCRIPTS INVENTORY")

    print()
    for script in SCRIPTS_EXPECTED:
        if script.exists():
            age_h = (datetime.now(timezone.utc).timestamp() - script.stat().st_mtime) / 3600
            ok(f"{script.name:<35} {DIM}(modified {age_h:.0f}h ago){RST}")
        else:
            fail(f"{script.name:<35} NOT FOUND at {script}")


# ════════════════════════════════════════════════════════════════════════════════
# 9 — MISSION BRIEF FRESHNESS
# ════════════════════════════════════════════════════════════════════════════════

def verify_brief():
    head("MISSION BRIEF + ENGAGEMENT CONTEXT")

    for label, path in [
        ("MISSION-BRIEF.md",       BRIEF_PATH),
        ("ACTIVE-ENGAGEMENT.md",   ACTIVE_ENG_PATH),
        ("SCOPE-CACHE.json",       SCOPE_CACHE_PATH),
        ("SOUL.md",                SOUL_PATH),
    ]:
        if not path.exists():
            fail(f"{label} missing at {path}")
            continue

        age_h    = (datetime.now(timezone.utc).timestamp() - path.stat().st_mtime) / 3600
        age_days = age_h / 24

        if label == 'MISSION-BRIEF.md' and age_h > 24:
            warn(f"{label} is {age_days:.1f} days old — regenerate: python3 {SCRIPTS}/generate-briefing.py")
        elif label == 'ACTIVE-ENGAGEMENT.md' and age_h > 48:
            warn(f"{label} is {age_days:.1f} days old — reload scope before next task")
        else:
            ok(f"{label} — last modified {age_h:.1f}h ago")


# ════════════════════════════════════════════════════════════════════════════════
# 10 — DISK SPACE
# ════════════════════════════════════════════════════════════════════════════════

def verify_disk():
    head("VPS DISK SPACE")

    code, out, _ = run("df -h / /home 2>/dev/null | tail -n +2")
    if code == 0 and out:
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                use_pct = parts[4].replace('%', '')
                mount   = parts[5] if len(parts) > 5 else parts[-1]
                try:
                    pct = int(use_pct)
                    if pct >= 90:
                        fail(f"{mount}: {pct}% used — CRITICAL, clean up scan output files")
                    elif pct >= 75:
                        warn(f"{mount}: {pct}% used — getting full")
                    else:
                        ok(f"{mount}: {pct}% used  ({parts[2]} used / {parts[1]} total)")
                except ValueError:
                    info(line)

    # Check size of findings directories
    for label, path in [
        ("engagements/public/", ENGAGEMENTS),
        ("findings/ (legacy)",  OLD_FINDINGS),
        ("logs/",               LAB / 'logs'),
    ]:
        if path.exists():
            code, out, _ = run(f"du -sh {path} 2>/dev/null")
            size = out.split()[0] if out else '?'
            info(f"{label:<30} {size}")


# ════════════════════════════════════════════════════════════════════════════════
# 11 — CRON JOBS
# ════════════════════════════════════════════════════════════════════════════════

def verify_cron():
    head("CRON JOBS")

    code, out, _ = run("crontab -l 2>/dev/null")
    if code != 0 or not out:
        warn("No crontab found for current user")
        info("Expected: daily generate-briefing.py at 08:00")
        info("Add with: crontab -e")
        info("  0 8 * * * python3 ~/.openclaw/workspace/scripts/generate-briefing.py")
        return

    print()
    lines = [l for l in out.splitlines() if l.strip() and not l.startswith('#')]
    if not lines:
        warn("Crontab exists but has no active jobs")
    else:
        for line in lines:
            print(f"  {G}✅ {line}{RST}")

    has_briefing = any('generate-briefing' in l for l in lines)
    if not has_briefing:
        warn("generate-briefing.py not in crontab — MISSION-BRIEF.md won't auto-refresh")


def verify_fabrication():
    head("SHA FABRICATION CHECK")

    print(f"\n  Paste up to 5 SHAs reported by ESTHER to verify against GitHub.")
    print(f"  Enter one per line. Empty line when done.\n")

    shas = []
    while len(shas) < 5:
        try:
            raw = input(f"  SHA {len(shas)+1} (or Enter to finish): ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not raw:
            break
        # Strip common prefixes ESTHER might include
        sha = raw.replace('SHA:', '').replace('✅','').replace('commit','').strip().split()[0]
        if sha:
            shas.append(sha)

    if not shas:
        info("No SHAs entered.")
        return

    print()
    all_real = True
    for sha in shas:
        code, out, err = run(
            f"gh api repos/FinkSecurity/esther-lab/commits/{sha} "
            f"--jq '{{sha: .sha[:9], date: .commit.author.date[:10], "
            f"message: (.commit.message | split(\"\\n\")[0][:60]), "
            f"files: (.files | length)}}'",
            timeout=20
        )
        if code == 0 and out and 'sha' in out:
            try:
                import json
                data = json.loads(out)
                ok(f"{sha} — REAL ✅")
                print(f"    {DIM}Date:    {data.get('date','?')}{RST}")
                print(f"    {DIM}Message: {data.get('message','?')}{RST}")
                print(f"    {DIM}Files:   {data.get('files','?')} changed{RST}")
            except Exception:
                ok(f"{sha} — exists (parse error, but API returned 200)")
        elif '422' in err or 'No commit found' in err or 'No commit found' in out:
            fail(f"{sha} — FABRICATED ❌  (no commit found in repo)")
            all_real = False
        elif 'timeout' in err:
            warn(f"{sha} — timeout, could not verify")
        else:
            fail(f"{sha} — FABRICATED or invalid ❌")
            all_real = False
        print()

    if all_real:
        print(f"  {G}{B}All SHAs verified real.{RST}")
    else:
        print(f"  {R}{B}One or more SHAs are fabricated. Do not trust ESTHER's report.{RST}")
        print(f"  {Y}  Send ESTHER: \"SHA <x> does not exist. Redo the work and verify before reporting.\"{RST}")


# ════════════════════════════════════════════════════════════════════════════════
# 12 — OPENCLAW PROCESS STATUS
# ════════════════════════════════════════════════════════════════════════════════

def verify_openclaw():
    head("OPENCLAW PROCESS STATUS")

    # Check for openclaw process
    code, out, _ = run("ps aux | grep -i 'openclaw\\|claude\\|anthropic' | grep -v grep")
    if code == 0 and out:
        lines = out.splitlines()
        ok(f"openclaw process(es) found: {len(lines)}")
        for line in lines:
            parts = line.split()
            pid  = parts[1] if len(parts) > 1 else '?'
            cmd  = ' '.join(parts[10:])[:80] if len(parts) > 10 else line[:80]
            print(f"    {DIM}PID {pid}: {cmd}{RST}")
    else:
        fail("No openclaw process found — ESTHER may be offline")
        info("Check your openclaw startup script and restart if needed")

    # Check workspace directory exists and is populated
    if WORKSPACE.exists():
        ok(f"Workspace directory exists: {WORKSPACE}")
        files = list(WORKSPACE.iterdir())
        info(f"{len(files)} items in workspace")
    else:
        fail(f"Workspace directory missing: {WORKSPACE}")

    # Check ENVIRONMENT.md exists and is fresh
    env_path = HOME / '.openclaw' / 'ENVIRONMENT.md'
    if env_path.exists():
        age_h = (datetime.now(timezone.utc).timestamp() - env_path.stat().st_mtime) / 3600
        ok(f"ENVIRONMENT.md present — last modified {age_h:.1f}h ago")
    else:
        fail(f"ENVIRONMENT.md missing at {env_path}")

    # Check Telegram bot token is set in environment or .env
    env_candidates = [
        HOME / '.openclaw' / '.env',
        HOME / 'finksecurity-notify' / '.env',
    ]
    token_found = False
    for env_file in env_candidates:
        if env_file.exists():
            try:
                content = env_file.read_text()
            except Exception:
                continue
            if 'TELEGRAM_BOT_TOKEN' in content and len(content.split('TELEGRAM_BOT_TOKEN')[1].strip()) > 5:
                ok(f"TELEGRAM_BOT_TOKEN present ({env_file})")
                token_found = True
                break
    if not token_found:
        warn("TELEGRAM_BOT_TOKEN not found in ~/.openclaw/.env or ~/finksecurity-notify/.env")


# ════════════════════════════════════════════════════════════════════════════════
# 13 — LATEST COMMIT VERIFICATION
# ════════════════════════════════════════════════════════════════════════════════

def verify_latest_commit():
    head("LATEST COMMIT VERIFICATION")

    print(f"\n  {DIM}Use this after ESTHER reports 'Pushed. SHA: <sha>'{RST}")
    print(f"  {DIM}Paste the SHA she reported, or press Enter to check HEAD.{RST}\n")

    try:
        raw = input(f"  SHA to verify (or Enter to use git HEAD): ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not raw:
        # Pull HEAD from local repo
        code, out, err = run(f"git -C {LAB} rev-parse HEAD")
        if code != 0 or not out:
            fail(f"Could not get HEAD from {LAB}: {err[:80]}")
            return
        sha = out.strip()
        info(f"Using local HEAD: {sha[:9]}")
    else:
        sha = raw.replace('SHA:', '').replace('Pushed.', '').strip().split()[0]

    print(f"\n  {DIM}Verifying {sha[:9]} against GitHub...{RST}\n")

    code, out, err = run(
        f"gh api repos/FinkSecurity/esther-lab/commits/{sha} "
        f"--jq '{{sha: .sha[:9], date: .commit.author.date[:10], "
        f"message: (.commit.message | split(\"\\n\")[0][:70]), "
        f"files: [.files[].filename]}}'",
        timeout=20
    )

    if code == 0 and out and 'sha' in out:
        try:
            data = json.loads(out)
            ok(f"REAL commit verified ✅")
            print(f"\n    {B}SHA:     {RST}{data.get('sha','?')}")
            print(f"    {B}Date:    {RST}{data.get('date','?')}")
            print(f"    {B}Message: {RST}{data.get('message','?')}")
            files = data.get('files', [])
            print(f"    {B}Files:   {RST}{len(files)} changed")
            for f in files:
                print(f"             {DIM}{f}{RST}")
        except Exception:
            ok(f"{sha[:9]} — exists (raw: {out[:120]})")
    elif '422' in err or 'No commit found' in err or 'No commit found' in out:
        fail(f"SHA {sha[:9]} — FABRICATED ❌  (no commit found in repo)")
        print(f"\n  {R}{B}This commit does not exist. ESTHER fabricated it.{RST}")
        print(f"  {Y}Send her: \"SHA {sha[:9]} does not exist. Do the work and push for real.\"{RST}")
    elif 'timeout' in err:
        warn(f"GitHub API timed out — try again")
    else:
        fail(f"Unexpected error: {err[:100]}")


# ════════════════════════════════════════════════════════════════════════════════
# MENU
# ════════════════════════════════════════════════════════════════════════════════

MENU_ITEMS = [
    ("Git commits (all engagements)",  verify_commits),
    ("H1 submission drafts",           verify_h1_drafts),
    ("Notify relay + Telegram",        verify_notify),
    ("Scope files",                    verify_scope),
    ("Tool inventory",                 verify_tools),
    ("nginx + SSL",                    verify_nginx),
    ("Docker stack",                   verify_docker),
    ("Scripts inventory",              verify_scripts),
    ("Mission brief freshness",        verify_brief),
    ("Disk space",                     verify_disk),
    ("Cron jobs",                      verify_cron),
    ("SHA fabrication check",          verify_fabrication),
    ("openclaw process status",        verify_openclaw),
    ("Latest commit verification",     verify_latest_commit),
    ("Run ALL checks",                 None),
]


def print_menu():
    print(f"\n{B}{C}")
    print("  ███████╗███████╗████████╗██╗  ██╗███████╗██████╗ ")
    print("  ██╔════╝██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗")
    print("  █████╗  ███████╗   ██║   ███████║█████╗  ██████╔╝")
    print("  ██╔══╝  ╚════██║   ██║   ██╔══██║██╔══╝  ██╔══██╗")
    print("  ███████╗███████║   ██║   ██║  ██║███████╗██║  ██║")
    print("  ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝")
    print(f"  {RST}{B}  Fink Security — System Verification Tool{RST}")
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"  {DIM}  {now}{RST}\n")
    print(f"{B}  Select a check to run:{RST}\n")
    for i, (label, _) in enumerate(MENU_ITEMS, 1):
        icon = '🔍' if label != 'Run ALL checks' else '🦂'
        print(f"  {C}{i:>2}.{RST}  {icon}  {label}")
    print(f"\n   {DIM}0.  Exit{RST}\n")


def main():
    while True:
        print_menu()
        try:
            choice = input(f"  {B}>{RST} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {DIM}Exiting. Stay frosty. 🦂{RST}\n")
            sys.exit(0)

        if choice == '0':
            print(f"\n  {DIM}Exiting. Stay frosty. 🦂{RST}\n")
            sys.exit(0)

        try:
            idx = int(choice) - 1
        except ValueError:
            print(f"  {R}Invalid choice.{RST}")
            continue

        if idx < 0 or idx >= len(MENU_ITEMS):
            print(f"  {R}Invalid choice.{RST}")
            continue

        label, fn = MENU_ITEMS[idx]

        if fn is None:
            # Run ALL
            print(f"\n{B}{C}🦂 Running all checks...{RST}")
            for item_label, item_fn in MENU_ITEMS[:-1]:
                try:
                    item_fn()
                except Exception as e:
                    fail(f"{item_label} check crashed: {e}")
        else:
            try:
                fn()
            except Exception as e:
                fail(f"Check crashed unexpectedly: {e}")
                import traceback
                traceback.print_exc()

        input(f"\n  {DIM}Press Enter to return to menu...{RST}")


if __name__ == '__main__':
    main()
