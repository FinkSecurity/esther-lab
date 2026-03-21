#!/usr/bin/env python3
"""
generate-h1-report.py — ESTHER HackerOne Submission Draft Generator
Reads findings from engagements/public/<handle>/findings/ and generates
structured HackerOne submission drafts ready for Operator review.

Usage:
    python3 generate-h1-report.py <program_handle>
    python3 generate-h1-report.py x
    python3 generate-h1-report.py playtika

Writes:
    ~/esther-lab/engagements/public/<handle>/submissions/DRAFT-<slug>.md
    ~/esther-lab/engagements/public/<handle>/submissions/FINDINGS-SUMMARY.md
"""

import sys
import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
HOME        = Path.home()
ESTHER_LAB  = HOME / 'esther-lab'
ENGAGEMENTS = ESTHER_LAB / 'engagements' / 'public'
WORKSPACE   = HOME / '.openclaw' / 'workspace'
SCOPE_CACHE = WORKSPACE / 'SCOPE-CACHE.json'

# ── Severity definitions ───────────────────────────────────────────────────────
SEVERITY_CVSS = {
    'critical': '9.0-10.0',
    'high':     '7.0-8.9',
    'medium':   '4.0-6.9',
    'low':      '0.1-3.9',
    'info':     'N/A',
}

# Keywords that must appear in a severity-declaring context to count.
# These are matched only within explicit severity/finding declaration lines,
# not anywhere in the document (prevents recon notes from triggering).
SEVERITY_DECLARED_PATTERNS = [
    # Explicit severity declarations ESTHER should write in finding files
    (r'(?:severity|rating|cvss)[:\s]+critical',    'critical'),
    (r'(?:severity|rating|cvss)[:\s]+high',        'high'),
    (r'(?:severity|rating|cvss)[:\s]+medium',      'medium'),
    (r'(?:severity|rating|cvss)[:\s]+low',         'low'),
    (r'cvss.*?(?:score)?[:\s]+(?:9\.|10\.)',       'critical'),
    (r'cvss.*?(?:score)?[:\s]+[78]\.',             'high'),
    (r'cvss.*?(?:score)?[:\s]+[456]\.',            'medium'),
    (r'cvss.*?(?:score)?[:\s]+[123]\.',            'low'),
]

# Vulnerability class keywords — strong signal regardless of context
# These are specific enough that a false positive is unlikely
VULN_CLASS_KEYWORDS = {
    'critical': [
        'remote code execution', 'unauthenticated rce', 'sql injection',
        'authentication bypass', 'unauthenticated admin access',
        'full account takeover', 'arbitrary code execution',
    ],
    'high': [
        'server-side request forgery', 'ssrf', 'insecure direct object',
        'idor', 'xml external entity', 'xxe', 'privilege escalation',
        'exposed credentials', 'hardcoded secret', 'api key exposed',
        'leaked token', 'path traversal',
    ],
    'medium': [
        'cross-origin resource sharing misconfiguration', 'cors misconfiguration',
        'open redirect', 'subdomain takeover', 'reflected xss',
        'stored xss', 'csrf', 'clickjacking',
    ],
    'low': [
        'version disclosure', 'missing security header', 'directory listing',
        'error message disclosure', 'weak cipher',
    ],
}

# File patterns that indicate recon/notes files, not discrete findings
RECON_FILE_PATTERNS = [
    r'reconnaissance',
    r'recon',
    r'phase[-\s]\d+',
    r'investigation[-\s]notes',
    r'osint',
    r'enumeration',
    r'probing',
    r'fingerprint',
]


def is_recon_notes(content: str, filename: str) -> bool:
    """Return True if this file looks like recon notes rather than a discrete finding."""
    combined = (filename + ' ' + content[:500]).lower()
    for pattern in RECON_FILE_PATTERNS:
        if re.search(pattern, combined):
            return True
    return False


def detect_severity(content: str) -> str:
    """
    Detect severity from finding content using two-pass approach:
    1. Look for explicit severity declarations (most reliable)
    2. Look for specific vulnerability class keywords
    Never fires on generic words like 'critical' used descriptively.
    """
    content_lower = content.lower()

    # Pass 1: explicit severity declarations
    for pattern, severity in SEVERITY_DECLARED_PATTERNS:
        if re.search(pattern, content_lower):
            return severity

    # Pass 2: specific vulnerability class keywords
    for severity in ['critical', 'high', 'medium', 'low']:
        for kw in VULN_CLASS_KEYWORDS[severity]:
            if kw in content_lower:
                return severity

    return 'info'


def extract_title(content: str, filename: str) -> str:
    """Extract or infer a title from the finding."""
    # Try H1 heading
    m = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Try H2
    m = re.search(r'^##\s+(.+)', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Fall back to filename
    return filename.replace('-', ' ').replace('_', ' ').replace('.md', '').title()


def extract_evidence(content: str) -> str:
    """Extract code blocks or evidence sections from content."""
    blocks = re.findall(r'```[\s\S]*?```', content)
    if blocks:
        return '\n\n'.join(blocks[:3])  # max 3 code blocks
    # Try to find evidence section
    m = re.search(r'(?:evidence|proof|output|response)[:\s]*\n([\s\S]{50,500})',
                  content, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return '_(No evidence block found — Operator must add reproduction steps)_'


def extract_target(content: str) -> str:
    """Extract target URL or asset from content."""
    # Look for URLs
    m = re.search(r'https?://[^\s\)]+', content)
    if m:
        return m.group(0)
    # Look for domain patterns
    m = re.search(r'`([a-z0-9\-\.]+\.[a-z]{2,}[^\`]*)`', content)
    if m:
        return m.group(1)
    return '_(target not identified — add manually)_'


def slugify(title: str) -> str:
    """Convert title to filename slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s\-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = slug[:60]
    return slug


def is_reportable(content: str, severity: str, filename: str) -> bool:
    """Determine if a finding is likely reportable."""
    if severity == 'info':
        return False
    # Skip recon notes files — these are investigation logs not discrete findings
    if is_recon_notes(content, filename):
        return False
    # Skip null result files
    null_indicators = [
        'null result', 'nxdomain', 'no finding', 'not reportable',
        'empty response', '422', 'blocked by', 'cloudflare challenge',
        'all blocked', 'no commits found'
    ]
    content_lower = content.lower()
    null_count = sum(1 for i in null_indicators if i in content_lower)
    if null_count >= 2:
        return False
    return True


def generate_draft(finding_path: Path, handle: str, program_info: dict,
                   severity_override: str = None) -> dict | None:
    """Generate a single H1 draft from a finding file."""
    content = finding_path.read_text(errors='ignore')
    severity = severity_override or detect_severity(content)

    if not is_reportable(content, severity, finding_path.name):
        return None

    title    = extract_title(content, finding_path.name)
    evidence = extract_evidence(content)
    target   = extract_target(content)
    slug     = slugify(title)
    now      = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    platform_url = program_info.get('platform_url',
                   f'https://hackerone.com/{handle}')

    draft = f"""# H1 SUBMISSION DRAFT — OPERATOR REVIEW REQUIRED
<!-- Generated by generate-h1-report.py · {now} -->
<!-- Source: {finding_path.name} -->
<!-- STATUS: DRAFT — do not submit without Operator review -->

---

## Submission Metadata

| Field         | Value |
|---------------|-------|
| Program       | {handle} |
| Platform      | {platform_url} |
| Severity      | **{severity.upper()}** (CVSS {SEVERITY_CVSS[severity]}) |
| Asset / URL   | `{target}` |
| Finding File  | `{finding_path.name}` |
| Generated     | {now} |

---

## Title

```
{title}
```

---

## Vulnerability Summary

_(Operator: review and refine the summary below before submission)_

{content[:800].strip()}

---

## Steps to Reproduce

_(describe the exact request/response sequence that demonstrates the issue)_

OPERATOR REVIEW REQUIRED — add reproduction steps here.

1. Navigate to: `{target}`
2. _(add steps)_
3. Observe: _(describe the vulnerable behavior)_

---

## Evidence

{evidence}

---

## Impact

_(Operator: describe the real-world impact of this vulnerability)_

**Severity:** {severity.upper()}

If exploited, this vulnerability could allow an attacker to:
- _(describe impact)_

---

## Recommended Remediation

_(Operator: add remediation recommendations)_

---

## References

- [OWASP](https://owasp.org)
- [HackerOne Disclosure Guidelines](https://www.hackerone.com/disclosure-guidelines)

---

_This draft was auto-generated by ESTHER. All fields marked OPERATOR REVIEW REQUIRED
must be completed before submission. Do not submit fabricated or unverified findings._
"""
    return {
        'slug':     slug,
        'title':    title,
        'severity': severity,
        'target':   target,
        'draft':    draft,
        'source':   finding_path.name,
    }


def generate_summary(drafts: list, null_count: int, handle: str) -> str:
    """Generate FINDINGS-SUMMARY.md overview."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    severity_counts = {}
    for d in drafts:
        s = d['severity']
        severity_counts[s] = severity_counts.get(s, 0) + 1

    draft_list = '\n'.join(
        f"- **{d['severity'].upper()}** — {d['title']} (`DRAFT-{d['slug']}.md`)"
        for d in sorted(drafts, key=lambda x: ['critical','high','medium','low'].index(x['severity'])
                        if x['severity'] in ['critical','high','medium','low'] else 99)
    ) or '_No reportable findings generated._'

    return f"""# FINDINGS SUMMARY — {handle.upper()}
<!-- Generated by generate-h1-report.py · {now} -->

## Overview

| Metric | Count |
|--------|-------|
| Total findings files | {len(drafts) + null_count} |
| Reportable findings | {len(drafts)} |
| Null / informational | {null_count} |
| Critical | {severity_counts.get('critical', 0)} |
| High | {severity_counts.get('high', 0)} |
| Medium | {severity_counts.get('medium', 0)} |
| Low | {severity_counts.get('low', 0)} |

## Reportable Findings

{draft_list}

## Next Steps

- [ ] Operator reviews each DRAFT-*.md file
- [ ] Add Steps to Reproduce for each finding
- [ ] Verify evidence is real and reproducible
- [ ] Submit via HackerOne — never submit unverified findings

---

_Generated by ESTHER · {now}_
_All drafts require Operator review before submission._
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-h1-report.py <program_handle> [--severity critical|high|medium|low]")
        print("   eg: python3 generate-h1-report.py x")
        print("   eg: python3 generate-h1-report.py x --severity medium")
        sys.exit(1)

    handle = sys.argv[1].lower().strip()

    # Parse optional --severity flag
    severity_override = None
    if '--severity' in sys.argv:
        idx = sys.argv.index('--severity')
        if idx + 1 < len(sys.argv):
            sev = sys.argv[idx + 1].lower()
            if sev in ['critical', 'high', 'medium', 'low', 'info']:
                severity_override = sev
                print(f"  ⚠️  Severity override: {sev.upper()} (applied to all findings)")
            else:
                print(f"  ❌ Invalid severity: {sev}. Use: critical|high|medium|low")
                sys.exit(1)
    engagement_dir = ENGAGEMENTS / handle
    findings_dir   = engagement_dir / 'findings'
    submissions_dir = engagement_dir / 'submissions'

    if not findings_dir.exists():
        print(f"❌ Findings directory not found: {findings_dir}")
        sys.exit(1)

    findings = sorted(findings_dir.glob('*.md'))
    if not findings:
        print(f"❌ No .md findings files in {findings_dir}")
        sys.exit(1)

    # Load program info from scope cache if available
    program_info = {}
    if SCOPE_CACHE.exists():
        try:
            cache = json.loads(SCOPE_CACHE.read_text())
            if cache.get('handle') == handle:
                program_info = cache
        except Exception:
            pass

    print(f"🦂 Generating H1 report drafts for: {handle}")
    print(f"   Scanning {len(findings)} finding(s) in {findings_dir}\n")

    submissions_dir.mkdir(parents=True, exist_ok=True)

    drafts     = []
    null_count = 0

    for finding_path in findings:
        result = generate_draft(finding_path, handle, program_info, severity_override)
        if result is None:
            null_count += 1
            print(f"  ⏭️  Skipped (null/info): {finding_path.name}")
            continue

        draft_path = submissions_dir / f"DRAFT-{result['slug']}.md"
        draft_path.write_text(result['draft'])
        drafts.append(result)
        print(f"  ✅ {result['severity'].upper():<8} {result['title'][:55]}")
        print(f"            → {draft_path.name}")

    # Write summary
    summary_path = submissions_dir / 'FINDINGS-SUMMARY.md'
    summary_path.write_text(generate_summary(drafts, null_count, handle))
    print(f"\n  📋 Summary: {summary_path}")

    print(f"\n{'─'*54}")
    print(f"  {len(drafts)} draft(s) generated, {null_count} skipped")
    print(f"  All drafts require Operator review before submission.")
    print(f"  Path: {submissions_dir}")

    if not drafts:
        print(f"\n  ℹ️  No reportable findings detected in current findings.")
        print(f"     Continue recon or review finding files manually.")


if __name__ == '__main__':
    main()
