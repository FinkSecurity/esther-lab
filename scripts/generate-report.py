#!/usr/bin/env python3
"""
Fink Security — PDF Report Generator
Converts markdown reports to branded PDFs and delivers via Telegram.
Usage: python3 generate-report.py <markdown_file> [--send]
"""

import os
import sys
import subprocess
import datetime
import urllib.request
import urllib.parse
import json

# ── Config ────────────────────────────────────────────────────────────────────
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/reports/pdf")
ENV_FILE   = os.path.expanduser("~/.openclaw/.env")

def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

ENV = load_env()
TELEGRAM_TOKEN   = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = ENV.get("TELEGRAM_CHAT_ID", "")

# ── CSS Template ──────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;700&family=Share+Tech+Mono&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Exo 2', 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1e293b;
    background: white;
    padding: 0;
}

/* Cover page */
.cover {
    page-break-after: always;
    background: #0a0a12;
    color: white;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 80px 60px;
    position: relative;
}

.cover-accent {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: #22d3ee;
}

.cover-logo {
    font-family: 'Exo 2', sans-serif;
    font-weight: 700;
    font-size: 28pt;
    letter-spacing: 0.08em;
    color: white;
    margin-bottom: 60px;
}

.cover-logo span { color: #22d3ee; }

.cover-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 9pt;
    color: #22d3ee;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 16px;
}

.cover-title {
    font-size: 28pt;
    font-weight: 700;
    line-height: 1.2;
    color: white;
    margin-bottom: 40px;
    max-width: 600px;
}

.cover-meta {
    font-family: 'Share Tech Mono', monospace;
    font-size: 9pt;
    color: #94a3b8;
    line-height: 2;
}

.cover-meta strong { color: #22d3ee; }

.cover-confidential {
    position: absolute;
    bottom: 40px; right: 60px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 8pt;
    color: #ef4444;
    letter-spacing: 0.2em;
    border: 1px solid #ef4444;
    padding: 4px 12px;
}

.cover-footer {
    position: absolute;
    bottom: 40px; left: 60px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 8pt;
    color: #475569;
}

/* Content pages */
.content {
    padding: 60px;
    max-width: 800px;
    margin: 0 auto;
}

.page-header {
    border-bottom: 2px solid #22d3ee;
    padding-bottom: 12px;
    margin-bottom: 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.page-header-logo {
    font-family: 'Exo 2', sans-serif;
    font-weight: 700;
    font-size: 12pt;
    color: #0a0a12;
    letter-spacing: 0.06em;
}

.page-header-logo span { color: #22d3ee; }

.page-header-meta {
    font-family: 'Share Tech Mono', monospace;
    font-size: 8pt;
    color: #94a3b8;
    text-align: right;
}

h1 {
    font-size: 20pt;
    font-weight: 700;
    color: #0a0a12;
    margin: 32px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e2e8f0;
}

h2 {
    font-size: 15pt;
    font-weight: 600;
    color: #0a0a12;
    margin: 28px 0 12px;
}

h3 {
    font-size: 12pt;
    font-weight: 600;
    color: #22d3ee;
    margin: 20px 0 8px;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 0.05em;
}

p { margin-bottom: 14px; color: #334155; }

code {
    font-family: 'Share Tech Mono', monospace;
    font-size: 9.5pt;
    background: #f1f5f9;
    color: #0e7490;
    padding: 2px 6px;
    border-radius: 3px;
}

pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 20px 24px;
    margin: 16px 0;
    border-left: 3px solid #22d3ee;
    overflow-x: auto;
    font-family: 'Share Tech Mono', monospace;
    font-size: 9pt;
    line-height: 1.6;
}

pre code {
    background: none;
    color: #e2e8f0;
    padding: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10pt;
}

th {
    background: #0a0a12;
    color: #22d3ee;
    font-family: 'Share Tech Mono', monospace;
    font-size: 9pt;
    letter-spacing: 0.08em;
    padding: 10px 14px;
    text-align: left;
}

td {
    padding: 10px 14px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
}

tr:nth-child(even) td { background: #f8fafc; }

blockquote {
    border-left: 3px solid #22d3ee;
    padding: 12px 20px;
    margin: 16px 0;
    background: #f0f9ff;
    color: #0e7490;
    font-style: italic;
}

ul, ol {
    padding-left: 24px;
    margin-bottom: 14px;
    color: #334155;
}

li { margin-bottom: 6px; }

.severity-critical { color: #dc2626; font-weight: 700; }
.severity-high     { color: #ea580c; font-weight: 700; }
.severity-medium   { color: #d97706; font-weight: 700; }
.severity-low      { color: #16a34a; font-weight: 700; }

.page-footer {
    position: fixed;
    bottom: 20px; left: 60px; right: 60px;
    border-top: 1px solid #e2e8f0;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    font-family: 'Share Tech Mono', monospace;
    font-size: 8pt;
    color: #94a3b8;
}
"""

# ── HTML Template ─────────────────────────────────────────────────────────────
def build_html(title, content_html, report_id, date_str):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>{CSS}</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover">
  <div class="cover-accent"></div>
  <div class="cover-logo">FINK<span> SECURITY</span></div>
  <div class="cover-label">// Security Research Report</div>
  <div class="cover-title">{title}</div>
  <div class="cover-meta">
    <div><strong>Report ID:</strong> {report_id}</div>
    <div><strong>Date:</strong> {date_str}</div>
    <div><strong>Generated by:</strong> ESTHER — Autonomous AI Security Agent</div>
    <div><strong>Classification:</strong> Confidential</div>
  </div>
  <div class="cover-confidential">CONFIDENTIAL</div>
  <div class="cover-footer">finksecurity.com · estherops.tech</div>
</div>

<!-- CONTENT -->
<div class="content">
  <div class="page-header">
    <div class="page-header-logo">FINK<span> SECURITY</span></div>
    <div class="page-header-meta">{report_id}<br>{date_str}</div>
  </div>

  {content_html}

  <div class="page-footer">
    <span>FINK SECURITY — finksecurity.com</span>
    <span>CONFIDENTIAL — {date_str}</span>
  </div>
</div>

</body>
</html>"""

# ── Core Functions ────────────────────────────────────────────────────────────
def markdown_to_html(md_file):
    """Convert markdown to HTML using pandoc."""
    result = subprocess.run(
        ["pandoc", md_file, "-t", "html", "--no-highlight"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Pandoc error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def html_to_pdf(html_content, output_path):
    """Convert HTML to PDF using pandoc with HTML engine."""
    # Write temp HTML file
    tmp_html = "/tmp/fink-report-tmp.html"
    with open(tmp_html, 'w') as f:
        f.write(html_content)

    result = subprocess.run(
        ["pandoc", tmp_html, "-o", output_path,
         "--pdf-engine=weasyprint",
         "--metadata", "title=Fink Security Report"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        # Fallback to wkhtmltopdf style via chromium headless
        result2 = subprocess.run(
            ["chromium", "--headless", "--no-sandbox",
             "--print-to-pdf=" + output_path,
             "--print-to-pdf-no-header",
             "file://" + tmp_html],
            capture_output=True, text=True
        )
        if result2.returncode != 0:
            print(f"PDF generation failed: {result2.stderr}")
            sys.exit(1)

    return output_path

def extract_title(md_file):
    """Extract title from markdown frontmatter or first heading."""
    with open(md_file) as f:
        lines = f.readlines()

    # Check frontmatter
    if lines[0].strip() == '---':
        for line in lines[1:]:
            if line.startswith('title:'):
                return line.split(':', 1)[1].strip().strip('"\'')
            if line.strip() == '---':
                break

    # Fall back to first heading
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()

    return os.path.basename(md_file).replace('.md', '')

def send_telegram(pdf_path, title):
    """Send PDF via Telegram bot."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram not configured — PDF saved locally only")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"

    caption = f"📄 *Fink Security Report*\n_{title}_\nGenerated by ESTHER"

    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    import base64, urllib.request
    boundary = "----FormBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{TELEGRAM_CHAT_ID}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'
        f"Markdown\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="{os.path.basename(pdf_path)}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            if result.get('ok'):
                print(f"✅ PDF sent to Telegram")
                return True
    except Exception as e:
        print(f"❌ Telegram delivery failed: {e}")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-report.py <markdown_file> [--send]")
        sys.exit(1)

    md_file = sys.argv[1]
    send = "--send" in sys.argv

    if not os.path.exists(md_file):
        print(f"File not found: {md_file}")
        sys.exit(1)

    # Setup
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    title = extract_title(md_file)
    basename = os.path.splitext(os.path.basename(md_file))[0]
    report_id = f"FSR-{date_str}-{basename[:8].upper()}"
    output_path = os.path.join(OUTPUT_DIR, f"{basename}-{date_str}.pdf")

    print(f"📄 Generating: {title}")
    print(f"   Report ID: {report_id}")

    # Convert
    content_html = markdown_to_html(md_file)
    full_html = build_html(title, content_html, report_id, date_str)
    html_to_pdf(full_html, output_path)

    print(f"✅ PDF saved: {output_path}")
    print(f"   Size: {os.path.getsize(output_path):,} bytes")

    # Send
    if send:
        send_telegram(output_path, title)
    else:
        print(f"💡 Add --send flag to deliver via Telegram")

if __name__ == "__main__":
    main()
