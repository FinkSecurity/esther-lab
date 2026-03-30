#!/usr/bin/env python3
"""
generate-exposure-report.py — Fink Security Personal Exposure Report Generator
Combines HIBP breach data into a professional client-facing PDF.

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
        HRFlowable, KeepTogether, PageBreak
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.pdfgen import canvas
    
except ImportError:
    print("❌ reportlab not installed.")
    print("   Run: pip install reportlab --break-system-packages")
    sys.exit(1)

# ── Colour palette ─────────────────────────────────────────────────────────────
BLACK       = colors.HexColor('#0a0a12')
BG_DARK     = colors.HexColor('#0f1117')
CARD_DARK   = colors.HexColor('#1e293b')
CARD_MID    = colors.HexColor('#243044')
WHITE       = colors.HexColor('#f3f4f6')
CYAN        = colors.HexColor('#22d3ee')
CYAN_DIM    = colors.HexColor('#0e7490')
CYAN_LIGHT  = colors.HexColor('#67e8f9')
MUTED       = colors.HexColor('#94a3b8')
MUTED_DARK  = colors.HexColor('#64748b')
RED         = colors.HexColor('#ef4444')
ORANGE      = colors.HexColor('#f97316')
YELLOW      = colors.HexColor('#eab308')
BLUE        = colors.HexColor('#3b82f6')
GREEN       = colors.HexColor('#22c55e')
TEXT_DARK   = colors.HexColor('#1e293b')
TEXT_BODY   = colors.HexColor('#334155')
TEXT_MUTED  = colors.HexColor('#64748b')

SEV_COLORS = {
    'critical': RED,
    'high':     ORANGE,
    'medium':   YELLOW,
    'low':      BLUE,
}
SEV_LABELS = {
    'critical': 'CRITICAL',
    'high':     'HIGH',
    'medium':   'MEDIUM',
    'low':      'LOW',
}


def compute_risk_score(breaches: list, pastes: list) -> tuple[int, str, str]:
    """
    Compute a 0-100 risk score and letter grade.
    Returns (score, grade, label)
    """
    if not breaches:
        return 5, 'A', 'Minimal Risk'

    score = 0
    sev_weights = {'critical': 20, 'high': 12, 'medium': 6, 'low': 2}
    for b in breaches:
        score += sev_weights.get(b.get('severity', 'low'), 2)

    score += len(pastes) * 5

    # Cap at 100
    score = min(score, 100)

    if score >= 75:
        return score, 'F', 'Critical Risk'
    elif score >= 55:
        return score, 'D', 'High Risk'
    elif score >= 35:
        return score, 'C', 'Moderate Risk'
    elif score >= 15:
        return score, 'B', 'Low Risk'
    else:
        return score, 'A', 'Minimal Risk'


def grade_color(grade: str) -> colors.Color:
    return {
        'A': GREEN,
        'B': BLUE,
        'C': YELLOW,
        'D': ORANGE,
        'F': RED,
    }.get(grade, MUTED)


def build_styles():
    styles = {}

    # Cover page styles
    styles['cover_title'] = ParagraphStyle(
        'cover_title', fontSize=11, fontName='Helvetica-Bold',
        textColor=CYAN, alignment=TA_CENTER, spaceAfter=2,
        letterSpacing=4
    )
    styles['cover_report'] = ParagraphStyle(
        'cover_report', fontSize=26, fontName='Helvetica-Bold',
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=4
    )
    styles['cover_meta'] = ParagraphStyle(
        'cover_meta', fontSize=11, fontName='Helvetica',
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=4
    )
    styles['cover_confidential'] = ParagraphStyle(
        'cover_confidential', fontSize=9, fontName='Helvetica-Bold',
        textColor=CYAN_DIM, alignment=TA_CENTER, letterSpacing=3
    )

    # Body styles — dark text on white background
    styles['section'] = ParagraphStyle(
        'section', fontSize=14, fontName='Helvetica-Bold',
        textColor=CYAN_DIM, spaceBefore=20, spaceAfter=8,
        borderPad=0
    )
    styles['subsection'] = ParagraphStyle(
        'subsection', fontSize=11, fontName='Helvetica-Bold',
        textColor=TEXT_DARK, spaceBefore=10, spaceAfter=4
    )
    styles['body'] = ParagraphStyle(
        'body', fontSize=10, fontName='Helvetica',
        textColor=TEXT_BODY, spaceAfter=6, leading=16
    )
    styles['body_bold'] = ParagraphStyle(
        'body_bold', fontSize=10, fontName='Helvetica-Bold',
        textColor=TEXT_DARK, spaceAfter=6, leading=16
    )
    styles['muted'] = ParagraphStyle(
        'muted', fontSize=9, fontName='Helvetica',
        textColor=TEXT_MUTED, spaceAfter=4, leading=13
    )
    styles['breach_title'] = ParagraphStyle(
        'breach_title', fontSize=11, fontName='Helvetica-Bold',
        textColor=TEXT_DARK, spaceAfter=3
    )
    styles['mono'] = ParagraphStyle(
        'mono', fontSize=9, fontName='Courier',
        textColor=CYAN_DIM, spaceAfter=4
    )
    styles['rec_number'] = ParagraphStyle(
        'rec_number', fontSize=10, fontName='Helvetica-Bold',
        textColor=CYAN_DIM, spaceAfter=2
    )
    styles['rec_body'] = ParagraphStyle(
        'rec_body', fontSize=10, fontName='Helvetica',
        textColor=TEXT_BODY, spaceAfter=10, leading=15,
        leftIndent=16
    )
    styles['footer'] = ParagraphStyle(
        'footer', fontSize=8, fontName='Helvetica',
        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=2
    )
    styles['tag'] = ParagraphStyle(
        'tag', fontSize=8, fontName='Helvetica-Bold',
        textColor=CYAN, spaceAfter=0, letterSpacing=2
    )

    return styles


def draw_cover_page(c, doc):
    """Draw the full dark cover page background and branding."""
    w, h = letter

    # Full dark background
    c.setFillColor(BLACK)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Subtle grid lines
    c.setStrokeColor(colors.HexColor('#1a2234'))
    c.setLineWidth(0.5)
    grid_spacing = 48
    for x in range(0, int(w) + grid_spacing, grid_spacing):
        c.line(x, 0, x, h)
    for y in range(0, int(h) + grid_spacing, grid_spacing):
        c.line(0, y, w, y)

    # Cyan glow circle (subtle)
    c.setFillColor(colors.HexColor('#22d3ee'))
    c.setFillAlpha(0.04)
    c.circle(w/2, h/2, 280, fill=1, stroke=0)
    c.setFillAlpha(0.03)
    c.circle(w/2, h/2, 180, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    # Top cyan accent bar
    c.setFillColor(CYAN)
    c.rect(0, h - 4, w, 4, fill=1, stroke=0)

    # Corner accents
    accent_len = 40
    c.setStrokeColor(CYAN)
    c.setLineWidth(2)
    c.setStrokeAlpha(0.5)
    # Top left
    c.line(0, h - 4, accent_len, h - 4)
    c.line(0, h - 4, 0, h - 4 - accent_len)
    # Top right
    c.line(w, h - 4, w - accent_len, h - 4)
    c.line(w, h - 4, w, h - 4 - accent_len)
    # Bottom left
    c.line(0, 4, accent_len, 4)
    c.line(0, 4, 0, 4 + accent_len)
    # Bottom right
    c.line(w, 4, w - accent_len, 4)
    c.line(w, 4, w, 4 + accent_len)
    c.setStrokeAlpha(1.0)

    # Shield SVG-style drawn in reportlab
    shield_cx = w / 2
    shield_cy = h * 0.52
    shield_w = 90
    shield_h = 105

    # Outer shield
    c.setFillColor(CARD_DARK)
    c.setStrokeColor(CYAN)
    c.setLineWidth(2)
    shield_path = c.beginPath()
    shield_path.moveTo(shield_cx, shield_cy + shield_h/2)
    shield_path.lineTo(shield_cx + shield_w/2, shield_cy + shield_h*0.32)
    shield_path.lineTo(shield_cx + shield_w/2, shield_cy - shield_h*0.1)
    shield_path.curveTo(
        shield_cx + shield_w/2, shield_cy - shield_h*0.4,
        shield_cx + shield_w*0.2, shield_cy - shield_h*0.48,
        shield_cx, shield_cy - shield_h/2
    )
    shield_path.curveTo(
        shield_cx - shield_w*0.2, shield_cy - shield_h*0.48,
        shield_cx - shield_w/2, shield_cy - shield_h*0.4,
        shield_cx - shield_w/2, shield_cy - shield_h*0.1
    )
    shield_path.lineTo(shield_cx - shield_w/2, shield_cy + shield_h*0.32)
    shield_path.close()
    c.drawPath(shield_path, fill=1, stroke=1)

    # Center dot
    c.setFillColor(CYAN)
    c.setStrokeColor(CYAN_LIGHT)
    c.setLineWidth(1.5)
    c.circle(shield_cx, shield_cy, 7, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#a5f3fc'))
    c.circle(shield_cx, shield_cy, 3.5, fill=1, stroke=0)

    # Spokes
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    import math
    spoke_angles = [90, 90+360/7, 90+2*360/7, 90+3*360/7, 90+4*360/7, 90+5*360/7, 90+6*360/7]
    for angle in spoke_angles:
        rad = math.radians(angle)
        end_r = 28
        c.line(
            shield_cx + 7*math.cos(rad), shield_cy + 7*math.sin(rad),
            shield_cx + end_r*math.cos(rad), shield_cy + end_r*math.sin(rad)
        )
        c.setFillColor(CYAN_LIGHT)
        c.circle(
            shield_cx + end_r*math.cos(rad),
            shield_cy + end_r*math.sin(rad),
            3.5, fill=1, stroke=0
        )

    # FINK SECURITY wordmark
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(w/2, shield_cy - shield_h/2 - 50, 'FINK')
    c.setFillColor(CYAN)
    c.drawCentredString(w/2, shield_cy - shield_h/2 - 82, 'SECURITY')

    # Tagline
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, shield_cy - shield_h/2 - 102, 'finksecurity.com')

    # Bottom divider
    c.setStrokeColor(CYAN_DIM)
    c.setLineWidth(0.5)
    c.setStrokeAlpha(0.4)
    c.line(inch, 1.2*inch, w - inch, 1.2*inch)
    c.setStrokeAlpha(1.0)

    # Bottom confidential text
    c.setFillColor(MUTED_DARK)
    c.setFont('Helvetica', 8)
    c.drawCentredString(w/2, 0.9*inch, 'CONFIDENTIAL — PREPARED FOR AUTHORIZED RECIPIENT ONLY')
    c.drawCentredString(w/2, 0.7*inch, f'Generated by ESTHER · Autonomous Security Agent · {datetime.now().strftime("%B %d, %Y")}')


def draw_page_header_footer(c, doc):
    """Draw header and footer on body pages."""
    w, h = letter

    # Header bar
    c.setFillColor(CARD_DARK)
    c.rect(0, h - 36, w, 36, fill=1, stroke=0)

    # Cyan top accent
    c.setFillColor(CYAN)
    c.rect(0, h - 3, w, 3, fill=1, stroke=0)

    # Header text
    c.setFillColor(CYAN)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(0.75*inch, h - 22, 'FINK SECURITY')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 9)
    c.drawRightString(w - 0.75*inch, h - 22, 'Personal Exposure Report — CONFIDENTIAL')

    # Footer
    c.setFillColor(colors.HexColor('#e2e8f0'))
    c.rect(0, 0, w, 28, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor('#cbd5e1'))
    c.setLineWidth(0.5)
    c.line(0, 28, w, 28)

    c.setFillColor(TEXT_MUTED)
    c.setFont('Helvetica', 8)
    c.drawString(0.75*inch, 10, 'finksecurity.com  ·  Powered by ESTHER')
    c.drawRightString(w - 0.75*inch, 10, f'Page {doc.page}')


def build_risk_score_table(score: int, grade: str, label: str, total: int, sev_counts: dict, pastes: int) -> Table:
    """Build the prominent risk score summary block."""
    g_color = grade_color(grade)

    # Score block
    score_data = [[
        Paragraph(f'<font size="42" color="{g_color.hexval()}"><b>{grade}</b></font>', ParagraphStyle('g', alignment=TA_CENTER)),
        Table([
            [Paragraph(f'<font size="11" color="{CYAN_DIM.hexval()}"><b>EXPOSURE RISK SCORE</b></font>', ParagraphStyle('rs', alignment=TA_LEFT))],
            [Paragraph(f'<font size="20" color="{g_color.hexval()}"><b>{label}</b></font>', ParagraphStyle('rl', alignment=TA_LEFT))],
            [Paragraph(f'<font size="10" color="{TEXT_MUTED.hexval()}">{score}/100 · {total} breach{"es" if total != 1 else ""} · {pastes} paste{"s" if pastes != 1 else ""}</font>', ParagraphStyle('rm', alignment=TA_LEFT))],
        ], colWidths=[3.8*inch]),
        Table([
            [Paragraph(f'<font size="9" color="{RED.hexval()}"><b>CRITICAL</b></font>', ParagraphStyle('sc', alignment=TA_CENTER)),
             Paragraph(f'<font size="9" color="{ORANGE.hexval()}"><b>HIGH</b></font>', ParagraphStyle('sh', alignment=TA_CENTER)),
             Paragraph(f'<font size="9" color="{YELLOW.hexval()}"><b>MEDIUM</b></font>', ParagraphStyle('sm', alignment=TA_CENTER)),
             Paragraph(f'<font size="9" color="{BLUE.hexval()}"><b>LOW</b></font>', ParagraphStyle('sl', alignment=TA_CENTER))],
            [Paragraph(f'<font size="18" color="{RED.hexval()}"><b>{sev_counts.get("critical",0)}</b></font>', ParagraphStyle('scv', alignment=TA_CENTER)),
             Paragraph(f'<font size="18" color="{ORANGE.hexval()}"><b>{sev_counts.get("high",0)}</b></font>', ParagraphStyle('shv', alignment=TA_CENTER)),
             Paragraph(f'<font size="18" color="{YELLOW.hexval()}"><b>{sev_counts.get("medium",0)}</b></font>', ParagraphStyle('smv', alignment=TA_CENTER)),
             Paragraph(f'<font size="18" color="{BLUE.hexval()}"><b>{sev_counts.get("low",0)}</b></font>', ParagraphStyle('slv', alignment=TA_CENTER))],
        ], colWidths=[0.6*inch, 0.6*inch, 0.75*inch, 0.55*inch]),
    ]]

    outer = Table(score_data, colWidths=[0.7*inch, 3.8*inch, 2.5*inch])
    outer.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), CARD_DARK),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (0, 0),   16),
        ('RIGHTPADDING', (0, 0), (0, 0),   8),
        ('LEFTPADDING',  (1, 0), (1, 0),   8),
        ('TOPPADDING',   (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 14),
        ('LINEBELOW',    (0, 0), (-1, -1), 2, CYAN),
        ('LINEBEFORE',   (2, 0), (2, 0),   0.5, CYAN_DIM),
    ]))
    return outer


def build_breach_table(breach: dict) -> Table:
    sev   = breach.get('severity', 'low')
    color = SEV_COLORS.get(sev, BLUE)
    label = SEV_LABELS.get(sev, sev.upper())

    data = [
        [Paragraph('<font size="9" color="#0e7490"><b>Field</b></font>', ParagraphStyle('fh', alignment=TA_LEFT)),
         Paragraph('<font size="9" color="#0e7490"><b>Value</b></font>', ParagraphStyle('vh', alignment=TA_LEFT))],
        [Paragraph('<font size="9" color="#64748b">Severity</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="{color.hexval()}"><b>{label}</b></font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Breach date</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{breach.get("breach_date", "Unknown")}</font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Records exposed</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{breach.get("pwn_count", 0):,}</font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Data exposed</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{", ".join(breach.get("data_classes", [])[:6])}</font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Domain</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{breach.get("domain") or "N/A"}</font>', ParagraphStyle('vl'))],
        [Paragraph('<font size="9" color="#64748b">Verified</font>', ParagraphStyle('fl')),
         Paragraph(f'<font size="9" color="#334155">{"Yes" if breach.get("is_verified") else "No — unverified aggregate"}</font>', ParagraphStyle('vl'))],
    ]

    t = Table(data, colWidths=[1.5*inch, 4.5*inch])
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


def build_priority_actions(breaches: list, pastes: list) -> list:
    """Build a prioritized, breach-specific action list."""
    actions = []
    classes = {dc for b in breaches for dc in b.get('data_classes', [])}
    sevs = {b['severity'] for b in breaches}
    critical_breaches = [b for b in breaches if b.get('severity') == 'critical']
    recent_breaches = [b for b in breaches if b.get('breach_date', '') >= '2022-01-01']

    if 'Passwords' in classes or 'critical' in sevs:
        breach_names = ', '.join([b.get('title', b.get('name', '')) for b in critical_breaches[:3]])
        actions.append((
            'IMMEDIATE — Change compromised passwords',
            f'Your password was exposed in: {breach_names}. Change these passwords now and on any site where you reused them. Use a password manager (Bitwarden is free) to generate unique passwords for every account.'
        ))

    actions.append((
        'IMMEDIATE — Enable two-factor authentication',
        'Enable 2FA on your email, banking, and social media accounts. Use an authenticator app (Google Authenticator, Authy) rather than SMS. This stops attackers even if they have your password.'
    ))

    if any(c in classes for c in ['Credit cards', 'Partial credit card data', 'Bank account numbers']):
        actions.append((
            'URGENT — Monitor financial accounts',
            'Your financial data was exposed. Check your bank and credit card statements for unauthorized charges. Consider placing a free credit freeze at Equifax, Experian, and TransUnion to prevent new accounts being opened in your name.'
        ))

    if recent_breaches:
        actions.append((
            'THIS WEEK — Check for account takeovers',
            f'You have {len(recent_breaches)} breach(es) from 2022 or later. Log into your important accounts and check for unrecognized logins, devices, or email forwarding rules that you did not set up.'
        ))

    if pastes:
        actions.append((
            'THIS WEEK — Your credentials are on paste sites',
            f'Your email appeared in {len(pastes)} paste site(s) — locations where attackers share stolen credential lists. This means your data is actively being used in automated login attacks. Change passwords on any account using exposed credentials.'
        ))

    if len(breaches) > 6:
        actions.append((
            'ONGOING — Use email aliases',
            'With this many breaches, consider using a unique email alias for each service (SimpleLogin and Apple Hide My Email are free options). This limits future exposure and lets you identify which service leaked your data.'
        ))

    actions.append((
        'ONGOING — Monitor for future breaches',
        'Sign up for free breach alerts at haveibeenpwned.com to be notified if your email appears in future data breaches. Consider upgrading to Fink Security continuous monitoring for automated alerts.'
    ))

    return actions


def build_recommendations(breaches: list, pastes: list) -> list:
    """Legacy recommendations — now replaced by build_priority_actions."""
    return build_priority_actions(breaches, pastes)


def generate_pdf(
    client_name: str,
    email: str,
    hibp_data: dict,
    out_path: Path
):
    w, h = letter

    # Custom page templates
    def cover_template(canvas_obj, doc):
        draw_cover_page(canvas_obj, doc)

    def body_template(canvas_obj, doc):
        draw_page_header_footer(canvas_obj, doc)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.55*inch,   bottomMargin=0.55*inch,
        title=f"Personal Exposure Report — {client_name}",
        author="Fink Security / ESTHER"
    )

    styles   = build_styles()
    story    = []
    now      = datetime.now(timezone.utc).strftime('%B %d, %Y')
    breaches = hibp_data.get('breaches', [])
    pastes   = hibp_data.get('pastes', [])
    summary  = hibp_data.get('summary', {})
    sev_counts = summary.get('severity', {})
    total    = summary.get('total_breaches', len(breaches))

    score, grade, label = compute_risk_score(breaches, pastes)

    # ── Cover page content ────────────────────────────────────────────────────
    # Push content to the lower portion of the cover (above the wordmark area)
    story.append(Spacer(1, h * 0.08))

    # Report type badge
    story.append(Paragraph('PERSONAL EXPOSURE REPORT', styles['cover_title']))
    story.append(Spacer(1, 0.1*inch))

    # Client info block
    story.append(Paragraph(f'Prepared for: {client_name}', styles['cover_meta']))
    story.append(Paragraph(email, styles['cover_meta']))
    story.append(Paragraph(now, styles['cover_meta']))
    story.append(Spacer(1, 0.15*inch))

    # Risk grade on cover
    g_color = grade_color(grade)
    story.append(Paragraph(
        f'<font size="14" color="{g_color.hexval()}"><b>Risk Grade: {grade} — {label}</b></font>',
        ParagraphStyle('cg', alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Paragraph(
        f'<font size="11" color="{MUTED.hexval()}">{total} breach{"es" if total != 1 else ""} · {sev_counts.get("critical",0)} critical · {sev_counts.get("high",0)} high</font>',
        ParagraphStyle('cs', alignment=TA_CENTER, spaceAfter=4)
    ))

    # Switch to body template
    story.append(PageBreak())

    # ── Body pages ────────────────────────────────────────────────────────────
    # Risk Score Section
    story.append(Paragraph('Risk Assessment', styles['section']))
    story.append(Spacer(1, 0.05*inch))
    story.append(build_risk_score_table(score, grade, label, total, sev_counts, len(pastes)))
    story.append(Spacer(1, 0.2*inch))

    # Executive Summary
    story.append(Paragraph('Executive Summary', styles['section']))

    if total == 0:
        summary_text = (
            f'Good news — no breach data was found for <b>{email}</b> in the '
            f'Have I Been Pwned database. Your email address has not appeared in '
            f'any known publicly disclosed data breaches. Continue practising '
            f'strong password hygiene and monitoring for future exposure.'
        )
    else:
        critical = sev_counts.get('critical', 0)
        high     = sev_counts.get('high', 0)
        intro    = 'requires immediate attention' if critical > 0 else 'warrants your attention'
        summary_text = (
            f'Your email address <b>{email}</b> has appeared in <b>{total} data '
            f'breach{"es" if total != 1 else ""}</b> and {intro}. '
            f'{"There are <b>" + str(critical) + " critical severity</b> breaches involving your passwords. " if critical else ""}'
            f'{"There are <b>" + str(high) + " high severity</b> breaches. " if high else ""}'
            f'Review the breach details and priority actions below to reduce your risk.'
        )

    story.append(Paragraph(summary_text, styles['body']))
    story.append(Spacer(1, 0.2*inch))

    # Priority Actions
    story.append(Paragraph('Priority Actions', styles['section']))
    story.append(Paragraph(
        'The following actions are specific to your breach profile, ordered by urgency.',
        styles['muted']
    ))
    story.append(Spacer(1, 0.1*inch))

    actions = build_priority_actions(breaches, pastes)
    for i, (title, body_text) in enumerate(actions, 1):
        action_block = [
            Paragraph(f'{i}. {title}', styles['rec_number']),
            Paragraph(body_text, styles['rec_body']),
        ]
        story.append(KeepTogether(action_block))

    story.append(Spacer(1, 0.1*inch))

    # Breach Details
    if breaches:
        story.append(Paragraph('Breach Details', styles['section']))
        story.append(Paragraph(
            "The following data breaches were found associated with your email address. "
            "Entries marked 'unverified' come from credential lists and may include "
            "data aggregated from multiple sources.",
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
                    Spacer(1, 0.15*inch),
                ]
                story.append(KeepTogether(block))

    # Paste Sites
    if pastes:
        story.append(Paragraph('Paste Site Appearances', styles['section']))
        story.append(Paragraph(
            f'Your email was found in {len(pastes)} paste site(s). '
            'These are public posts where credential lists are shared by attackers.',
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
        pt = Table(paste_data, colWidths=[1.2*inch, 1*inch, 3.8*inch])
        pt.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0),  colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR',    (0, 0), (-1, 0),  CYAN_DIM),
            ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, -1), 9),
            ('BACKGROUND',   (0, 1), (-1, -1), WHITE),
            ('TEXTCOLOR',    (0, 1), (-1, -1), TEXT_BODY),
            ('ROWBACKGROUNDS',(0,1), (-1, -1), [WHITE, colors.HexColor('#f8fafc')]),
            ('GRID',         (0, 0), (-1, -1), 0.3, colors.HexColor('#cbd5e1')),
            ('TOPPADDING',   (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
            ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ]))
        story.append(pt)
        story.append(Spacer(1, 0.2*inch))

    # What This Means section
    story.append(Paragraph('What This Means', styles['section']))
    story.append(Paragraph(
        'Data breaches occur when attackers compromise a company\'s database and steal user records. '
        'Once your data is in a breach, it is typically sold on dark web markets and used in '
        '<b>credential stuffing attacks</b> — automated tools that try your email and password '
        'combination across thousands of websites simultaneously.',
        styles['body']
    ))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        '<b>Old breaches are still dangerous.</b> Attackers don\'t discard old data — they combine '
        'multiple breach databases to build comprehensive profiles. A 2014 breach combined with a '
        '2020 breach gives attackers more information about you than either alone.',
        styles['body']
    ))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        '<b>Unverified breaches still matter.</b> While unverified entries cannot be confirmed '
        'as originating from a specific source, they still contain real credentials that are '
        'actively used in attacks.',
        styles['body']
    ))

    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(
        width='100%', thickness=0.5,
        color=colors.HexColor('#cbd5e1'), spaceAfter=8
    ))
    story.append(Paragraph(
        'This report was generated by ESTHER, Fink Security\'s autonomous security research agent. '
        'Breach data sourced from Have I Been Pwned (haveibeenpwned.com). '
        'For questions, continuous monitoring, or to upgrade your protection, visit finksecurity.com.',
        styles['muted']
    ))
    story.append(Paragraph(
        f'© {datetime.now().year} Fink Security · Confidential · finksecurity.com',
        styles['footer']
    ))

    def on_first_page(c, doc):
        draw_cover_page(c, doc)

    def on_later_pages(c, doc):
        draw_page_header_footer(c, doc)

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f'  ✅ Report generated: {out_path}')
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
        print(f'❌ HIBP JSON not found: {hibp_path}')
        print(f'   Run first: python3 hibp-check.py {args.email} --out <dir>')
        sys.exit(1)

    hibp_data = json.loads(hibp_path.read_text())
    out_dir   = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str  = datetime.now().strftime('%Y-%m-%d')
    safe_name = args.name.lower().replace(' ', '-')
    out_path  = out_dir / f'exposure-report-{safe_name}-{date_str}.pdf'

    print(f'🦂 Generating Personal Exposure Report for {args.name}...')
    generate_pdf(args.name, args.email, hibp_data, out_path)

    total = hibp_data.get('summary', {}).get('total_breaches', 0)
    crit  = hibp_data.get('summary', {}).get('severity', {}).get('critical', 0)
    print(f'   {total} breaches | {crit} critical')
    print(f'   Ready to deliver to client.')


if __name__ == '__main__':
    main()
