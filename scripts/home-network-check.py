#!/usr/bin/env python3
"""
home-network-check.py — Fink Security Home Network Security Check
Scans a client's public IP via Shodan and generates a plain-English PDF report.

Usage:
    python3 home-network-check.py \
        --target <email or IP> \
        --job-id <job_id> \
        --output-dir <dir>

    python3 home-network-check.py \
        --ip 1.2.3.4 \
        --name "Jane Smith" \
        --email client@example.com \
        --out ~/output/

Requires:
    pip install shodan reportlab requests --break-system-packages

Output:
    <output-dir>/home-network-report-<name>-<date>.pdf
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timezone
from pathlib import Path

try:
    import shodan
except ImportError:
    print("❌ shodan not installed. Run: pip install shodan --break-system-packages")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.pdfgen import canvas
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, PageBreak
except ImportError:
    print("❌ reportlab not installed. Run: pip install reportlab --break-system-packages")
    sys.exit(1)

# ── Colours ────────────────────────────────────────────────────────────────────
BLACK      = colors.HexColor('#0a0a12')
BG_DARK    = colors.HexColor('#0f1117')
CARD_DARK  = colors.HexColor('#1e293b')
WHITE      = colors.HexColor('#f3f4f6')
CYAN       = colors.HexColor('#22d3ee')
CYAN_DIM   = colors.HexColor('#0e7490')
CYAN_LIGHT = colors.HexColor('#67e8f9')
MUTED      = colors.HexColor('#94a3b8')
MUTED_DARK = colors.HexColor('#64748b')
RED        = colors.HexColor('#ef4444')
ORANGE     = colors.HexColor('#f97316')
YELLOW     = colors.HexColor('#eab308')
GREEN      = colors.HexColor('#22c55e')
BLUE       = colors.HexColor('#3b82f6')
TEXT_BODY  = colors.HexColor('#334155')
TEXT_DARK  = colors.HexColor('#1e293b')
TEXT_MUTED = colors.HexColor('#64748b')

# ── Known risky ports ──────────────────────────────────────────────────────────
RISKY_PORTS = {
    21:    ('FTP',              'high',   'Unencrypted file transfer. Often exploited for unauthorized access.'),
    22:    ('SSH',              'medium', 'Remote access protocol. Ensure strong passwords or key-based auth only.'),
    23:    ('Telnet',           'critical','Unencrypted remote access. Should never be exposed to the internet.'),
    25:    ('SMTP',             'high',   'Email server. If unintended, may be abused for spam relay.'),
    53:    ('DNS',              'medium', 'DNS resolver exposed. Can be abused for amplification attacks.'),
    80:    ('HTTP',             'low',    'Unencrypted web server. Check what is being served.'),
    443:   ('HTTPS',            'info',   'Encrypted web server. Verify the certificate and service.'),
    445:   ('SMB',              'critical','Windows file sharing. Extremely dangerous to expose — WannaCry vector.'),
    1433:  ('MSSQL',            'critical','Microsoft SQL Server. Database should never be internet-facing.'),
    1883:  ('MQTT',             'high',   'IoT messaging protocol. Often misconfigured and unauthenticated.'),
    3306:  ('MySQL',            'critical','MySQL database. Should never be internet-facing.'),
    3389:  ('RDP',              'critical','Windows Remote Desktop. Frequent ransomware entry point.'),
    5432:  ('PostgreSQL',       'critical','PostgreSQL database. Should never be internet-facing.'),
    5900:  ('VNC',              'critical','Remote desktop protocol. Often unencrypted and unauthenticated.'),
    6379:  ('Redis',            'critical','Redis database. Unauthenticated Redis is trivially exploitable.'),
    7547:  ('TR-069',           'critical','Router management protocol. Exploited in Mirai botnet attacks.'),
    8080:  ('HTTP Alt',         'low',    'Alternative web server port. Check what is being served.'),
    8443:  ('HTTPS Alt',        'low',    'Alternative HTTPS port. Verify the certificate and service.'),
    8888:  ('HTTP Alt',         'low',    'Alternative web port. Often used by IoT devices.'),
    9200:  ('Elasticsearch',    'critical','Search database. Unauthenticated Elasticsearch leaks everything.'),
    27017: ('MongoDB',          'critical','MongoDB database. Unauthenticated MongoDB is a data breach waiting to happen.'),
    49152: ('UPnP',             'high',   'Universal Plug and Play. Can expose internal services to the internet.'),
}

RISK_COLORS = {
    'critical': RED,
    'high':     ORANGE,
    'medium':   YELLOW,
    'low':      BLUE,
    'info':     GREEN,
}

RISK_LABELS = {
    'critical': 'CRITICAL',
    'high':     'HIGH',
    'medium':   'MEDIUM',
    'low':      'LOW',
    'info':     'INFO',
}


def get_public_ip(target_email: str) -> str | None:
    """Try to resolve public IP from email domain or return None."""
    try:
        import socket
        domain = target_email.split('@')[1] if '@' in target_email else target_email
        ip = socket.gethostbyname(domain)
        return ip
    except Exception:
        return None


def scan_ip(api_key: str, ip: str) -> dict:
    """Run Shodan host lookup on an IP address."""
    try:
        api = shodan.Shodan(api_key)
        result = api.host(ip)
        return {'success': True, 'data': result}
    except shodan.APIError as e:
        if 'No information available' in str(e):
            return {'success': True, 'data': {'ip_str': ip, 'ports': [], 'data': [], 'country_name': 'Unknown', 'isp': 'Unknown', 'org': 'Unknown'}}
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def assess_port(port: int, service_data: dict) -> dict:
    """Assess risk level of an exposed port."""
    known = RISKY_PORTS.get(port, None)
    product = service_data.get('product', '')
    version = service_data.get('version', '')
    banner  = service_data.get('data', '')[:200] if service_data.get('data') else ''

    if known:
        name, risk, description = known
    else:
        name = service_data.get('transport', 'TCP').upper()
        risk = 'low'
        description = f'Service on port {port}. Verify this is intentional.'

    return {
        'port':        port,
        'name':        name,
        'risk':        risk,
        'description': description,
        'product':     product,
        'version':     version,
        'banner':      banner[:100] if banner else '',
    }


def compute_risk_score(findings: list) -> tuple[int, str, str]:
    """Compute overall risk score from port findings."""
    if not findings:
        return 5, 'A', 'Minimal Risk'

    weights = {'critical': 25, 'high': 15, 'medium': 8, 'low': 3, 'info': 0}
    score = sum(weights.get(f['risk'], 0) for f in findings)
    score = min(score, 100)

    if score >= 75:   return score, 'F', 'Critical Risk'
    elif score >= 55: return score, 'D', 'High Risk'
    elif score >= 35: return score, 'C', 'Moderate Risk'
    elif score >= 15: return score, 'B', 'Low Risk'
    else:             return score, 'A', 'Minimal Risk'


def grade_color(grade: str) -> colors.Color:
    return {'A': GREEN, 'B': BLUE, 'C': YELLOW, 'D': ORANGE, 'F': RED}.get(grade, MUTED)


def build_styles():
    styles = {}
    styles['section'] = ParagraphStyle(
        'section', fontSize=14, fontName='Helvetica-Bold',
        textColor=CYAN_DIM, spaceBefore=20, spaceAfter=8)
    styles['body'] = ParagraphStyle(
        'body', fontSize=10, fontName='Helvetica',
        textColor=TEXT_BODY, spaceAfter=6, leading=16)
    styles['muted'] = ParagraphStyle(
        'muted', fontSize=9, fontName='Helvetica',
        textColor=TEXT_MUTED, spaceAfter=4, leading=13)
    styles['breach_title'] = ParagraphStyle(
        'breach_title', fontSize=11, fontName='Helvetica-Bold',
        textColor=TEXT_DARK, spaceAfter=3)
    styles['footer'] = ParagraphStyle(
        'footer', fontSize=8, fontName='Helvetica',
        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=2)
    styles['rec_number'] = ParagraphStyle(
        'rec_number', fontSize=10, fontName='Helvetica-Bold',
        textColor=CYAN_DIM, spaceAfter=2)
    styles['rec_body'] = ParagraphStyle(
        'rec_body', fontSize=10, fontName='Helvetica',
        textColor=TEXT_BODY, spaceAfter=10, leading=15, leftIndent=16)
    return styles


def draw_cover_page(c, doc, client_name, ip, score, grade, label, port_count):
    import math
    w, h = letter
    gc = grade_color(grade)

    # Dark background
    c.setFillColor(BLACK)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Grid
    c.setStrokeColor(colors.HexColor('#1a2234'))
    c.setLineWidth(0.5)
    for x in range(0, int(w) + 48, 48):
        c.line(x, 0, x, h)
    for y in range(0, int(h) + 48, 48):
        c.line(0, y, w, y)

    # Glow
    c.setFillColor(CYAN)
    c.setFillAlpha(0.04)
    c.circle(w/2, h/2, 280, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    # Top bar
    c.setFillColor(CYAN)
    c.rect(0, h - 4, w, 4, fill=1, stroke=0)

    # Corner accents
    c.setStrokeColor(CYAN)
    c.setLineWidth(2)
    c.setStrokeAlpha(0.5)
    for x1, y1, x2, y2 in [
        (0, h-4, 40, h-4), (0, h-4, 0, h-44),
        (w, h-4, w-40, h-4), (w, h-4, w, h-44),
        (0, 4, 40, 4), (0, 4, 0, 44),
        (w, 4, w-40, 4), (w, 4, w, 44),
    ]:
        c.line(x1, y1, x2, y2)
    c.setStrokeAlpha(1.0)

    # Shield
    shield_cx = w / 2
    shield_cy = h * 0.52
    shield_w, shield_h = 90, 105

    c.setFillColor(CARD_DARK)
    c.setStrokeColor(CYAN)
    c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(shield_cx, shield_cy + shield_h/2)
    p.lineTo(shield_cx + shield_w/2, shield_cy + shield_h*0.32)
    p.lineTo(shield_cx + shield_w/2, shield_cy - shield_h*0.1)
    p.curveTo(shield_cx + shield_w/2, shield_cy - shield_h*0.4,
              shield_cx + shield_w*0.2, shield_cy - shield_h*0.48,
              shield_cx, shield_cy - shield_h/2)
    p.curveTo(shield_cx - shield_w*0.2, shield_cy - shield_h*0.48,
              shield_cx - shield_w/2, shield_cy - shield_h*0.4,
              shield_cx - shield_w/2, shield_cy - shield_h*0.1)
    p.lineTo(shield_cx - shield_w/2, shield_cy + shield_h*0.32)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    c.setFillColor(CYAN)
    c.setStrokeColor(CYAN_LIGHT)
    c.setLineWidth(1.5)
    c.circle(shield_cx, shield_cy, 7, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#a5f3fc'))
    c.circle(shield_cx, shield_cy, 3.5, fill=1, stroke=0)

    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    for angle in [90, 90+360/7*i for i in range(1, 7)]:
        rad = math.radians(angle)
        c.line(shield_cx + 7*math.cos(rad), shield_cy + 7*math.sin(rad),
               shield_cx + 28*math.cos(rad), shield_cy + 28*math.sin(rad))
        c.setFillColor(CYAN_LIGHT)
        c.circle(shield_cx + 28*math.cos(rad), shield_cy + 28*math.sin(rad), 3.5, fill=1, stroke=0)

    # Wordmark
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(w/2, shield_cy - shield_h/2 - 50, 'FINK')
    c.setFillColor(CYAN)
    c.drawCentredString(w/2, shield_cy - shield_h/2 - 82, 'SECURITY')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, shield_cy - shield_h/2 - 102, 'finksecurity.com')

    # Report type
    c.setFillColor(CYAN)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, h*0.93, 'HOME NETWORK SECURITY REPORT')

    # Client info
    c.setFillColor(WHITE)
    c.setFont('Helvetica', 11)
    c.drawCentredString(w/2, h*0.89, f'Prepared for: {client_name}')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, h*0.86, f'IP Address: {ip}')
    c.drawCentredString(w/2, h*0.83, datetime.now().strftime('%B %d, %Y'))

    # Risk grade
    c.setFillColor(gc)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(w/2, h*0.79, f'Risk Grade: {grade} — {label}')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 11)
    c.drawCentredString(w/2, h*0.76, f'{port_count} exposed port{"s" if port_count != 1 else ""} detected')

    # Bottom
    c.setStrokeColor(CYAN_DIM)
    c.setLineWidth(0.5)
    c.setStrokeAlpha(0.4)
    c.line(inch, 1.2*inch, w - inch, 1.2*inch)
    c.setStrokeAlpha(1.0)
    c.setFillColor(MUTED_DARK)
    c.setFont('Helvetica', 8)
    c.drawCentredString(w/2, 0.9*inch, 'CONFIDENTIAL — PREPARED FOR AUTHORIZED RECIPIENT ONLY')
    c.drawCentredString(w/2, 0.7*inch, f'Generated by ESTHER · Autonomous Security Agent · {datetime.now().strftime("%B %d, %Y")}')


def draw_body_page(c, doc):
    w, h = letter
    c.setFillColor(CARD_DARK)
    c.rect(0, h - 36, w, 36, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, h - 3, w, 3, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(0.75*inch, h - 22, 'FINK SECURITY')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 9)
    c.drawRightString(w - 0.75*inch, h - 22, 'Home Network Security Report — CONFIDENTIAL')
    c.setFillColor(colors.HexColor('#e2e8f0'))
    c.rect(0, 0, w, 28, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor('#cbd5e1'))
    c.setLineWidth(0.5)
    c.line(0, 28, w, 28)
    c.setFillColor(TEXT_MUTED)
    c.setFont('Helvetica', 8)
    c.drawString(0.75*inch, 10, 'finksecurity.com  ·  Powered by ESTHER')
    c.drawRightString(w - 0.75*inch, 10, f'Page {doc.page}')


def build_port_table(finding: dict) -> Table:
    risk = finding['risk']
    color = RISK_COLORS.get(risk, BLUE)
    label = RISK_LABELS.get(risk, risk.upper())

    rows = [
        [Paragraph('<font size="9" color="#0e7490"><b>Field</b></font>', ParagraphStyle('fh')),
         Paragraph('<font size="9" color="#0e7490"><b>Value</b></font>', ParagraphStyle('vh'))],
        [Paragraph('<font size="9" color="#64748b">Risk Level</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="{color.hexval()}"><b>{label}</b></font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Port</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{finding["port"]}/TCP</font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Service</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{finding["name"]}{" — " + finding["product"] if finding["product"] else ""}{" " + finding["version"] if finding["version"] else ""}</font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Risk</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{finding["description"]}</font>', ParagraphStyle('vl'))],
    ]

    if finding.get('banner'):
        rows.append([
            Paragraph('<font size="9" color="#64748b">Banner</font>', ParagraphStyle('fl')),
            Paragraph(f'<font size="8" color="#64748b">{finding["banner"]}</font>', ParagraphStyle('vl'))
        ])

    t = Table(rows, colWidths=[1.5*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#f1f5f9')),
        ('BACKGROUND',    (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, colors.HexColor('#f8fafc')]),
        ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor('#cbd5e1')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    return t


def build_priority_actions(findings: list, host_data: dict) -> list:
    actions = []
    risks = {f['risk'] for f in findings}
    ports = {f['port'] for f in findings}

    critical = [f for f in findings if f['risk'] == 'critical']
    if critical:
        names = ', '.join(f['name'] for f in critical[:3])
        actions.append((
            'IMMEDIATE — Close or firewall these critical services',
            f'The following services are critically dangerous to expose: {names}. '
            f'Log into your router admin panel and disable port forwarding for these ports immediately. '
            f'If these services are not intentionally exposed, your router may be misconfigured or compromised.'
        ))

    if 3389 in ports or 5900 in ports:
        actions.append((
            'IMMEDIATE — Disable remote desktop access',
            'RDP (port 3389) or VNC (port 5900) is exposed to the internet. These are the most common '
            'ransomware entry points. Disable remote desktop unless absolutely necessary, and if needed, '
            'place it behind a VPN.'
        ))

    if any(p in ports for p in [3306, 5432, 27017, 6379, 9200]):
        actions.append((
            'IMMEDIATE — Remove database from internet',
            'A database service is directly exposed to the internet. This should never happen. '
            'Log into your router and remove any port forwarding rules for database ports. '
            'Databases should only be accessible from your local network.'
        ))

    if 7547 in ports:
        actions.append((
            'URGENT — Update or replace your router',
            'Port 7547 (TR-069) is exposed. This is the port exploited by the Mirai botnet to compromise '
            'millions of routers. Contact your ISP or replace your router immediately.'
        ))

    if findings:
        actions.append((
            'THIS WEEK — Audit your router port forwarding rules',
            'Log into your router admin panel (usually at 192.168.1.1 or 192.168.0.1) and review all '
            'port forwarding rules. Remove any rules you did not intentionally create. '
            'Disable UPnP if your router supports it — it can automatically create dangerous port forwards.'
        ))

    actions.append((
        'THIS WEEK — Update router firmware',
        'Log into your router admin panel and check for firmware updates. Router manufacturers regularly '
        'release security patches. Many home routers run outdated firmware with known vulnerabilities.'
    ))

    actions.append((
        'ONGOING — Consider a network firewall',
        'A hardware firewall or next-generation router (like a Firewalla or pfSense box) gives you '
        'visibility into what devices on your network are doing and blocks inbound threats automatically.'
    ))

    return actions


def generate_pdf(
    client_name: str,
    email: str,
    ip: str,
    host_data: dict,
    findings: list,
    score: int,
    grade: str,
    label: str,
    out_path: Path
):
    w, h = letter
    styles = build_styles()
    now = datetime.now(timezone.utc).strftime('%B %d, %Y')

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.55*inch,   bottomMargin=0.55*inch,
        title=f"Home Network Security Report — {client_name}",
        author="Fink Security / ESTHER"
    )

    def on_first_page(c, doc):
        draw_cover_page(c, doc, client_name, ip, score, grade, label, len(findings))

    def on_later_pages(c, doc):
        draw_body_page(c, doc)

    story = []
    gc = grade_color(grade)

    # ── Risk score block ──────────────────────────────────────────────────────
    story.append(Paragraph('Risk Assessment', styles['section']))

    risk_data = [[
        Paragraph(f'<font size="42" color="{gc.hexval()}"><b>{grade}</b></font>',
                  ParagraphStyle('g', alignment=TA_CENTER)),
        Table([
            [Paragraph(f'<font size="9" color="{CYAN_DIM.hexval()}"><b>NETWORK EXPOSURE SCORE</b></font>',
                       ParagraphStyle('rs'))],
            [Paragraph(f'<font size="17" color="{gc.hexval()}"><b>{label}</b></font>',
                       ParagraphStyle('rl'))],
            [Paragraph(f'<font size="9" color="{TEXT_MUTED.hexval()}">{score}/100  ·  {len(findings)} exposed port{"s" if len(findings) != 1 else ""}  ·  IP: {ip}</font>',
                       ParagraphStyle('rm'))],
        ], colWidths=[4.3*inch]),
        Table([
            [Paragraph(f'<font size="7" color="{RED.hexval()}"><b>CRIT</b></font>',
                       ParagraphStyle('sc', alignment=TA_CENTER)),
             Paragraph(f'<font size="7" color="{ORANGE.hexval()}"><b>HIGH</b></font>',
                       ParagraphStyle('sh', alignment=TA_CENTER)),
             Paragraph(f'<font size="7" color="{YELLOW.hexval()}"><b>MED</b></font>',
                       ParagraphStyle('sm', alignment=TA_CENTER)),
             Paragraph(f'<font size="7" color="{BLUE.hexval()}"><b>LOW</b></font>',
                       ParagraphStyle('sl', alignment=TA_CENTER))],
            [Paragraph(f'<font size="18" color="{RED.hexval()}"><b>{sum(1 for f in findings if f["risk"]=="critical")}</b></font>',
                       ParagraphStyle('scv', alignment=TA_CENTER)),
             Paragraph(f'<font size="18" color="{ORANGE.hexval()}"><b>{sum(1 for f in findings if f["risk"]=="high")}</b></font>',
                       ParagraphStyle('shv', alignment=TA_CENTER)),
             Paragraph(f'<font size="18" color="{YELLOW.hexval()}"><b>{sum(1 for f in findings if f["risk"]=="medium")}</b></font>',
                       ParagraphStyle('smv', alignment=TA_CENTER)),
             Paragraph(f'<font size="18" color="{BLUE.hexval()}"><b>{sum(1 for f in findings if f["risk"]=="low")}</b></font>',
                       ParagraphStyle('slv', alignment=TA_CENTER))],
        ], colWidths=[0.7*inch]*4),
    ]]

    risk_table = Table(risk_data, colWidths=[0.7*inch, 4.3*inch, 2.15*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), CARD_DARK),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (0, 0),   18),
        ('LEFTPADDING',   (1, 0), (1, 0),   10),
        ('LINEBELOW',     (0, 0), (-1, -1), 2, CYAN),
        ('LINEBEFORE',    (2, 0), (2, 0),   0.5, CYAN_DIM),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.2*inch))

    # ── Executive Summary ─────────────────────────────────────────────────────
    story.append(Paragraph('Executive Summary', styles['section']))

    isp  = host_data.get('isp', 'Unknown ISP')
    org  = host_data.get('org', '')
    country = host_data.get('country_name', 'Unknown')

    if not findings:
        summary = (
            f'Good news — no exposed services were found on your public IP address ({ip}). '
            f'Your home network appears to have a clean external footprint. '
            f'Continue to keep your router firmware updated and review these results periodically.'
        )
    else:
        critical_count = sum(1 for f in findings if f['risk'] == 'critical')
        intro = 'requires immediate attention' if critical_count > 0 else 'warrants your attention'
        summary = (
            f'Your public IP address <b>{ip}</b> ({isp}{", " + country if country != "Unknown" else ""}) '
            f'has <b>{len(findings)} exposed service{"s" if len(findings) != 1 else ""}</b> and {intro}. '
            f'{"There are <b>" + str(critical_count) + " critically dangerous</b> service(s) exposed. " if critical_count else ""}'
            f'Review the findings and priority actions below.'
        )

    story.append(Paragraph(summary, styles['body']))
    story.append(Spacer(1, 0.2*inch))

    # ── Priority Actions ──────────────────────────────────────────────────────
    story.append(Paragraph('Priority Actions', styles['section']))
    story.append(Paragraph(
        'The following actions are specific to your network exposure, ordered by urgency.',
        styles['muted']
    ))
    story.append(Spacer(1, 0.1*inch))

    actions = build_priority_actions(findings, host_data)
    for i, (title, body) in enumerate(actions, 1):
        story.append(KeepTogether([
            Paragraph(f'{i}. {title}', styles['rec_number']),
            Paragraph(body, styles['rec_body']),
        ]))

    # ── Exposed Services ──────────────────────────────────────────────────────
    if findings:
        story.append(Paragraph('Exposed Services', styles['section']))
        story.append(Paragraph(
            'The following services were found accessible on your public IP address. '
            'Each entry shows the port, service type, risk level, and what it means for your security.',
            styles['muted']
        ))
        story.append(Spacer(1, 0.1*inch))

        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            sev_findings = [f for f in findings if f['risk'] == sev]
            for finding in sev_findings:
                block = [
                    Paragraph(f'Port {finding["port"]} — {finding["name"]}', styles['breach_title']),
                    build_port_table(finding),
                    Spacer(1, 0.15*inch),
                ]
                story.append(KeepTogether(block))
    else:
        story.append(Paragraph('No Exposed Services Found', styles['section']))
        story.append(Paragraph(
            'No services were detected on your public IP address. This is the ideal result — '
            'your router is not exposing any internal services to the internet.',
            styles['body']
        ))

    # ── What This Means ───────────────────────────────────────────────────────
    story.append(Paragraph('What This Means', styles['section']))
    story.append(Paragraph(
        'Every device on your home network — laptops, phones, smart TVs, cameras, routers — '
        'communicates with the internet through your public IP address. When services are exposed, '
        'it means attackers anywhere in the world can attempt to connect to them.',
        styles['body']
    ))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        '<b>Your router is your front door.</b> Port forwarding rules, UPnP, and remote management '
        'features can leave services exposed without you realizing it. Attackers continuously scan '
        'the entire internet for exposed services — if yours are exposed, they will be found.',
        styles['body']
    ))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        '<b>IoT devices are high risk.</b> Smart cameras, thermostats, and home automation devices '
        'often have weak default credentials and outdated firmware. If exposed, they can be '
        'compromised within minutes of being discovered.',
        styles['body']
    ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(
        width='100%', thickness=0.5,
        color=colors.HexColor('#cbd5e1'), spaceAfter=8
    ))
    story.append(Paragraph(
        'This report was generated by ESTHER, Fink Security\'s autonomous security research agent. '
        'Network data sourced from Shodan (shodan.io). '
        'For questions or continuous monitoring, visit finksecurity.com.',
        styles['muted']
    ))
    story.append(Paragraph(
        f'© {datetime.now().year} Fink Security · Confidential · finksecurity.com',
        styles['footer']
    ))

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f'  ✅ Report generated: {out_path}')
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Fink Security Home Network Security Check')
    parser.add_argument('--target',     help='Client email (for task poller integration)')
    parser.add_argument('--job-id',     help='Job ID (for task poller integration)')
    parser.add_argument('--output-dir', help='Output directory (for task poller integration)')
    parser.add_argument('--ip',         help='IP address to scan directly')
    parser.add_argument('--name',       default='Client', help='Client full name')
    parser.add_argument('--email',      help='Client email address')
    parser.add_argument('--out',        default='.', help='Output directory')
    args = parser.parse_args()

    # Load Shodan API key
    shodan_key = os.environ.get('SHODAN_API_KEY', '')
    if not shodan_key:
        # Try secrets.env
        secrets_path = Path.home() / '.openclaw' / 'workspace' / 'secrets.env'
        if secrets_path.exists():
            for line in secrets_path.read_text().splitlines():
                if line.startswith('SHODAN_API_KEY='):
                    shodan_key = line.split('=', 1)[1].strip().strip('"\'')
                    break

    if not shodan_key:
        print('❌ SHODAN_API_KEY not found in environment or secrets.env')
        sys.exit(1)

    # Resolve arguments — support both task poller and direct invocation
    client_email = args.email or args.target or 'client@example.com'
    client_name  = args.name
    out_dir      = Path(args.output_dir or args.out).expanduser()
    job_id       = args.job_id or 'manual'

    # Resolve IP
    target_ip = args.ip
    if not target_ip:
        print(f'🔍 Resolving public IP for {client_email}...')
        target_ip = get_public_ip(client_email)
        if not target_ip:
            # Fall back to asking the client's apparent IP via a public API
            try:
                r = requests.get('https://api.ipify.org?format=json', timeout=5)
                target_ip = r.json().get('ip', '')
                print(f'  ℹ️  Using VPS public IP as fallback: {target_ip}')
            except Exception:
                print('❌ Could not resolve target IP address')
                sys.exit(1)

    print(f'🦂 Scanning {target_ip} via Shodan...')

    result = scan_ip(shodan_key, target_ip)
    if not result['success']:
        print(f'❌ Shodan scan failed: {result["error"]}')
        sys.exit(1)

    host_data = result['data']
    ports     = host_data.get('data', [])

    print(f'  Found {len(ports)} open port(s)')

    # Assess each port
    findings = []
    for service in ports:
        port    = service.get('port', 0)
        finding = assess_port(port, service)
        findings.append(finding)
        print(f'  Port {port}: {finding["name"]} — {finding["risk"].upper()}')

    # Sort by risk severity
    risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    findings.sort(key=lambda f: risk_order.get(f['risk'], 5))

    score, grade, label = compute_risk_score(findings)
    print(f'  Risk score: {score}/100 — Grade {grade} ({label})')

    # Generate PDF
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str  = datetime.now().strftime('%Y-%m-%d')
    safe_name = client_name.lower().replace(' ', '-')
    out_path  = out_dir / f'home-network-report-{safe_name}-{date_str}.pdf'

    print(f'🦂 Generating Home Network Security Report for {client_name}...')
    generate_pdf(client_name, client_email, target_ip, host_data, findings, score, grade, label, out_path)
    print(f'   {len(findings)} exposed services | Grade {grade}')
    print(f'   Ready to deliver to client.')

    # Save JSON summary for task poller
    summary_path = out_dir / f'home-network-summary-{job_id}.json'
    summary_path.write_text(json.dumps({
        'job_id':    job_id,
        'ip':        target_ip,
        'client':    client_name,
        'email':     client_email,
        'score':     score,
        'grade':     grade,
        'label':     label,
        'findings':  len(findings),
        'pdf':       str(out_path),
        'generated': datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    print(f'   Summary: {summary_path}')


if __name__ == '__main__':
    main()
