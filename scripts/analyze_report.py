#!/usr/bin/env python3
"""
analyze_report.py — Fink Security Network Scan Analyzer
ESTHER runs this after receiving a network scan report via report_ingest.py

Usage:
  python3 analyze_report.py <path_to_report.json> <customer_email>

What it does:
  1. Parses the incoming JSON scan report
  2. Looks up CVEs via NVD API for detected service versions
  3. Maps findings to Metasploit modules
  4. Computes risk score (Severity × Exposure × Ease)
  5. Generates a beautiful HTML report
  6. Emails it to the customer via Gmail SMTP

Dependencies:
  pip install requests jinja2
"""

import os
import sys
import json
import smtplib
import logging
import argparse
import datetime
import requests
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
GMAIL_USER     = os.environ.get('GMAIL_USER', 'finksecopsteam@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
NVD_API_KEY    = os.environ.get('NVD_API_KEY', '')   # optional — raises rate limit
NVD_BASE_URL   = "https://services.nvd.nist.gov/rest/json/cves/2.0"
FINK_BRAND     = "#22d3ee"
FINK_DARK      = "#0a0a12"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ANALYZE] %(message)s')
log = logging.getLogger(__name__)


# ── CVE Lookup ────────────────────────────────────────────────────────────────
def lookup_cves(product: str, version: str) -> list:
    """Query NVD API for CVEs matching product + version."""
    if not product:
        return []
    try:
        params = {"keywordSearch": product, "resultsPerPage": 5}
        if version:
            params["keywordSearch"] = f"{product} {version}"
        headers = {}
        if NVD_API_KEY:
            headers["apiKey"] = NVD_API_KEY

        resp = requests.get(NVD_BASE_URL, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []

        data = resp.json()
        cves = []
        for item in data.get("vulnerabilities", [])[:5]:
            cve = item.get("cve", {})
            cve_id = cve.get("id", "")
            descriptions = cve.get("descriptions", [])
            desc = next((d["value"] for d in descriptions if d["lang"] == "en"), "")[:200]
            metrics = cve.get("metrics", {})

            # Get CVSS score — try v3.1 first, fall back to v2
            score = None
            severity = None
            for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if key in metrics and metrics[key]:
                    m = metrics[key][0]
                    score = m.get("cvssData", {}).get("baseScore")
                    severity = m.get("cvssData", {}).get("baseSeverity", "")
                    break

            if cve_id:
                cves.append({
                    "id":       cve_id,
                    "desc":     desc,
                    "score":    score,
                    "severity": severity,
                    "url":      f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                })
        time.sleep(0.6)  # NVD rate limit: 5 req/30s without key, 50/30s with key
        return cves
    except Exception as e:
        log.warning(f"CVE lookup failed for {product}: {e}")
        return []


# ── Metasploit module mapping ─────────────────────────────────────────────────
METASPLOIT_MAP = {
    445:  [{"module": "exploit/windows/smb/ms17_010_eternalblue", "name": "EternalBlue (MS17-010)", "reliability": "Excellent"}],
    3389: [{"module": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce", "name": "BlueKeep RCE (CVE-2019-0708)", "reliability": "Normal"}],
    21:   [{"module": "exploit/unix/ftp/vsftpd_234_backdoor", "name": "vsftpd 2.3.4 Backdoor", "reliability": "Excellent"},
           {"module": "auxiliary/scanner/ftp/anonymous", "name": "FTP Anonymous Login Scanner", "reliability": "Normal"}],
    23:   [{"module": "auxiliary/scanner/telnet/telnet_login", "name": "Telnet Login Scanner", "reliability": "Normal"}],
    5900: [{"module": "auxiliary/scanner/vnc/vnc_login", "name": "VNC Login Scanner", "reliability": "Normal"},
           {"module": "exploit/multi/vnc/vnc_keyboard_exec", "name": "VNC Keyboard Exec", "reliability": "Normal"}],
    1433: [{"module": "exploit/windows/mssql/ms09_004_sp_replwritetovarbin", "name": "MSSQL sp_replwritetovarbin", "reliability": "Good"}],
    3306: [{"module": "exploit/multi/mysql/mysql_udf_payload", "name": "MySQL UDF Payload", "reliability": "Good"},
           {"module": "auxiliary/scanner/mysql/mysql_login", "name": "MySQL Login Scanner", "reliability": "Normal"}],
    27017:[{"module": "auxiliary/scanner/mongodb/mongodb_login", "name": "MongoDB Login Scanner", "reliability": "Normal"}],
    5985: [{"module": "exploit/windows/winrm/winrm_script_exec", "name": "WinRM Script Exec", "reliability": "Normal"}],
    6379: [{"module": "auxiliary/scanner/redis/redis_login", "name": "Redis Login Scanner", "reliability": "Normal"}],
}

# ── Risk scoring ──────────────────────────────────────────────────────────────
SEVERITY_SCORE  = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
EXPOSURE_SCORE  = {"internet": 3, "network": 2, "local": 1}
EASE_SCORE      = {
    23: 3, 21: 3, 5900: 3, 445: 3, 3389: 3, 27017: 3,
    3306: 2, 1433: 2, 5985: 2, 135: 2, 139: 2,
    80: 1, 443: 1, 22: 1, 53: 1,
}

def compute_risk_score(findings: list) -> dict:
    """Compute overall risk score 0-100 and letter grade."""
    if not findings:
        return {"score": 95, "grade": "A", "color": "#22c55e", "label": "Excellent"}

    total = 0
    max_possible = 0
    for f in findings:
        sev   = SEVERITY_SCORE.get(f.get("risk", "LOW"), 1)
        exp   = EXPOSURE_SCORE.get("network", 2)
        ease  = EASE_SCORE.get(f.get("port", 0), 1)
        total += sev * exp * ease
        max_possible += 4 * 3 * 3

    raw = 1 - (total / max_possible) if max_possible else 1
    score = round(raw * 100)

    if score >= 90:   return {"score": score, "grade": "A", "color": "#22c55e",  "label": "Excellent"}
    elif score >= 80: return {"score": score, "grade": "B", "color": "#84cc16",  "label": "Good"}
    elif score >= 65: return {"score": score, "grade": "C", "color": "#eab308",  "label": "Fair"}
    elif score >= 40: return {"score": score, "grade": "D", "color": "#f97316",  "label": "Poor"}
    else:             return {"score": score, "grade": "F", "color": "#ef4444",  "label": "Critical Risk"}


def classify_exposure(port: int, host_ip: str, gateway: str) -> str:
    """Rough exposure classification."""
    if host_ip == gateway:
        return "internet"  # Router-facing — assume internet exposed
    return "network"


def ease_label(port: int) -> str:
    e = EASE_SCORE.get(port, 1)
    return {3: "Easy", 2: "Moderate", 1: "Hard"}.get(e, "Moderate")


# ── Device classification ─────────────────────────────────────────────────────
def friendly_device_role(device_type: str, open_ports: list) -> str:
    dt = device_type.lower()
    ports = [p["port"] for p in open_ports]
    if "router" in dt or "tp-link" in dt or "netgear" in dt or "ubiquiti" in dt:
        return "Router / Gateway"
    if "apple" in dt:
        if 5900 in ports: return "Mac (Screen Sharing enabled)"
        return "Apple Device (Mac / iPhone / iPad)"
    if "raspberry" in dt:    return "Raspberry Pi"
    if "google" in dt:       return "Google Smart Home Device"
    if "amazon" in dt:       return "Amazon Echo / Fire Device"
    if "philips" in dt:      return "Smart Lighting (Philips Hue)"
    if "xiaomi" in dt:       return "Xiaomi IoT Device"
    if "vmware" in dt:       return "Virtual Machine"
    if 3389 in ports:        return "Windows PC (RDP enabled)"
    if 445 in ports:         return "Windows PC / NAS"
    if 22 in ports:          return "Linux / Unix Device"
    if 80 in ports or 443 in ports: return "Web Server / NAS"
    return device_type if device_type != "unknown" else "Unknown Device"


def display_name(host: dict, role: str) -> str:
    """Return a friendly display name — never 'unknown'."""
    hostname = host.get("hostname", "") or ""
    vendor   = host.get("vendor", "") or ""
    if hostname and hostname.lower() not in ("unknown", "localhost"):
        return hostname
    if vendor and vendor.lower() not in ("unknown", ""):
        return f"{vendor} Device"
    if role and role.lower() not in ("unknown", "unknown device"):
        return role
    return "Unidentified Device"


def positive_findings(hosts: list, findings: list) -> list:
    """Generate positive security observations."""
    positives = []
    finding_ports = {f["port"] for f in findings}
    all_open_ports = {p["port"] for h in hosts for p in h.get("open_ports", [])}

    if 445 not in all_open_ports:
        positives.append("No SMB file sharing exposed — protects against ransomware-class attacks like EternalBlue")
    if 23 not in all_open_ports:
        positives.append("No Telnet detected — good, it transmits passwords in plain text")
    if 3389 not in finding_ports and 3389 not in all_open_ports:
        positives.append("No exposed Remote Desktop (RDP) — one of the most common attack entry points")
    if 27017 not in all_open_ports:
        positives.append("No exposed MongoDB database — a common source of data breaches")
    if len(hosts) < 20:
        positives.append(f"Manageable network size — {len(hosts)} devices makes it easier to monitor for unexpected additions")
    return positives


# ── Plain-English explanations ────────────────────────────────────────────────
PORT_EXPLAINERS = {
    21:    ("FTP File Transfer", "An old file transfer service that sends data — including passwords — without encryption. Anyone on your network could intercept them.", "Disable FTP on this device. Use SFTP or a modern file sharing service instead."),
    22:    ("SSH Remote Access", "A secure remote login service. While encrypted, it can be brute-forced if weak passwords are used.", "Ensure SSH uses key-based authentication and disable password login. Consider changing the default port."),
    23:    ("Telnet (Unencrypted Remote Access)", "A remote login service that sends everything — including your password — in plain text that anyone can read. This should never be open.", "Disable Telnet immediately. There is no reason to use it on a modern network."),
    80:    ("Web Server (HTTP)", "This device is running a website or web interface accessible over your network.", "Ensure the web interface requires a strong password and consider disabling it if not needed."),
    135:   ("Windows RPC", "A Windows networking service. Often targeted by malware and worms.", "If this is a Windows PC, ensure Windows Firewall is enabled and the system is fully updated."),
    139:   ("NetBIOS / File Sharing", "An older Windows file sharing protocol. Historically a major attack target.", "Disable NetBIOS if not actively sharing files. Enable Windows Firewall."),
    443:   ("Secure Web Server (HTTPS)", "An encrypted web interface. Lower risk than HTTP but should still require authentication.", "Verify the web interface requires a strong password."),
    445:   ("SMB File Sharing", "Windows file sharing — the same service exploited by the WannaCry ransomware. Critical to secure.", "Ensure Windows is fully updated. Disable SMB if not actively sharing files. Never expose this to the internet."),
    1433:  ("Microsoft SQL Server", "A database server that should never be internet-facing.", "Immediately restrict access to this database. It should only be accessible from trusted applications."),
    3306:  ("MySQL Database", "A database server exposed on your network.", "Restrict MySQL access to localhost or specific IPs only. Change the root password if still default."),
    3389:  ("Remote Desktop (RDP)", "Allows full remote control of a Windows PC. One of the most attacked services on the internet.", "Disable RDP if not needed. If required, enable Network Level Authentication and use a VPN."),
    5900:  ("VNC Remote Desktop", "Remote desktop access — often with weak or no authentication by default.", "Disable VNC if not actively used. If needed, require a strong password and consider a VPN."),
    5985:  ("Windows Remote Management", "Allows remote management of Windows systems.", "Restrict WinRM access and ensure strong credentials are required."),
    8080:  ("Alternate Web Server", "A secondary web interface, often used by routers, cameras, or NAS devices.", "Verify this interface requires a strong password. Update the device firmware."),
    27017: ("MongoDB Database", "A database often misconfigured to require no authentication — a major breach risk.", "Immediately restrict MongoDB access. Add authentication if not enabled."),
}

GLOSSARY = {
    "RDP":          "Remote Desktop Protocol — allows someone to control a computer remotely over a network",
    "SMB":          "Server Message Block — Windows file and printer sharing protocol",
    "SSH":          "Secure Shell — encrypted remote access protocol",
    "VNC":          "Virtual Network Computing — remote desktop access tool",
    "FTP":          "File Transfer Protocol — an old, unencrypted file transfer method",
    "CVE":          "Common Vulnerabilities and Exposures — a database of known security flaws",
    "CVSS":         "Common Vulnerability Scoring System — rates vulnerability severity from 0-10",
    "MITRE ATT&CK": "A framework that describes how attackers operate — used by security professionals worldwide",
    "Metasploit":   "A tool used by security professionals (and attackers) to test and exploit vulnerabilities",
    "IoT":          "Internet of Things — smart home devices like thermostats, cameras, and doorbells",
    "Port":         "A numbered door on a device through which network traffic flows",
    "Firewall":     "A security system that controls which network traffic is allowed in or out",
}


# ── HTML Report Generator ─────────────────────────────────────────────────────
def generate_html_report(report: dict, enriched_findings: list, risk: dict, positives: list) -> str:
    network   = report.get("network", {})
    hosts     = report.get("hosts", [])
    scan_meta = report.get("scan_meta", {})
    sys_info  = report.get("system_info", {})
    timestamp = report.get("timestamp", "")[:10]
    rs        = report.get("analysis", {}).get("risk_summary", {})

    # Quick win checklist
    quick_wins = []
    seen_ports = set()
    priority_ports = [23, 5900, 3389, 445, 21, 3306, 1433, 27017, 135, 139]
    for port in priority_ports:
        for f in enriched_findings:
            if f["port"] == port and port not in seen_ports:
                _, _, action = PORT_EXPLAINERS.get(port, ("", "", "Review and secure this service."))
                quick_wins.append({"device": f["hostname"] or f["host"], "port": port, "action": action, "risk": f["risk"]})
                seen_ports.add(port)
    if not quick_wins:
        quick_wins.append({"device": "All devices", "port": None, "action": "Keep firmware and software updated on all devices", "risk": "MEDIUM"})
        quick_wins.append({"device": "Router", "port": None, "action": "Change default router admin password if not already done", "risk": "MEDIUM"})
        quick_wins.append({"device": "All devices", "port": None, "action": "Enable automatic security updates where available", "risk": "LOW"})

    # Device rows
    device_rows = ""
    for host in hosts:
        open_ports = host.get("open_ports", [])
        role = friendly_device_role(host.get("device_type", "unknown"), open_ports)
        port_list = ", ".join(str(p["port"]) for p in open_ports) if open_ports else "None detected"
        host_findings = [f for f in enriched_findings if f["host"] == host["ip"]]
        if any(f["risk"] == "CRITICAL" for f in host_findings):
            badge = '<span class="badge critical">Critical Issue</span>'
        elif any(f["risk"] == "HIGH" for f in host_findings):
            badge = '<span class="badge high">High Risk</span>'
        elif host_findings:
            badge = '<span class="badge medium">Review Needed</span>'
        else:
            badge = '<span class="badge ok">Clean</span>'

        anchor_id = f"device-{host['ip'].replace('.', '-')}"
        findings_link = f'''<br><a href="#{anchor_id}-findings" style="font-size:0.75rem;color:var(--cyan);">View findings ↓</a>''' if host_findings else ""
        dname = display_name(host, role)
        device_rows += f"""
        <tr id="{anchor_id}">
          <td><strong>{dname}</strong><br>
              <span class="ip-toggle" style="display:none;font-size:0.75rem;color:#64748b;">{host['ip']}</span>
              {findings_link}</td>
          <td>{role}</td>
          <td>{host.get('vendor', 'Unknown')}</td>
          <td>{port_list}</td>
          <td>{badge}</td>
        </tr>"""

    # Finding cards
    finding_cards = ""
    for f in enriched_findings:
        port = f["port"]
        name, plain_explain, action = PORT_EXPLAINERS.get(port, (
            f"Port {port} Open",
            "An unexpected service is running on this device.",
            "Investigate and disable if not needed."
        ))
        risk_colors = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}
        risk_color  = risk_colors.get(f["risk"], "#94a3b8")
        msf_modules = METASPLOIT_MAP.get(port, [])
        cves        = f.get("cves", [])

        cve_html = ""
        if cves:
            cve_html = '<div class="cve-list"><strong>⚠ Known Vulnerabilities (CVEs):</strong><ul>'
            for cve in cves:
                score_badge = f'<span class="cvss-score" style="background:{risk_colors.get(cve["severity"], "#94a3b8")}">{cve["score"]} {cve["severity"]}</span>' if cve.get("score") else ""
                cve_html += f'<li><a href="{cve["url"]}" target="_blank">{cve["id"]}</a> {score_badge} — {cve["desc"]}</li>'
            cve_html += "</ul></div>"

        msf_html = ""
        if msf_modules:
            msf_html = '<div class="msf-list"><strong>🔧 Known Exploit Modules:</strong><ul>'
            for m in msf_modules:
                msf_html += f'<li><code>{m["module"]}</code> — {m["name"]} (Reliability: {m["reliability"]})</li>'
            msf_html += "</ul></div>"

        # Get device role for this finding's host
        host_match = next((h for h in hosts if h["ip"] == f["host"]), {})
        host_open_ports = host_match.get("open_ports", [])
        host_role = friendly_device_role(host_match.get("device_type", "unknown"), host_open_ports)
        host_anchor = f"device-{f['host'].replace('.', '-')}"
        host_label = display_name(host_match, host_role) if host_match else (f.get('hostname') or f['host'])
        product_str = f'— {f["product"]} {f["version"]}'.strip() if f.get('product') else ""
        finding_cards += f"""
        <div class="finding-card" data-risk="{f['risk']}" id="{host_anchor}-findings">
          <div class="finding-header" style="border-left: 4px solid {risk_color}">
            <div class="finding-meta">
              <span class="risk-badge" style="background:{risk_color}">{f['risk']}</span>
              <span class="ease-badge">Exploit Ease: {ease_label(port)}</span>
              <span class="mitre-badge">MITRE {f.get('mitre_id', '')}</span>
            </div>
            <h3>{name}</h3>
            <div class="finding-device-box" style="background:#0a0a12;border:1px solid #1e293b;border-radius:6px;padding:0.6rem 0.9rem;margin-top:0.5rem;display:flex;align-items:center;gap:0.75rem;">
              <span style="font-size:1.3rem;">🖥</span>
              <div>
                <div style="font-weight:700;font-size:0.95rem;">{host_label}</div>
                <div style="font-size:0.78rem;color:#64748b;">{host_role} {product_str}</div>
                <a href="#{host_anchor}" style="font-size:0.75rem;color:#22d3ee;">← Back to device table</a>
              </div>
            </div>
          </div>
          <div class="finding-body">
            <div class="explain-box">
              <h4>What this means</h4>
              <p>{plain_explain}</p>
            </div>
            <div class="risk-box">
              <h4>Real-world risk</h4>
              <p>{f.get('advice', '')}</p>
            </div>
            <div class="action-box">
              <h4>✅ What to do</h4>
              <p>{action}</p>
            </div>
            {cve_html}
            {msf_html}
            <details class="technical-detail">
              <summary>Technical details</summary>
              <table class="tech-table">
                <tr><td>Port</td><td>{port}</td></tr>
                <tr><td>Service</td><td>{f.get('service', 'unknown')}</td></tr>
                <tr><td>Product</td><td>{f.get('product', '—')}</td></tr>
                <tr><td>Version</td><td>{f.get('version', '—')}</td></tr>
                <tr><td>MITRE Technique</td><td><a href="https://attack.mitre.org/techniques/{f.get('mitre_id', '').replace('.', '/')}" target="_blank">{f.get('mitre_id', '')} — {f.get('mitre_name', '')}</a></td></tr>
                <tr><td>Tactic</td><td>{f.get('tactic', '')}</td></tr>
              </table>
            </details>
          </div>
        </div>"""

    # Quick wins
    win_items = ""
    for i, w in enumerate(quick_wins[:6], 1):
        risk_colors = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}
        color = risk_colors.get(w["risk"], "#22d3ee")
        win_items += f"""
        <div class="win-item">
          <div class="win-number" style="background:{color}">{i}</div>
          <div class="win-content">
            <strong>{w['device']}{f' — Port {w["port"]}' if w.get('port') else ''}</strong>
            <p>{w['action']}</p>
          </div>
        </div>"""

    # Positive findings
    positive_items = ""
    for p in positives:
        positive_items += f'<div class="positive-item">✓ {p}</div>'

    # Glossary
    glossary_items = ""
    for term, definition in GLOSSARY.items():
        glossary_items += f"<dt><strong>{term}</strong></dt><dd>{definition}</dd>"

    # Full technical appendix
    appendix_hosts = json.dumps(hosts, indent=2)

    one_sentence = (
        f"We found {rs.get('CRITICAL', 0)} critical, {rs.get('HIGH', 0)} high, "
        f"{rs.get('MEDIUM', 0)} medium, and {rs.get('LOW', 0)} low severity issues "
        f"that {'require immediate attention' if rs.get('CRITICAL', 0) else 'should be reviewed'}."
    ) if enriched_findings else "No significant security issues were detected on your network."

    unexpected = [h for h in hosts if h.get("vendor", "").lower() == "unknown" and h.get("device_type", "").lower() in ["unknown", "unknown device"]]
    unexpected_note = f'<div class="alert-box">⚠ <strong>Unexpected Device:</strong> We found {len(unexpected)} device(s) we could not identify. Verify these belong to you.</div>' if unexpected else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fink Security — Home Network Security Report</title>
<style>
  :root {{
    --cyan: #22d3ee;
    --dark: #0a0a12;
    --card: #0f1729;
    --border: #1e293b;
    --text: #e2e8f0;
    --muted: #64748b;
    --critical: #ef4444;
    --high: #f97316;
    --medium: #eab308;
    --low: #22c55e;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--dark); color: var(--text); line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}

  /* Header */
  .report-header {{ background: linear-gradient(135deg, #0f1729 0%, #0a0a12 100%); border: 1px solid var(--border); border-radius: 12px; padding: 2.5rem; margin-bottom: 2rem; text-align: center; }}
  .report-header .logo {{ color: var(--cyan); font-size: 1.2rem; font-weight: 700; letter-spacing: 0.2em; margin-bottom: 0.5rem; }}
  .report-header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  .report-header .meta {{ color: var(--muted); font-size: 0.9rem; }}

  /* Section headers */
  .section-title {{ font-size: 1.2rem; font-weight: 700; color: var(--cyan); border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin: 2rem 0 1rem; letter-spacing: 0.05em; text-transform: uppercase; }}

  /* Cards */
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; }}

  /* Executive summary */
  .exec-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 1rem; }}
  .exec-stat {{ background: var(--dark); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; }}
  .exec-stat .number {{ font-size: 2rem; font-weight: 700; }}
  .exec-stat .label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }}
  .exec-verdict {{ background: var(--dark); border-left: 4px solid var(--cyan); border-radius: 0 8px 8px 0; padding: 1rem 1.25rem; margin-top: 1rem; font-size: 1rem; }}

  /* Risk score */
  .risk-score-display {{ display: flex; align-items: center; gap: 2rem; flex-wrap: wrap; }}
  .risk-grade {{ width: 90px; height: 90px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 900; border: 4px solid; flex-shrink: 0; }}
  .risk-details {{ flex: 1; }}
  .risk-bar-wrap {{ margin: 0.4rem 0; }}
  .risk-bar-label {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 0.2rem; display: flex; justify-content: space-between; }}
  .risk-bar {{ height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }}
  .risk-bar-fill {{ height: 100%; border-radius: 4px; }}

  /* Device table */
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ text-align: left; padding: 0.6rem 0.8rem; color: var(--muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }}
  td {{ padding: 0.7rem 0.8rem; border-bottom: 1px solid #0f1729; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  .ip-toggle {{ cursor: pointer; color: var(--cyan); font-size: 0.75rem; }}
  .show-ip-btn {{ background: none; border: 1px solid var(--border); color: var(--muted); padding: 0.3rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem; margin-bottom: 1rem; }}

  /* Badges */
  .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
  .badge.critical {{ background: #450a0a; color: #ef4444; }}
  .badge.high {{ background: #431407; color: #f97316; }}
  .badge.medium {{ background: #422006; color: #eab308; }}
  .badge.ok {{ background: #052e16; color: #22c55e; }}

  /* Finding cards */
  .finding-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 1.5rem; overflow: hidden; }}
  .finding-header {{ padding: 1.25rem 1.5rem; padding-left: calc(1.5rem + 4px); }}
  .finding-meta {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }}
  .risk-badge {{ display: inline-block; padding: 0.2rem 0.7rem; border-radius: 4px; font-size: 0.72rem; font-weight: 700; color: white; text-transform: uppercase; }}
  .ease-badge, .mitre-badge {{ display: inline-block; padding: 0.2rem 0.7rem; border-radius: 4px; font-size: 0.72rem; background: var(--dark); color: var(--muted); border: 1px solid var(--border); }}
  .finding-header h3 {{ font-size: 1.1rem; margin: 0.3rem 0; }}
  .finding-device {{ font-size: 0.85rem; color: var(--muted); }}
  .finding-body {{ padding: 0 1.5rem 1.5rem; display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
  .explain-box, .risk-box, .action-box {{ background: var(--dark); border-radius: 8px; padding: 1rem; }}
  .action-box {{ grid-column: 1 / -1; border: 1px solid #052e16; }}
  .finding-body h4 {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 0.4rem; }}
  .finding-body p {{ font-size: 0.9rem; }}
  .cve-list, .msf-list {{ grid-column: 1 / -1; background: var(--dark); border-radius: 8px; padding: 1rem; font-size: 0.85rem; }}
  .cve-list ul, .msf-list ul {{ padding-left: 1.2rem; }}
  .cve-list li, .msf-list li {{ margin-bottom: 0.4rem; }}
  .cve-list a {{ color: var(--cyan); }}
  .cvss-score {{ display: inline-block; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 700; color: white; margin: 0 0.3rem; }}
  .msf-list code {{ background: #1e293b; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.78rem; color: var(--cyan); }}
  details.technical-detail {{ grid-column: 1 / -1; }}
  summary {{ cursor: pointer; color: var(--muted); font-size: 0.85rem; padding: 0.5rem 0; }}
  .tech-table {{ margin-top: 0.5rem; font-size: 0.82rem; }}
  .tech-table td {{ padding: 0.3rem 0.5rem; border-bottom: 1px solid var(--border); }}
  .tech-table td:first-child {{ color: var(--muted); width: 140px; }}
  .tech-table a {{ color: var(--cyan); }}

  /* Quick wins */
  .win-item {{ display: flex; gap: 1rem; align-items: flex-start; padding: 1rem; background: var(--dark); border-radius: 8px; margin-bottom: 0.75rem; }}
  .win-number {{ width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; color: white; flex-shrink: 0; }}
  .win-content strong {{ display: block; margin-bottom: 0.2rem; }}
  .win-content p {{ font-size: 0.88rem; color: var(--muted); }}

  /* Positives */
  .positive-item {{ background: #052e16; border: 1px solid #14532d; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.9rem; color: #86efac; }}

  /* Alert box */
  .alert-box {{ background: #431407; border: 1px solid #f97316; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.9rem; }}

  /* Glossary */
  dl {{ display: grid; grid-template-columns: auto 1fr; gap: 0.3rem 1rem; font-size: 0.88rem; }}
  dt {{ color: var(--cyan); font-weight: 600; padding: 0.3rem 0; }}
  dd {{ color: var(--muted); padding: 0.3rem 0; border-bottom: 1px solid var(--border); }}

  /* Appendix */
  .appendix pre {{ background: var(--dark); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; font-size: 0.75rem; overflow-x: auto; color: #94a3b8; white-space: pre-wrap; }}

  /* Footer */
  .report-footer {{ text-align: center; padding: 2rem; color: var(--muted); font-size: 0.82rem; border-top: 1px solid var(--border); margin-top: 3rem; }}
  .report-footer a {{ color: var(--cyan); text-decoration: none; }}

  @media (max-width: 600px) {{
    .finding-body {{ grid-template-columns: 1fr; }}
    .action-box {{ grid-column: 1; }}
    .exec-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="report-header">
    <div class="logo">FINK SECURITY</div>
    <h1>Home Network Security Report</h1>
    <div class="meta">Scan date: {timestamp} &nbsp;·&nbsp; Duration: {scan_meta.get('scan_duration', 'N/A')} &nbsp;·&nbsp; Ports checked: {scan_meta.get('ports_checked', 0)}</div>
  </div>

  <!-- Executive Summary -->
  <div class="section-title">Your Network at a Glance</div>
  <div class="card">
    <div class="exec-grid">
      <div class="exec-stat">
        <div class="number" style="color:var(--cyan)">{network.get('hosts_found', 0)}</div>
        <div class="label">Devices Found</div>
      </div>
      <div class="exec-stat">
        <div class="number" style="color:#ef4444">{rs.get('CRITICAL', 0)}</div>
        <div class="label">Critical Issues</div>
      </div>
      <div class="exec-stat">
        <div class="number" style="color:#f97316">{rs.get('HIGH', 0)}</div>
        <div class="label">High Risk</div>
      </div>
      <div class="exec-stat">
        <div class="number" style="color:#eab308">{rs.get('MEDIUM', 0)}</div>
        <div class="label">Medium Risk</div>
      </div>
      <div class="exec-stat">
        <div class="number" style="color:#22c55e">{rs.get('LOW', 0)}</div>
        <div class="label">Low Risk</div>
      </div>
    </div>
    <div class="exec-verdict">{one_sentence}</div>
  </div>

  {unexpected_note}

  <!-- Devices Found -->
  <div class="section-title">Devices Found on Your Network</div>
  <div class="card">
    <button class="show-ip-btn" onclick="toggleIPs()">Show IP / MAC Addresses</button>
    <table>
      <thead>
        <tr>
          <th>Device Name</th>
          <th>Type / Role</th>
          <th>Manufacturer</th>
          <th>Open Ports</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>{device_rows}</tbody>
    </table>
  </div>

  <!-- Risk Score -->
  <div class="section-title">Overall Risk Score</div>
  <div class="card">
    <div class="risk-score-display">
      <div class="risk-grade" style="color:{risk['color']};border-color:{risk['color']}">
        {risk['grade']}
      </div>
      <div class="risk-details">
        <div style="font-size:1.4rem;font-weight:700;color:{risk['color']}">{risk['score']}/100 — {risk['label']}</div>
        <div style="color:var(--muted);font-size:0.9rem;margin:0.3rem 0 1rem;">Based on severity, exposure, and ease of exploitation</div>
        <div class="risk-bar-wrap">
          <div class="risk-bar-label"><span>Security Exposure</span><span>{min(rs.get('CRITICAL',0)*25 + rs.get('HIGH',0)*10, 100)}%</span></div>
          <div class="risk-bar"><div class="risk-bar-fill" style="width:{min(rs.get('CRITICAL',0)*25 + rs.get('HIGH',0)*10, 100)}%;background:{risk['color']}"></div></div>
        </div>
        <div class="risk-bar-wrap">
          <div class="risk-bar-label"><span>Attack Surface</span><span>{min(len(enriched_findings)*15, 100)}%</span></div>
          <div class="risk-bar"><div class="risk-bar-fill" style="width:{min(len(enriched_findings)*15, 100)}%;background:{risk['color']}"></div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Security Findings -->
  {"<div class='section-title'>Security Findings</div>" + finding_cards if enriched_findings else ""}

  <!-- Quick Wins -->
  <div class="section-title">Quick Win Checklist</div>
  <div class="card">
    <p style="color:var(--muted);font-size:0.88rem;margin-bottom:1rem;">Fix these first — highest impact, prioritized by risk.</p>
    {win_items}
  </div>

  <!-- Positive Findings -->
  {"<div class='section-title'>What You're Doing Right</div><div class='card'>" + positive_items + "</div>" if positives else ""}

  <!-- Glossary -->
  <div class="section-title">Glossary</div>
  <div class="card">
    <dl>{glossary_items}</dl>
  </div>

  <!-- Technical Appendix -->
  <div class="section-title">Technical Appendix</div>
  <div class="card">
    <details>
      <summary style="cursor:pointer;color:var(--muted);">Click to expand full scan data</summary>
      <div class="appendix">
        <p style="color:var(--muted);font-size:0.82rem;margin:1rem 0 0.5rem;">Full device and port scan results:</p>
        <pre>{appendix_hosts}</pre>
      </div>
    </details>
  </div>

  <div class="report-footer">
    <p>Generated by ESTHER &mdash; Fink Security &nbsp;·&nbsp; <a href="https://finksecurity.com">finksecurity.com</a></p>
    <p style="margin-top:0.3rem;">Questions? Email <a href="mailto:finksecopsteam@gmail.com">finksecopsteam@gmail.com</a></p>
  </div>

</div>
<script>
  function toggleIPs() {{
    const spans = document.querySelectorAll('.ip-toggle');
    const btn = document.querySelector('.show-ip-btn');
    const visible = spans[0]?.style.display !== 'none';
    spans.forEach(s => s.style.display = visible ? 'none' : 'inline');
    btn.textContent = visible ? 'Show IP / MAC Addresses' : 'Hide IP / MAC Addresses';
  }}
</script>
</body>
</html>"""
    return html


# ── Email delivery ────────────────────────────────────────────────────────────
def send_email(to_email: str, report_html: str, job_id: str, risk: dict):
    """Send HTML report via Gmail SMTP."""
    if not GMAIL_PASSWORD:
        log.error("GMAIL_APP_PASSWORD not set — cannot send email")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Fink Security Network Report — Risk Grade: {risk['grade']}"
    msg["From"]    = f"ESTHER @ Fink Security <{GMAIL_USER}>"
    msg["To"]      = to_email

    # Plain text fallback
    plain = f"""Your Fink Security Home Network Security Report is ready.

Risk Grade: {risk['grade']} ({risk['score']}/100 — {risk['label']})

Please open the attached HTML file in your browser to view your full report.

Questions? Reply to this email or contact finksecopsteam@gmail.com

— ESTHER, Fink Security
https://finksecurity.com
"""
    msg.attach(MIMEText(plain, "plain"))

    # Attach HTML report as file
    attachment = MIMEBase("text", "html")
    attachment.set_payload(report_html.encode())
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment",
                          filename=f"fink-security-report-{job_id[:8]}.html")
    msg.attach(attachment)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        log.info(f"Report emailed to {to_email}")
        return True
    except Exception as e:
        log.error(f"Email failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fink Security Network Scan Analyzer")
    parser.add_argument("report", help="Path to JSON scan report")
    parser.add_argument("email",  help="Customer email address")
    parser.add_argument("--no-cve", action="store_true", help="Skip CVE lookup (faster)")
    parser.add_argument("--save",   help="Save HTML report to this path")
    args = parser.parse_args()

    # Load report
    report_path = Path(args.report)
    if not report_path.exists():
        log.error(f"Report not found: {report_path}")
        sys.exit(1)

    report   = json.loads(report_path.read_text())
    job_id   = report.get("job_id", "unknown")
    findings = report.get("analysis", {}).get("findings", [])

    log.info(f"Analyzing report for job {job_id} — {len(findings)} findings")

    # CVE enrichment
    enriched = []
    for f in findings:
        ef = dict(f)
        if not args.no_cve and f.get("cve_lookup_ready") and f.get("product"):
            log.info(f"Looking up CVEs for {f['product']} {f.get('version', '')}")
            ef["cves"] = lookup_cves(f.get("product", ""), f.get("version", ""))
        else:
            ef["cves"] = []
        enriched.append(ef)

    # Risk score
    risk      = compute_risk_score(findings)
    hosts     = report.get("hosts", [])
    positives = positive_findings(hosts, findings)

    log.info(f"Risk score: {risk['score']}/100 ({risk['grade']} — {risk['label']})")

    # Generate HTML report
    html = generate_html_report(report, enriched, risk, positives)

    # Save locally if requested
    if args.save:
        Path(args.save).write_text(html)
        log.info(f"Report saved to {args.save}")
    else:
        # Default save path alongside the scan report
        default_path = report_path.parent / f"report-{job_id[:8]}.html"
        default_path.write_text(html)
        log.info(f"Report saved to {default_path}")

    # Email to customer
    success = send_email(args.email, html, job_id, risk)
    if success:
        log.info("✅ Report delivered successfully")
    else:
        log.error("❌ Email delivery failed — report saved locally")
        sys.exit(1)


if __name__ == "__main__":
    main()
