#!/usr/bin/env python3
"""
h1-ingest.py — HackerOne Manual Scope Ingestion for ESTHER
Converts a manually downloaded H1 CSV export (+ optional Burp Suite JSON)
into scope.json and scope.md inside the engagement directory.

Usage:
    python3 h1-ingest.py --program <handle> --csv <file.csv> [--burp <file.json>]

Example:
    python3 h1-ingest.py --program syfe --csv ~/scopes.csv --burp ~/burpe.json

Outputs (written to ~/esther-lab/engagements/public/<program>/):
    scope.json  — machine-readable, used by ESTHER's scripts
    scope.md    — human-readable, used by load-scope.py to activate the engagement

Next step after running this:
    python3 load-scope.py <program>
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
HOME        = Path.home()
ENGAGEMENTS = HOME / 'esther-lab' / 'engagements' / 'public'

# ── Asset type mappings ────────────────────────────────────────────────────────
ASSET_CATEGORY = {
    'URL':               'web',
    'WILDCARD':          'web',
    'GOOGLE_PLAY_APP_ID':'android',
    'APPLE_STORE_APP_ID':'ios',
    'CIDR':              'network',
    'IP_ADDRESS':        'network',
    'SOURCE_CODE':       'source_code',
    'HARDWARE':          'hardware',
    'OTHER':             'other',
}

ASSET_LABEL = {
    'URL':               'Web / URL',
    'WILDCARD':          'Wildcard Domain',
    'GOOGLE_PLAY_APP_ID':'Android App',
    'APPLE_STORE_APP_ID':'iOS App',
    'CIDR':              'CIDR Range',
    'IP_ADDRESS':        'IP Address',
    'SOURCE_CODE':       'Source Code',
    'HARDWARE':          'Hardware',
    'OTHER':             'Other',
}

STAGING_KEYWORDS = ['nonprod', 'uat', 'staging', 'dev', 'test']


# ── Parsers ────────────────────────────────────────────────────────────────────

def parse_csv(path: Path) -> list[dict]:
    """Parse H1 CSV export into a list of asset dicts."""
    assets = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            asset_type = row.get('asset_type', '').strip()
            identifier = row['identifier'].strip()
            eligible_bounty  = row.get('eligible_for_bounty', '').lower() == 'true'
            eligible_submit  = row.get('eligible_for_submission', '').lower() == 'true'
            environment = 'staging' if any(k in identifier.lower() for k in STAGING_KEYWORDS) else 'production'

            assets.append({
                'identifier':                identifier,
                'asset_type':                asset_type,
                'category':                  ASSET_CATEGORY.get(asset_type, 'other'),
                'instruction':               row.get('instruction', '').strip(),
                'eligible_for_bounty':       eligible_bounty,
                'eligible_for_submission':   eligible_submit,
                'max_severity':              row.get('max_severity', '').strip(),
                'availability_requirement':  row.get('availability_requirement', '').strip(),
                'confidentiality_requirement': row.get('confidentiality_requirement', '').strip(),
                'integrity_requirement':     row.get('integrity_requirement', '').strip(),
                'environment':               environment,
            })
    return assets


def parse_burp(path: Path) -> dict:
    """Extract include/exclude host lists from a Burp Suite project config JSON."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    scope = data.get('target', {}).get('scope', {})
    include_hosts = []
    exclude_hosts = []

    for entry in scope.get('include', []):
        raw = entry.get('host', '')
        clean = re.sub(r'^\^|\\|\$$', '', raw).replace('\\.', '.')
        include_hosts.append({
            'host':     clean,
            'protocol': entry.get('protocol', ''),
            'port':     entry.get('port', ''),
        })

    for entry in scope.get('exclude', []):
        raw = entry.get('host', '')
        clean = re.sub(r'^\^|\\|\$$', '', raw).replace('\\.', '.')
        exclude_hosts.append(clean)

    return {'include': include_hosts, 'exclude': exclude_hosts}


# ── Writers ────────────────────────────────────────────────────────────────────

def write_scope_json(assets: list[dict], burp: dict | None, program: str, out_path: Path):
    """Write machine-readable scope.json."""
    in_scope    = [a for a in assets if a['eligible_for_submission']]
    out_of_scope = [a for a in assets if not a['eligible_for_submission']]

    output = {
        'meta': {
            'program':           program,
            'generated_at':      datetime.now(timezone.utc).isoformat(),
            'source':            'HackerOne CSV export (manual download)',
            'total_assets':      len(assets),
            'in_scope_count':    len(in_scope),
            'out_of_scope_count':len(out_of_scope),
        },
        'summary': {
            'bounty_eligible':   [a['identifier'] for a in in_scope if a['eligible_for_bounty']],
            'staging_targets':   [a['identifier'] for a in in_scope if a['environment'] == 'staging'],
            'production_targets':[a['identifier'] for a in in_scope if a['environment'] == 'production'],
            'web_count':         sum(1 for a in in_scope if a['category'] == 'web'),
            'mobile_count':      sum(1 for a in in_scope if a['category'] in ('android', 'ios')),
        },
        'in_scope':    in_scope,
        'out_of_scope': out_of_scope,
    }

    if burp:
        output['burp_validation'] = burp

    out_path.write_text(json.dumps(output, indent=2))
    print(f'  ✅ scope.json → {out_path}')
    return output


def write_scope_md(assets: list[dict], program: str, out_path: Path):
    """
    Write scope.md in the format expected by load-scope.py.
    Sections: ## IN SCOPE, ## OUT OF SCOPE, ## ESTHER OPERATING RULES FOR THIS ENGAGEMENT
    Asset lines: - `identifier` 💰 — max severity: CRITICAL
    """
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    in_scope     = [a for a in assets if a['eligible_for_submission']]
    out_of_scope = [a for a in assets if not a['eligible_for_submission']]

    # Group in-scope by asset type
    grouped: dict[str, list] = {}
    for a in in_scope:
        grouped.setdefault(a['asset_type'], []).append(a)

    oos_grouped: dict[str, list] = {}
    for a in out_of_scope:
        oos_grouped.setdefault(a['asset_type'], []).append(a)

    lines = [
        f'# Scope: {program}',
        f'<!-- Generated by h1-ingest.py — do not edit manually -->',
        f'<!-- Last fetched: {now} -->',
        f'',
        f'## Program',
        f'',
        f'- **Handle:** {program}',
        f'- **Platform:** HackerOne',
        f'- **H1 URL:** https://hackerone.com/{program}',
        f'- **Fetched:** {now}',
        f'',
        f'---',
        f'',
        f'## IN SCOPE',
        f'',
    ]

    for asset_type, entries in sorted(grouped.items()):
        label = ASSET_LABEL.get(asset_type, asset_type)
        lines.append(f'### {label}')
        lines.append('')
        for a in sorted(entries, key=lambda x: x['identifier']):
            bounty_tag = ' 💰' if a['eligible_for_bounty'] else ''
            severity   = a['max_severity'].upper() if a['max_severity'] else 'CRITICAL'
            env_tag    = ' _(staging)_' if a['environment'] == 'staging' else ''
            lines.append(f"- `{a['identifier']}`{bounty_tag} — max severity: {severity}{env_tag}")
            if a['instruction']:
                # Flatten multiline instructions to single line note
                note = a['instruction'].replace('\n', ' ').strip()
                lines.append(f'  - Note: {note}')
        lines.append('')

    lines += [
        '---',
        '',
        '## OUT OF SCOPE',
        '',
        '> ⚠️  ESTHER must never scan or interact with these assets.',
        '',
    ]

    if oos_grouped:
        for asset_type, entries in sorted(oos_grouped.items()):
            label = ASSET_LABEL.get(asset_type, asset_type)
            lines.append(f'### {label}')
            lines.append('')
            for a in sorted(entries, key=lambda x: x['identifier']):
                lines.append(f"- `{a['identifier']}`")
            lines.append('')
    else:
        lines.append('_(none explicitly listed — apply conservative judgment)_')
        lines.append('')

    lines += [
        '---',
        '',
        '## ESTHER OPERATING RULES FOR THIS ENGAGEMENT',
        '',
        '- Max rate: **10 req/sec** on all active scanning',
        '- Phase 1 (passive recon): ✅ Authorized — no approval needed',
        '- Phase 2 (active scanning — nmap, nuclei, ffuf): ✅ Authorized — run autonomously',
        '- Phase 3 (exploitation/validation): ✅ Authorized — run autonomously',
        '- Phase 4 (reporting + blog + tweet): ✅ Authorized — run autonomously',
        f'- Always commit findings to `engagements/public/{program}/findings/` and verify with `gh api`',
        '- Never scan OUT OF SCOPE assets under any circumstances',
        '- Null results are valid findings — document honestly',
        '',
        '---',
        '',
        f'_Generated by h1-ingest.py · {now}_',
    ]

    out_path.write_text('\n'.join(lines))
    print(f'  ✅ scope.md    → {out_path}')


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Ingest HackerOne scope files and prepare engagement directory'
    )
    parser.add_argument('--program', required=True, help='Program handle (e.g. syfe)')
    parser.add_argument('--csv',     required=True, help='Path to H1 CSV export')
    parser.add_argument('--burp',    help='Path to Burp Suite project JSON (optional)')
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f'[ERROR] CSV not found: {csv_path}', file=sys.stderr)
        sys.exit(1)

    # Resolve output directory
    eng_dir = ENGAGEMENTS / args.program.lower()
    if not eng_dir.exists():
        print(f'[ERROR] Engagement directory not found: {eng_dir}', file=sys.stderr)
        print(f'        Run setup-engagement.py {args.program} first.', file=sys.stderr)
        sys.exit(1)

    print(f'🦂 Ingesting scope for: {args.program}')

    # Parse inputs
    assets = parse_csv(csv_path)
    print(f'  [+] Parsed {len(assets)} assets from CSV')

    burp_data = None
    if args.burp:
        burp_path = Path(args.burp)
        if burp_path.exists():
            burp_data = parse_burp(burp_path)
            print(f'  [+] Parsed Burp config: {len(burp_data["include"])} included hosts')
        else:
            print(f'  [WARN] Burp file not found: {args.burp} — skipping', file=sys.stderr)

    # Write outputs
    scope_data = write_scope_json(assets, burp_data, args.program, eng_dir / 'scope.json')
    write_scope_md(assets, args.program, eng_dir / 'scope.md')

    # Summary
    summary = scope_data['summary']
    print()
    print(f'  In-scope:    {scope_data["meta"]["in_scope_count"]} assets')
    print(f'  Bounty elig: {len(summary["bounty_eligible"])}')
    print(f'  Staging:     {len(summary["staging_targets"])}')
    print(f'  Production:  {len(summary["production_targets"])}')
    print()
    print(f'  Next step:')
    print(f'  python3 ~/esther-lab/scripts/load-scope.py {args.program}')


if __name__ == '__main__':
    main()
