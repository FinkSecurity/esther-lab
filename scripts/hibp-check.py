#!/usr/bin/env python3
"""
hibp-check.py — Have I Been Pwned breach lookup for Fink Security
Used by ESTHER for Personal Exposure Report and Breach & Credential Check services.

Usage:
    python3 hibp-check.py <email>
    python3 hibp-check.py <email> --json
    python3 hibp-check.py <email> --out ~/report-output/

Environment:
    HIBP_API_KEY — required

API docs: https://haveibeenpwned.com/API/v3
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime, timezone
from pathlib import Path

HIBP_API_KEY = os.environ.get('HIBP_API_KEY')
HIBP_BASE    = 'https://haveibeenpwned.com/api/v3'
HEADERS      = {
    'hibp-api-key': HIBP_API_KEY or '',
    'user-agent':   'FinkSecurity-ESTHER/1.0',
}

SEVERITY_MAP = {
    'critical': [
        'Passwords', 'CreditCards', 'BankAccountNumbers', 'SSNs',
        'Passport numbers', 'Private messages', 'Security questions and answers',
    ],
    'high': [
        'PartialCreditCardData', 'Partial credit card data',
        'PhoneNumbers', 'Phone numbers',
        'PhysicalAddresses', 'Physical addresses',
        'HealthInsurance', 'Health insurance',
        'Financial transactions', 'Net worths', 'Salaries',
        'Government issued IDs', 'Drivers licences',
    ],
    'medium': [
        'EmailAddresses', 'Email addresses',
        'Names', 'Usernames', 'DateOfBirth', 'Dates of birth',
        'GeoLocation', 'Geographic locations',
        'IPAddresses', 'IP addresses',
        'Device information', 'Social media profiles',
        'Browser user agent details',
    ],
    'low': [
        'Genders', 'Employers', 'MaritalStatuses', 'Education',
        'Job titles', 'Ages', 'Nationalities', 'Time zones',
        'Spoken languages', 'Website activity',
    ],
}

def severity_for_breach(data_classes: list[str]) -> str:
    for sev, classes in SEVERITY_MAP.items():
        if any(dc in classes for dc in data_classes):
            return sev
    return 'low'

def get_breaches(email: str) -> list[dict]:
    if not HIBP_API_KEY:
        print("❌ HIBP_API_KEY not set. Run: export HIBP_API_KEY=your_key")
        sys.exit(1)

    url = f"{HIBP_BASE}/breachedaccount/{email}?truncateResponse=false"
    r   = requests.get(url, headers=HEADERS, timeout=15)

    if r.status_code == 404:
        return []
    if r.status_code == 401:
        print("❌ HIBP API key invalid or missing.")
        sys.exit(1)
    if r.status_code == 429:
        print("⚠️  HIBP rate limited — waiting 6 seconds...")
        time.sleep(6)
        return get_breaches(email)
    if r.status_code != 200:
        print(f"❌ HIBP API error {r.status_code}: {r.text[:200]}")
        sys.exit(1)

    return r.json()

def get_pastes(email: str) -> list[dict]:
    url = f"{HIBP_BASE}/pasteaccount/{email}"
    r   = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 404:
        return []
    if r.status_code != 200:
        return []
    return r.json()

def format_breach(breach: dict) -> dict:
    data_classes = breach.get('DataClasses', [])
    return {
        'name':         breach.get('Name', ''),
        'title':        breach.get('Title', ''),
        'domain':       breach.get('Domain', ''),
        'breach_date':  breach.get('BreachDate', ''),
        'added_date':   breach.get('AddedDate', '')[:10] if breach.get('AddedDate') else '',
        'pwn_count':    breach.get('PwnCount', 0),
        'data_classes': data_classes,
        'severity':     severity_for_breach(data_classes),
        'is_verified':  breach.get('IsVerified', False),
        'is_sensitive': breach.get('IsSensitive', False),
        'description':  breach.get('Description', ''),
    }

def print_report(email: str, breaches: list[dict], pastes: list[dict]):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    sev_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for b in breaches:
        sev_counts[b['severity']] += 1

    print(f"\n{'='*60}")
    print(f"  HIBP Breach Report — Fink Security")
    print(f"  Email:     {email}")
    print(f"  Generated: {now}")
    print(f"{'='*60}")
    print(f"\n  Breaches found: {len(breaches)}")
    print(f"  Pastes found:   {len(pastes)}")
    print(f"\n  Severity breakdown:")
    print(f"    🔴 Critical: {sev_counts['critical']}")
    print(f"    🟠 High:     {sev_counts['high']}")
    print(f"    🟡 Medium:   {sev_counts['medium']}")
    print(f"    🔵 Low:      {sev_counts['low']}")

    if breaches:
        print(f"\n  {'─'*56}")
        print(f"  BREACH DETAILS")
        print(f"  {'─'*56}")
        for sev in ['critical', 'high', 'medium', 'low']:
            sev_breaches = [b for b in breaches if b['severity'] == sev]
            if not sev_breaches:
                continue
            icons = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}
            for b in sev_breaches:
                print(f"\n  {icons[sev]} {b['title']} ({b['breach_date']})")
                print(f"     Domain:      {b['domain'] or 'N/A'}")
                print(f"     Records:     {b['pwn_count']:,}")
                print(f"     Exposed:     {', '.join(b['data_classes'][:5])}")
                if b['is_sensitive']:
                    print(f"     ⚠️  SENSITIVE breach")
                if not b['is_verified']:
                    print(f"     ℹ️  Unverified")

    if pastes:
        print(f"\n  {'─'*56}")
        print(f"  PASTE SITES ({len(pastes)} found)")
        print(f"  {'─'*56}")
        for p in pastes[:5]:
            source = p.get('Source', 'Unknown')
            date   = p.get('Date', 'Unknown')[:10] if p.get('Date') else 'Unknown'
            title  = p.get('Title', 'Untitled') or 'Untitled'
            print(f"\n  • {source} — {date}")
            print(f"    {title[:80]}")
        if len(pastes) > 5:
            print(f"\n  ... and {len(pastes)-5} more pastes")

    print(f"\n{'='*60}\n")

def save_json(email: str, breaches: list[dict], pastes: list[dict], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_email = email.replace('@', '_at_').replace('.', '_')
    out_path   = out_dir / f"hibp-{safe_email}.json"
    data = {
        'email':      email,
        'generated':  datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_breaches': len(breaches),
            'total_pastes':   len(pastes),
            'severity': {
                sev: sum(1 for b in breaches if b['severity'] == sev)
                for sev in ['critical', 'high', 'medium', 'low']
            }
        },
        'breaches': breaches,
        'pastes':   pastes,
    }
    out_path.write_text(json.dumps(data, indent=2))
    print(f"  JSON saved: {out_path}")
    return out_path

def main():
    parser = argparse.ArgumentParser(description='HIBP breach check for Fink Security')
    parser.add_argument('email',       help='Email address to check')
    parser.add_argument('--json',      action='store_true', help='Output raw JSON')
    parser.add_argument('--out',       default=None, help='Save JSON to directory')
    parser.add_argument('--no-pastes', action='store_true', help='Skip paste lookup')
    args = parser.parse_args()

    print(f"🦂 Checking {args.email} against HIBP...")

    breaches_raw = get_breaches(args.email)
    breaches     = [format_breach(b) for b in breaches_raw]

    pastes = []
    if not args.no_pastes:
        time.sleep(1.5)  # HIBP rate limit courtesy pause
        pastes = get_pastes(args.email)

    if args.json:
        print(json.dumps({
            'email': args.email,
            'breaches': breaches,
            'pastes': pastes
        }, indent=2))
        return

    print_report(args.email, breaches, pastes)

    if args.out:
        save_json(args.email, breaches, pastes, Path(args.out).expanduser())


if __name__ == '__main__':
    main()
