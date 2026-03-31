#!/usr/bin/env python3
"""
generate-exposure-report.py — Fink Security Personal Exposure Report Generator

Usage:
    python3 generate-exposure-report.py \
        --email client@example.com \
        --name "Jane Smith" \
        --hibp ~/path/to/hibp-output.json \
        --out ~/esther-lab/engagements/private/<client>/

Requires:
    pip install reportlab pypdf --break-system-packages
"""

import os
import sys
import json
import argparse
import math
from datetime import datetime, timezone
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether, PageBreak
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.pdfgen import canvas as pdfcanvas
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
except ImportError:
    print("❌ reportlab not installed. Run: pip install reportlab --break-system-packages")
    sys.exit(1)

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK      = colors.HexColor('#0a0a12')
CARD_DARK  = colors.HexColor('#1e293b')
PAGE_WHITE = colors.HexColor('#ffffff')
CYAN       = colors.HexColor('#22d3ee')
CYAN_DIM   = colors.HexColor('#0e7490')
CYAN_LIGHT = colors.HexColor('#67e8f9')
MUTED      = colors.HexColor('#94a3b8')
RED        = colors.HexColor('#ef4444')
ORANGE     = colors.HexColor('#f97316')
YELLOW     = colors.HexColor('#ca8a04')
BLUE       = colors.HexColor('#3b82f6')
GREEN      = colors.HexColor('#16a34a')
TEXT_DARK  = colors.HexColor('#0f172a')
TEXT_BODY  = colors.HexColor('#334155')
TEXT_MUTED = colors.HexColor('#64748b')
BORDER     = colors.HexColor('#e2e8f0')
ROW_ALT    = colors.HexColor('#f8fafc')
HEADER_BG  = colors.HexColor('#f1f5f9')

SEV_COLORS = {'critical': RED, 'high': ORANGE, 'medium': YELLOW, 'low': BLUE}
SEV_LABELS = {'critical': 'CRITICAL', 'high': 'HIGH', 'medium': 'MEDIUM', 'low': 'LOW'}

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch


# ── Risk score ────────────────────────────────────────────────────────────────

def compute_risk_score(breaches, pastes):
    if not breaches:
        return 5, 'A', 'Minimal Risk'
    score = sum({'critical': 20, 'high': 12, 'medium': 6, 'low': 2}.get(b.get('severity', 'low'), 2) for b in breaches)
    score += len(pastes) * 5
    score = min(score, 100)
    if score >= 75:   return score, 'F', 'Critical Risk'
    elif score >= 55: return score, 'D', 'High Risk'
    elif score >= 35: return score, 'C', 'Moderate Risk'
    elif score >= 15: return score, 'B', 'Low Risk'
    else:             return score, 'A', 'Minimal Risk'


def grade_color(grade):
    return {'A': GREEN, 'B': BLUE, 'C': YELLOW, 'D': ORANGE, 'F': RED}.get(grade, MUTED)


# ── Cover page ────────────────────────────────────────────────────────────────

def draw_cover(c, client_name, email, score, grade, label, total, sev_counts, pastes_count, date_str):
    w, h = PAGE_W, PAGE_H

    # Dark background
    c.setFillColor(BLACK)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Grid
    c.setStrokeColor(colors.HexColor('#1a2234'))
    c.setLineWidth(0.4)
    for x in range(0, int(w) + 48, 48):
        c.line(x, 0, x, h)
    for y in range(0, int(h) + 48, 48):
        c.line(0, y, w, y)

    # Glow
    for r, a in [(280, 0.03), (180, 0.04), (100, 0.03)]:
        c.setFillColor(CYAN)
        c.setFillAlpha(a)
        c.circle(w/2, h/2, r, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    # Top bar
    c.setFillColor(CYAN)
    c.rect(0, h - 3, w, 3, fill=1, stroke=0)

    # Corner accents
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    c.setStrokeAlpha(0.6)
    al = 36
    for pts in [(0,h-3,al,h-3,0,h-3,0,h-3-al),(w,h-3,w-al,h-3,w,h-3,w,h-3-al),
                (0,3,al,3,0,3,0,3+al),(w,3,w-al,3,w,3,w,3+al)]:
        c.line(pts[0],pts[1],pts[2],pts[3])
        c.line(pts[4],pts[5],pts[6],pts[7])
    c.setStrokeAlpha(1.0)

    # Shield
    cx, cy = w/2, h * 0.50
    sw, sh = 80, 95
    c.setFillColor(CARD_DARK)
    c.setStrokeColor(CYAN)
    c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx, cy+sh/2)
    p.lineTo(cx+sw/2, cy+sh*0.3)
    p.lineTo(cx+sw/2, cy-sh*0.08)
    p.curveTo(cx+sw/2, cy-sh*0.42, cx+sw*0.18, cy-sh*0.5, cx, cy-sh/2)
    p.curveTo(cx-sw*0.18, cy-sh*0.5, cx-sw/2, cy-sh*0.42, cx-sw/2, cy-sh*0.08)
    p.lineTo(cx-sw/2, cy+sh*0.3)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    c.setFillColor(CYAN)
    c.setStrokeColor(CYAN_LIGHT)
    c.setLineWidth(1.5)
    c.circle(cx, cy, 7, fill=1, stroke=1)
    c.setFillColor(colors.HexColor('#a5f3fc'))
    c.circle(cx, cy, 3.5, fill=1, stroke=0)

    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    for angle in [90 + i*(360/7) for i in range(7)]:
        rad = math.radians(angle)
        er = 26
        c.line(cx+7*math.cos(rad), cy+7*math.sin(rad), cx+er*math.cos(rad), cy+er*math.sin(rad))
        c.setFillColor(CYAN_LIGHT)
        c.circle(cx+er*math.cos(rad), cy+er*math.sin(rad), 3.5, fill=1, stroke=0)

    # Wordmark
    c.setFillColor(colors.HexColor('#f3f4f6'))
    c.setFont('Helvetica-Bold', 26)
    c.drawCentredString(w/2, cy-sh/2-44, 'FINK')
    c.setFillColor(CYAN)
    c.drawCentredString(w/2, cy-sh/2-72, 'SECURITY')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, cy-sh/2-90, 'finksecurity.com')

    # Report info — upper area
    iy = h * 0.83
    c.setFillColor(CYAN)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(w/2, iy, 'PERSONAL EXPOSURE REPORT')

    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, iy-22, f'Prepared for: {client_name}')
    c.drawCentredString(w/2, iy-38, email)
    c.drawCentredString(w/2, iy-54, date_str)

    gc = grade_color(grade)
    c.setFillColor(gc)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(w/2, iy-80, f'Risk Grade: {grade} — {label}')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, iy-97,
        f'{total} breach{"es" if total!=1 else ""}  ·  '
        f'{sev_counts.get("critical",0)} critical  ·  '
        f'{sev_counts.get("high",0)} high')

    c.setStrokeColor(CYAN_DIM)
    c.setLineWidth(0.5)
    c.setStrokeAlpha(0.35)
    c.line(MARGIN, iy+14, w-MARGIN, iy+14)
    c.line(MARGIN, iy-110, w-MARGIN, iy-110)
    c.setStrokeAlpha(1.0)

    c.setFillColor(colors.HexColor('#475569'))
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(w/2, 0.85*inch, 'CONFIDENTIAL — PREPARED FOR AUTHORIZED RECIPIENT ONLY')
    c.drawCentredString(w/2, 0.65*inch, f'Generated by ESTHER · Autonomous Security Agent · {date_str}')

    c.showPage()


# ── Body page template ────────────────────────────────────────────────────────

class ReportDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        frame = Frame(MARGIN, 0.5*inch, PAGE_W-2*MARGIN, PAGE_H-1.1*inch,
                      id='body', leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='Body', frames=[frame], onPage=self._page)])

    def _page(self, c, doc):
        w, h = PAGE_W, PAGE_H

        # White background — prevents cover bleed
        c.setFillColor(PAGE_WHITE)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Header
        c.setFillColor(CARD_DARK)
        c.rect(0, h-34, w, 34, fill=1, stroke=0)
        c.setFillColor(CYAN)
        c.rect(0, h-2, w, 2, fill=1, stroke=0)
        c.setFillColor(CYAN)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(MARGIN, h-21, 'FINK SECURITY')
        c.setFillColor(MUTED)
        c.setFont('Helvetica', 8)
        c.drawRightString(w-MARGIN, h-21, 'Personal Exposure Report — CONFIDENTIAL')

        # Footer
        c.setFillColor(HEADER_BG)
        c.rect(0, 0, w, 26, fill=1, stroke=0)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(0, 26, w, 26)
        c.setFillColor(TEXT_MUTED)
        c.setFont('Helvetica', 7.5)
        c.drawString(MARGIN, 8, 'finksecurity.com  ·  Powered by ESTHER')
        c.drawRightString(w-MARGIN, 8, f'Page {doc.page - 1}')


# ── Styles ────────────────────────────────────────────────────────────────────

def build_styles():
    return {
        'section': ParagraphStyle('section', fontSize=13, fontName='Helvetica-Bold',
            textColor=CYAN_DIM, spaceBefore=18, spaceAfter=6),
        'body': ParagraphStyle('body', fontSize=10, fontName='Helvetica',
            textColor=TEXT_BODY, spaceAfter=6, leading=16),
        'muted': ParagraphStyle('muted', fontSize=9, fontName='Helvetica',
            textColor=TEXT_MUTED, spaceAfter=4, leading=13),
        'breach_title': ParagraphStyle('breach_title', fontSize=11, fontName='Helvetica-Bold',
            textColor=TEXT_DARK, spaceAfter=3, spaceBefore=4),
        'rec_title': ParagraphStyle('rec_title', fontSize=10, fontName='Helvetica-Bold',
            textColor=CYAN_DIM, spaceAfter=2),
        'rec_body': ParagraphStyle('rec_body', fontSize=10, fontName='Helvetica',
            textColor=TEXT_BODY, spaceAfter=10, leading=15, leftIndent=12),
        'footer': ParagraphStyle('footer', fontSize=8, fontName='Helvetica',
            textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=2),
    }


# ── Tables ────────────────────────────────────────────────────────────────────

def build_risk_block(score, grade, label, total, sev_counts, pastes_count):
    gc = grade_color(grade)
    ps = lambda txt, align=TA_LEFT, size=10, color=TEXT_BODY, bold=False: Paragraph(
        txt, ParagraphStyle('p', fontSize=size, fontName='Helvetica-Bold' if bold else 'Helvetica',
        textColor=color, alignment=align))

    grade_cell = ps(f'<font size="34" color="{gc.hexval()}"><b>{grade}</b></font>', align=TA_CENTER)
    info_cell = Table([
        [ps(f'<font size="9" color="{CYAN_DIM.hexval()}"><b>EXPOSURE RISK SCORE</b></font>')],
        [ps(f'<font size="17" color="{gc.hexval()}"><b>{label}</b></font>')],
        [ps(f'<font size="9" color="{TEXT_MUTED.hexval()}">{score}/100  ·  {total} breach{"es" if total!=1 else ""}  ·  {pastes_count} paste{"s" if pastes_count!=1 else ""}</font>')],
    ], colWidths=[3.5*inch])
    counts_cell = Table([
        [ps(f'<font size="7" color="{RED.hexval()}"><b>CRITICAL</b></font>', align=TA_CENTER),
         ps(f'<font size="7" color="{ORANGE.hexval()}"><b>HIGH</b></font>', align=TA_CENTER),
         ps(f'<font size="7" color="{YELLOW.hexval()}"><b>MEDIUM</b></font>', align=TA_CENTER),
         ps(f'<font size="7" color="{BLUE.hexval()}"><b>LOW</b></font>', align=TA_CENTER)],
        [ps(f'<font size="20" color="{RED.hexval()}"><b>{sev_counts.get("critical",0)}</b></font>', align=TA_CENTER),
         ps(f'<font size="20" color="{ORANGE.hexval()}"><b>{sev_counts.get("high",0)}</b></font>', align=TA_CENTER),
         ps(f'<font size="20" color="{YELLOW.hexval()}"><b>{sev_counts.get("medium",0)}</b></font>', align=TA_CENTER),
         ps(f'<font size="20" color="{BLUE.hexval()}"><b>{sev_counts.get("low",0)}</b></font>', align=TA_CENTER)],
    ], colWidths=[0.92*inch, 0.65*inch, 0.85*inch, 0.58*inch])

    outer = Table([[grade_cell, info_cell, counts_cell]], colWidths=[0.65*inch, 3.5*inch, 3.0*inch])
    outer.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CARD_DARK),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 14),
        ('LEFTPADDING',   (0,0),(0,0),   18),
        ('LEFTPADDING',   (1,0),(1,0),   10),
        ('LINEBELOW',     (0,0),(-1,-1), 2, CYAN),
        ('LINEBEFORE',    (2,0),(2,0),   0.5, CYAN_DIM),
    ]))
    return outer


def build_breach_table(breach):
    sev   = breach.get('severity', 'low')
    color = SEV_COLORS.get(sev, BLUE)
    label = SEV_LABELS.get(sev, sev.upper())
    col_w = [1.5*inch, PAGE_W-2*MARGIN-1.5*inch]

    def c(txt, bold=False, clr=TEXT_BODY):
        return Paragraph(txt, ParagraphStyle('c', fontSize=9,
            fontName='Helvetica-Bold' if bold else 'Helvetica', textColor=clr, leading=13))

    data = [
        [c('Severity', bold=True, clr=TEXT_MUTED), c(label, bold=True, clr=color)],
        [c('Breach date', clr=TEXT_MUTED), c(breach.get('breach_date', 'Unknown'))],
        [c('Records exposed', clr=TEXT_MUTED), c(f'{breach.get("pwn_count",0):,}')],
        [c('Data exposed', clr=TEXT_MUTED), c(', '.join(breach.get('data_classes', [])[:6]))],
        [c('Domain', clr=TEXT_MUTED), c(breach.get('domain') or 'N/A')],
        [c('Verified', clr=TEXT_MUTED), c('Yes' if breach.get('is_verified') else 'No — unverified aggregate')],
    ]
    t = Table(data, colWidths=col_w)
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [PAGE_WHITE, ROW_ALT]),
        ('GRID',          (0,0),(-1,-1), 0.3, BORDER),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
    ]))
    return t


def build_priority_actions(breaches, pastes):
    classes  = {dc for b in breaches for dc in b.get('data_classes', [])}
    sevs     = {b['severity'] for b in breaches}
    critical = [b for b in breaches if b.get('severity') == 'critical']
    recent   = [b for b in breaches if b.get('breach_date', '') >= '2022-01-01']
    actions  = []

    if 'Passwords' in classes or 'critical' in sevs:
        names = ', '.join([b.get('title', b.get('name', '')) for b in critical[:3]])
        actions.append(('IMMEDIATE — Change compromised passwords',
            f'Your password was exposed in: {names}. Change these passwords now and on any site '
            'where you reused them. Use a password manager (Bitwarden is free) to generate '
            'unique passwords for every account.'))

    actions.append(('IMMEDIATE — Enable two-factor authentication',
        'Enable 2FA on your email, banking, and social media accounts. Use an authenticator app '
        '(Google Authenticator, Authy) rather than SMS. This stops attackers even if they have your password.'))

    if any(c in classes for c in ['Credit cards', 'Partial credit card data', 'Bank account numbers']):
        actions.append(('URGENT — Monitor financial accounts',
            'Your financial data was exposed. Check your bank and credit card statements for unauthorized '
            'charges. Consider a free credit freeze at Equifax, Experian, and TransUnion.'))

    if recent:
        actions.append((f'THIS WEEK — Check for account takeovers',
            f'You have {len(recent)} breach(es) from 2022 or later. Log into your important accounts '
            'and check for unrecognized logins, devices, or email forwarding rules you did not set up.'))

    if pastes:
        actions.append(('THIS WEEK — Your credentials are on paste sites',
            f'Your email appeared in {len(pastes)} paste site(s) — locations where attackers share stolen '
            'credential lists. Change passwords on any account using exposed credentials.'))

    if len(breaches) > 6:
        actions.append(('ONGOING — Use email aliases',
            'With this many breaches, use a unique email alias for each service (SimpleLogin or Apple Hide '
            'My Email). This limits future exposure and identifies which service leaked your data.'))

    actions.append(('ONGOING — Monitor for future breaches',
        'Sign up for free breach alerts at haveibeenpwned.com. Consider Fink Security continuous monitoring '
        'for automated alerts and monthly reports — visit finksecurity.com.'))

    return actions


# ── Main PDF generator ────────────────────────────────────────────────────────

def generate_pdf(client_name, email, hibp_data, out_path):
    breaches   = hibp_data.get('breaches', [])
    pastes     = hibp_data.get('pastes', [])
    summary    = hibp_data.get('summary', {})
    sev_counts = summary.get('severity', {})
    total      = summary.get('total_breaches', len(breaches))
    score, grade, label = compute_risk_score(breaches, pastes)
    now        = datetime.now(timezone.utc).strftime('%B %d, %Y')
    styles     = build_styles()

    tmp_cover = str(out_path) + '.cover.pdf'
    tmp_body  = str(out_path) + '.body.pdf'

    # Cover
    cv = pdfcanvas.Canvas(tmp_cover, pagesize=letter)
    draw_cover(cv, client_name, email, score, grade, label, total, sev_counts, len(pastes), now)
    cv.save()

    # Body
    doc = ReportDoc(tmp_body, pagesize=letter,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=0.5*inch, bottomMargin=0.5*inch,
        title=f'Personal Exposure Report — {client_name}',
        author='Fink Security / ESTHER')

    story = []

    story.append(Paragraph('Risk Assessment', styles['section']))
    story.append(Spacer(1, 0.06*inch))
    story.append(build_risk_block(score, grade, label, total, sev_counts, len(pastes)))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph('Executive Summary', styles['section']))
    if total == 0:
        stxt = (f'Good news — no breach data was found for <b>{email}</b>. '
                'Your email has not appeared in any known data breaches. '
                'Continue using strong passwords and monitoring for future exposure.')
    else:
        crit = sev_counts.get('critical', 0)
        high = sev_counts.get('high', 0)
        intro = 'requires immediate attention' if crit > 0 else 'warrants your attention'
        stxt = (f'Your email address <b>{email}</b> has appeared in <b>{total} data '
                f'breach{"es" if total!=1 else ""}</b> and {intro}. '
                f'{"There are <b>"+str(crit)+" critical severity</b> breaches involving your passwords. " if crit else ""}'
                f'{"There are <b>"+str(high)+" high severity</b> breaches. " if high else ""}'
                'Review the breach details and priority actions below.')
    story.append(Paragraph(stxt, styles['body']))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph('Priority Actions', styles['section']))
    story.append(Paragraph('These actions are specific to your breach profile, ordered by urgency.', styles['muted']))
    story.append(Spacer(1, 0.08*inch))
    for i, (title, body) in enumerate(build_priority_actions(breaches, pastes), 1):
        story.append(KeepTogether([
            Paragraph(f'{i}. {title}', styles['rec_title']),
            Paragraph(body, styles['rec_body']),
        ]))

    if breaches:
        story.append(Paragraph('Breach Details', styles['section']))
        story.append(Paragraph(
            "Entries marked 'unverified' come from credential lists aggregated from multiple sources.",
            styles['muted']))
        story.append(Spacer(1, 0.08*inch))
        for sev in ['critical', 'high', 'medium', 'low']:
            for b in [x for x in breaches if x.get('severity') == sev]:
                story.append(KeepTogether([
                    Paragraph(b.get('title', b.get('name', 'Unknown')), styles['breach_title']),
                    build_breach_table(b),
                    Spacer(1, 0.14*inch),
                ]))

    if pastes:
        story.append(Paragraph('Paste Site Appearances', styles['section']))
        story.append(Paragraph(
            f'Your email was found in {len(pastes)} paste site(s) — public posts '
            'where attackers share stolen credential lists.', styles['body']))
        paste_data = [['Source', 'Date', 'Title']] + [
            [p.get('Source', 'Unknown'), (p.get('Date') or 'Unknown')[:10], (p.get('Title') or 'Untitled')[:55]]
            for p in pastes[:10]]
        pt = Table(paste_data, colWidths=[1.2*inch, 1*inch, PAGE_W-2*MARGIN-2.2*inch])
        pt.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0),  HEADER_BG),
            ('TEXTCOLOR',     (0,0),(-1,0),  CYAN_DIM),
            ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0,0),(-1,-1), 9),
            ('TEXTCOLOR',     (0,1),(-1,-1), TEXT_BODY),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [PAGE_WHITE, ROW_ALT]),
            ('GRID',          (0,0),(-1,-1), 0.3, BORDER),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ]))
        story.append(pt)
        story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph('What This Means', styles['section']))
    story.append(Paragraph(
        'Data breaches occur when attackers compromise a company\'s database and steal user records. '
        'Once in a breach, your data is typically sold on dark web markets and used in '
        '<b>credential stuffing attacks</b> — automated tools that try your email and password '
        'across thousands of websites simultaneously.', styles['body']))
    story.append(Paragraph(
        '<b>Old breaches are still dangerous.</b> Attackers combine multiple breach databases to build '
        'comprehensive profiles. A 2014 breach combined with a 2020 breach gives attackers more '
        'information than either alone.', styles['body']))
    story.append(Paragraph(
        '<b>Unverified breaches still matter.</b> Unverified entries contain real credentials '
        'actively used in attacks, even if the original source cannot be confirmed.', styles['body']))

    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=8))
    story.append(Paragraph(
        'Report generated by ESTHER, Fink Security\'s autonomous security agent. '
        'Breach data sourced from Have I Been Pwned (haveibeenpwned.com). '
        'For continuous monitoring and additional services, visit finksecurity.com.',
        styles['muted']))
    story.append(Paragraph(
        f'© {datetime.now().year} Fink Security · Confidential · finksecurity.com',
        styles['footer']))

    doc.build(story)

    # Merge cover + body
    try:
        from pypdf import PdfWriter, PdfReader
        writer = PdfWriter()
        for pdf in [tmp_cover, tmp_body]:
            for page in PdfReader(pdf).pages:
                writer.add_page(page)
        with open(str(out_path), 'wb') as f:
            writer.write(f)
        Path(tmp_cover).unlink(missing_ok=True)
        Path(tmp_body).unlink(missing_ok=True)
        print(f'  ✅ Report generated: {out_path}')
    except ImportError:
        import shutil
        shutil.move(tmp_body, str(out_path))
        Path(tmp_cover).unlink(missing_ok=True)
        print(f'  ⚠️  Cover merge skipped (install pypdf). Report: {out_path}')

    return out_path


def main():
    parser = argparse.ArgumentParser(description='Generate Personal Exposure Report PDF')
    parser.add_argument('--email',  required=True)
    parser.add_argument('--name',   required=True)
    parser.add_argument('--hibp',   required=True)
    parser.add_argument('--out',    default='.')
    args = parser.parse_args()

    hibp_path = Path(args.hibp).expanduser()
    if not hibp_path.exists():
        print(f'❌ HIBP JSON not found: {hibp_path}')
        sys.exit(1)

    hibp_data = json.loads(hibp_path.read_text())
    out_dir   = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = args.name.lower().replace(' ', '-')
    out_path  = out_dir / f'exposure-report-{safe_name}-{datetime.now().strftime("%Y-%m-%d")}.pdf'

    print(f'🦂 Generating Personal Exposure Report for {args.name}...')
    generate_pdf(args.name, args.email, hibp_data, out_path)

    total = hibp_data.get('summary', {}).get('total_breaches', 0)
    crit  = hibp_data.get('summary', {}).get('severity', {}).get('critical', 0)
    print(f'   {total} breaches | {crit} critical')
    print(f'   Ready to deliver to client.')


if __name__ == '__main__':
    main()
