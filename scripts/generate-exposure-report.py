#!/usr/bin/env python3
"""
generate-exposure-report.py — Fink Security Personal Exposure Report Generator
Combines HIBP breach data + Shodan/DNS/harvester recon into a client-facing PDF.

Usage:
    python3 generate-exposure-report.py \
        --email client@example.com \
        --name "Jane Smith" \
        --hibp ~/path/to/hibp-output.json \
        --out ~/esther-lab/engagements/private/<client>/

Requires:
    pip install reportlab --break-system-packages

Output:
    ~/esther-lab/engagements/private/<client>/exposure-report-<date>.pdf
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
except ImportError:
    print("❌ reportlab not installed.")
    print("   Run: pip install reportlab --break-system-packages")
    sys.exit(1)

# ── Colour palette ─────────────────────────────────────────────────────────────
BLACK      = colors.HexColor('#0a0a12')
WHITE      = colors.HexColor('#f3f4f6')
CYAN       = colors.HexColor('#22d3ee')
CYAN_DIM   = colors.HexColor('#0e7490')
DARK_CARD  = colors.HexColor('#1e293b')
MUTED      = colors.HexColor('#94a3b8')
RED        = colors.HexColor('#ef4444')
ORANGE     = colors.HexColor('#f97316')
YELLOW     = colors.HexColor('#eab308')
BLUE       = colors.HexColor('#3b82f6')
GREEN      = colors.HexColor('#22c55e')

SEV_COLORS = {
    'critical': RED,
    'high':     ORANGE,
    'medium':   YELLOW,
    'low':      BLUE,
}
SEV_LABELS = {
    'critical': '🔴 CRITICAL',
    'high':     '🟠 HIGH',
    'medium':   '🟡 MEDIUM',
    'low':      '🔵 LOW',
}


def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles['title'] = ParagraphStyle(
        'title', fontSize=28, fontName='Helvetica-Bold',
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=4
    )
    styles['subtitle'] = ParagraphStyle(
        'subtitle', fontSize=13, fontName='Helvetica',
        textColor=CYAN, alignment=TA_CENTER, spaceAfter=2
    )
    styles['meta'] = ParagraphStyle(
        'meta', fontSize=10, fontName='Helvetica',
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=16
    )
    styles['section'] = ParagraphStyle(
        'section', fontSize=14, fontName='Helvetica-Bold',
        textColor=CYAN, spaceBefore=20, spaceAfter=8
    )
    styles['body'] = ParagraphStyle(
        'body', fontSize=10, fontName='Helvetica',
        textColor=WHITE, spaceAfter=6, leading=15
    )
    styles['muted'] = ParagraphStyle(
        'muted', fontSize=9, fontName='Helvetica',
        textColor=MUTED, spaceAfter=4, leading=13
    )
    styles['breach_title'] = ParagraphStyle(
        'breach_title', fontSize=11, fontName='Helvetica-Bold',
        textColor=WHITE, spaceAfter=2
    )
    styles['mono'] = ParagraphStyle(
        'mono', fontSize=9, fontName='Courier',
        textColor=CYAN, spaceAfter=4
    )
    return styles


def severity_badge_color(sev: str) -> colors.Color:
    return SEV_COLORS.get(sev, BLUE)


def build_summary_table(breach_counts: dict, total: int, pastes: int) -> Table:
    data = [
        ['Metric', 'Count'],
        ['Total breaches found', str(total)],
        ['Paste site appearances', str(pastes)],
        ['Critical severity', str(breach_counts.get('critical', 0))],
        ['High severity',     str(breach_counts.get('high', 0))],
        ['Medium severity',   str(breach_counts.get('medium', 0))],
        ['Low severity',      str(breach_counts.get('low', 0))],
    ]

    t = Table(data, colWidths=[3.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0),  DARK_CARD),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  CYAN),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 10),
        ('BACKGROUND',   (0, 1), (-1, -1), BLACK),
        ('TEXTCOLOR',    (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLACK, DARK_CARD]),
        ('GRID',         (0, 0), (-1, -1), 0.5, CYAN_DIM),
        ('ALIGN',        (1, 0), (1, -1),  'CENTER'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',   (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        # Colour the severity count cells
        ('TEXTCOLOR', (1, 3), (1, 3), RED),
        ('TEXTCOLOR', (1, 4), (1, 4), ORANGE),
        ('TEXTCOLOR', (1, 5), (1, 5), YELLOW),
        ('TEXTCOLOR', (1, 6), (1, 6), BLUE),
        ('FONTNAME',  (1, 3), (1, 6), 'Helvetica-Bold'),
    ]))
    return t


def build_breach_table(breach: dict) -> Table:
    sev   = breach.get('severity', 'low')
    color = severity_badge_color(sev)
    label = SEV_LABELS.get(sev, sev.upper())

    data = [
        ['Field',         'Value'],
        ['Severity',      label],
        ['Breach date',   breach.get('breach_date', 'Unknown')],
        ['Records',       f"{breach.get('pwn_count', 0):,}"],
        ['Data exposed',  ', '.join(breach.get('data_classes', [])[:6])],
        ['Domain',        breach.get('domain') or 'N/A'],
        ['Verified',      'Yes' if breach.get('is_verified') else 'No (unverified)'],
    ]
    if breach.get('is_sensitive'):
        data.append(['Warning', '⚠️ Sensitive breach'])

    t = Table(data, colWidths=[1.5*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  DARK_CARD),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  CYAN),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('BACKGROUND',    (0, 1), (-1, -1), BLACK),
        ('TEXTCOLOR',     (0, 1), (0, -1),  MUTED),
        ('TEXTCOLOR',     (1, 1), (1, -1),  WHITE),
        ('TEXTCOLOR',     (1, 1), (1, 1),   color),
        ('FONTNAME',      (0, 1), (0, -1),  'Helvetica-Bold'),
        ('FONTNAME',      (1, 1), (1, 1),   'Helvetica-Bold'),
        ('GRID',          (0, 0), (-1, -1), 0.3, CYAN_DIM),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    return t


def build_recommendations(breaches: list[dict]) -> list[str]:
    recs = []
    sevs = {b['severity'] for b in breaches}
    classes = {dc for b in breaches for dc in b.get('data_classes', [])}

    if 'Passwords' in classes or 'critical' in sevs:
        recs.append("Change passwords immediately on all accounts using the same or similar password. Use a password manager to generate unique passwords for every account.")
    if any(c in classes for c in ['Passwords', 'Email addresses']):
        recs.append("Enable two-factor authentication (2FA) on all important accounts — email, banking, social media. Use an authenticator app rather than SMS where possible.")
    if any(c in classes for c in ['CreditCards', 'Partial credit card data', 'BankAccountNumbers']):
        recs.append("Monitor your bank and credit card statements for unauthorized transactions. Consider placing a credit freeze with the major bureaus (Equifax, Experian, TransUnion).")
    if 'PhoneNumbers' in classes or 'Phone numbers' in classes:
        recs.append("Be alert to SIM swapping attacks. Contact your mobile carrier to add a PIN or passcode to your account.")
    if len(breaches) > 5:
        recs.append("You have appeared in many data breaches. Consider using a unique email alias for each service to limit future exposure.")
    if not recs:
        recs.append("Your exposure is limited. Continue using strong, unique passwords and enabling 2FA where available.")

    return recs


def generate_pdf(
    client_name: str,
    email: str,
    hibp_data: dict,
    out_path: Path
):
    doc    = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch,   bottomMargin=0.75*inch,
        title=f"Personal Exposure Report — {client_name}",
        author="Fink Security / ESTHER"
    )

    styles  = build_styles()
    story   = []
    now     = datetime.now(timezone.utc).strftime('%B %d, %Y')
    breaches = hibp_data.get('breaches', [])
    pastes   = hibp_data.get('pastes', [])
    summary  = hibp_data.get('summary', {})
    sev_counts = summary.get('severity', {})
    total    = summary.get('total_breaches', len(breaches))

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("FINK SECURITY", styles['title']))
    story.append(Paragraph("Personal Exposure Report", styles['subtitle']))
    story.append(Paragraph(
        f"Prepared for: {client_name} &nbsp;|&nbsp; {email} &nbsp;|&nbsp; {now}",
        styles['meta']
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=CYAN_DIM, spaceAfter=16))

    # ── Executive summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", styles['section']))

    if total == 0:
        summary_text = (
            f"Good news — no breach data was found for <b>{email}</b> in the "
            f"Have I Been Pwned database. This means your email address has not "
            f"appeared in any known publicly disclosed data breaches. Continue "
            f"practising strong password hygiene and monitoring for future exposure."
        )
    else:
        critical = sev_counts.get('critical', 0)
        high     = sev_counts.get('high', 0)
        intro    = "requires immediate attention" if critical > 0 else "warrants your attention"
        summary_text = (
            f"Your email address <b>{email}</b> has appeared in <b>{total} data "
            f"breach{'es' if total != 1 else ''}</b> and {intro}. "
            f"{'There are <b>' + str(critical) + ' critical severity</b> breaches involving your passwords. ' if critical else ''}"
            f"{'There are <b>' + str(high) + ' high severity</b> breaches. ' if high else ''}"
            f"Review the findings below and follow the recommendations to reduce your risk."
        )

    story.append(Paragraph(summary_text, styles['body']))
    story.append(Spacer(1, 0.1*inch))
    story.append(build_summary_table(sev_counts, total, len(pastes)))
    story.append(Spacer(1, 0.2*inch))

    # ── Breach details ────────────────────────────────────────────────────────
    if breaches:
        story.append(Paragraph("Breach Details", styles['section']))
        story.append(Paragraph(
            "The following data breaches were found. Entries marked 'unverified' "
            "come from credential lists and may include data aggregated from multiple sources.",
            styles['muted']
        ))
        story.append(Spacer(1, 0.1*inch))

        for sev in ['critical', 'high', 'medium', 'low']:
            sev_breaches = [b for b in breaches if b.get('severity') == sev]
            if not sev_breaches:
                continue
            for b in sev_breaches:
                block = [
                    Paragraph(b.get('title', b.get('name', 'Unknown')), styles['breach_title']),
                    build_breach_table(b),
                    Spacer(1, 0.12*inch),
                ]
                story.append(KeepTogether(block))

    # ── Paste sites ───────────────────────────────────────────────────────────
    if pastes:
        story.append(Paragraph("Paste Site Appearances", styles['section']))
        story.append(Paragraph(
            f"Your email was found in {len(pastes)} paste site(s). "
            "These are public posts where credential lists are shared.",
            styles['body']
        ))
        paste_data = [['Source', 'Date', 'Title']] + [
            [
                p.get('Source', 'Unknown'),
                (p.get('Date') or 'Unknown')[:10],
                (p.get('Title') or 'Untitled')[:60],
            ]
            for p in pastes[:10]
        ]
        pt = Table(paste_data, colWidths=[1.2*inch, 1*inch, 3.3*inch])
        pt.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),  DARK_CARD),
            ('TEXTCOLOR',   (0, 0), (-1, 0),  CYAN),
            ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, -1), 9),
            ('BACKGROUND',  (0, 1), (-1, -1), BLACK),
            ('TEXTCOLOR',   (0, 1), (-1, -1), WHITE),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLACK, DARK_CARD]),
            ('GRID',        (0, 0), (-1, -1), 0.3, CYAN_DIM),
            ('TOPPADDING',  (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(pt)
        story.append(Spacer(1, 0.2*inch))

    # ── Recommendations ───────────────────────────────────────────────────────
    story.append(Paragraph("Recommendations", styles['section']))
    recs = build_recommendations(breaches)
    for i, rec in enumerate(recs, 1):
        story.append(Paragraph(f"{i}. {rec}", styles['body']))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=CYAN_DIM, spaceAfter=8))
    story.append(Paragraph(
        "This report was generated by ESTHER, Fink Security's autonomous security agent. "
        "Breach data sourced from Have I Been Pwned (haveibeenpwned.com). "
        "For questions or to upgrade to continuous monitoring, visit finksecurity.com.",
        styles['muted']
    ))
    story.append(Paragraph(
        f"© {datetime.now().year} Fink Security · Confidential · finksecurity.com",
        styles['muted']
    ))

    doc.build(story)
    print(f"  ✅ Report generated: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Generate Personal Exposure Report PDF')
    parser.add_argument('--email',  required=True, help='Client email address')
    parser.add_argument('--name',   required=True, help='Client full name')
    parser.add_argument('--hibp',   required=True, help='Path to hibp-check.py JSON output')
    parser.add_argument('--out',    default='.', help='Output directory')
    args = parser.parse_args()

    hibp_path = Path(args.hibp).expanduser()
    if not hibp_path.exists():
        print(f"❌ HIBP JSON not found: {hibp_path}")
        print(f"   Run first: python3 hibp-check.py {args.email} --out <dir>")
        sys.exit(1)

    hibp_data = json.loads(hibp_path.read_text())
    out_dir   = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str  = datetime.now().strftime('%Y-%m-%d')
    safe_name = args.name.lower().replace(' ', '-')
    out_path  = out_dir / f"exposure-report-{safe_name}-{date_str}.pdf"

    print(f"🦂 Generating Personal Exposure Report for {args.name}...")
    generate_pdf(args.name, args.email, hibp_data, out_path)

    total = hibp_data.get('summary', {}).get('total_breaches', 0)
    crit  = hibp_data.get('summary', {}).get('severity', {}).get('critical', 0)
    print(f"   {total} breaches | {crit} critical")
    print(f"   Ready to deliver to client.")


if __name__ == '__main__':
    main()
