#!/usr/bin/env python3
"""
nuclei-scan.py — ESTHER Targeted Nuclei Wrapper
Enforces correct template selection, rate limiting, and output paths.
ESTHER uses this instead of bare nuclei to prevent generic all-template scans.

Usage:
    python3 nuclei-scan.py --targets /tmp/<domain>-live-hosts.txt \
                           --program playtika \
                           --domain bingoblitz.com \
                           --profile gaming

Profiles:
    gaming      — API, auth, CORS, GraphQL, JWT, cloud, takeover, exposure
    web         — CVE, SQLi, XSS, SSRF, XXE, RCE, LFI, IDOR, misconfig
    cloud       — AWS, GCP, Azure, S3, metadata, IAM
    takeover    — Subdomain takeover only (fast, high-value)
    exposure    — Exposed credentials, tokens, API keys
    full        — medium/high/critical only, still filtered by severity (never all templates)

Output:
    ~/esther-lab/engagements/public/<program>/findings/nuclei-<domain>.txt
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path

HOME        = Path.home()
ENGAGEMENTS = HOME / 'esther-lab' / 'engagements' / 'public'

# ── Profiles ───────────────────────────────────────────────────────────────────
PROFILES = {
    'gaming': {
        'description': 'Gaming / mobile app companies — API, auth, cloud surface',
        'tags':        'api,auth,cors,graphql,jwt,token,exposure,misconfig,takeover,cloud',
        'severity':    'medium,high,critical',
    },
    'web': {
        'description': 'Generic web targets — CVEs, injection, misconfig',
        'tags':        'cve,sqli,xss,ssrf,xxe,rce,lfi,idor,misconfig,exposure,redirect',
        'severity':    'medium,high,critical',
    },
    'cloud': {
        'description': 'Cloud infrastructure — AWS, GCP, Azure, storage buckets',
        'tags':        'cloud,aws,gcp,azure,s3,exposure,misconfig',
        'severity':    'medium,high,critical',
    },
    'takeover': {
        'description': 'Subdomain takeover only — fast, high-value',
        'tags':        'takeover',
        'severity':    'medium,high,critical',
    },
    'exposure': {
        'description': 'Exposed credentials, tokens, API keys in responses',
        'tags':        'exposure,token,api-key,secret',
        'severity':    'medium,high,critical',
    },
    'full': {
        'description': 'Broader scan — all medium/high/critical, still severity-filtered',
        'tags':        None,  # no tag filter, but severity still applied
        'severity':    'medium,high,critical',
    },
}


def check_nuclei():
    result = subprocess.run('which nuclei', shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ nuclei not found. Install: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")
        sys.exit(1)
    result = subprocess.run('nuclei -version 2>&1', shell=True, capture_output=True, text=True)
    print(f"  nuclei: {result.stdout.strip() or result.stderr.strip()}")


def build_command(args, profile: dict, output_path: Path) -> list[str]:
    cmd = [
        'nuclei',
        '-l', str(args.targets),
        '-rate-limit', str(args.rate_limit),
        '-timeout', str(args.timeout),
        '-retries', '1',
        '-severity', profile['severity'],
        '-o', str(output_path),
        '-stats',
        '-no-color',
    ]

    if profile['tags']:
        cmd += ['-tags', profile['tags']]

    if args.concurrency:
        cmd += ['-c', str(args.concurrency)]

    return cmd


def main():
    parser = argparse.ArgumentParser(
        description='ESTHER targeted nuclei wrapper — always use this instead of bare nuclei'
    )
    parser.add_argument('--targets',    required=True,
                        help='Path to live hosts file (output from httpx probe)')
    parser.add_argument('--program',    required=True,
                        help='HackerOne program handle (e.g. playtika)')
    parser.add_argument('--domain',     required=True,
                        help='Domain being scanned (e.g. bingoblitz.com)')
    parser.add_argument('--profile',    default='gaming',
                        choices=list(PROFILES.keys()),
                        help='Template profile to use (default: gaming)')
    parser.add_argument('--rate-limit', type=int, default=10,
                        help='Max requests per second (default: 10, never exceed for bug bounty)')
    parser.add_argument('--timeout',    type=int, default=10,
                        help='Request timeout in seconds (default: 10)')
    parser.add_argument('--concurrency', type=int, default=None,
                        help='Concurrent templates (default: nuclei auto)')
    parser.add_argument('--dry-run',    action='store_true',
                        help='Print command without running')
    args = parser.parse_args()

    targets_path = Path(args.targets)
    if not targets_path.exists():
        print(f"❌ Targets file not found: {targets_path}")
        print(f"   Run httpx probe first — see RECON-PLAYBOOK.md Phase 2 Step 1")
        sys.exit(1)

    target_count = sum(1 for _ in targets_path.open())
    if target_count == 0:
        print(f"❌ Targets file is empty: {targets_path}")
        sys.exit(1)

    profile = PROFILES[args.profile]

    out_dir = ENGAGEMENTS / args.program / 'findings'
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp  = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')
    output_path = out_dir / f"nuclei-{args.domain}-{args.profile}-{timestamp}.txt"

    print(f"\n🦂 ESTHER Nuclei Scanner")
    print(f"   Program:     {args.program}")
    print(f"   Domain:      {args.domain}")
    print(f"   Profile:     {args.profile} — {profile['description']}")
    print(f"   Tags:        {profile['tags'] or '(all, severity-filtered)'}")
    print(f"   Severity:    {profile['severity']}")
    print(f"   Rate limit:  {args.rate_limit} req/sec")
    print(f"   Targets:     {target_count} hosts from {targets_path}")
    print(f"   Output:      {output_path}")
    print()

    check_nuclei()

    cmd = build_command(args, profile, output_path)

    print(f"   Command: {' '.join(cmd)}")
    print()

    if args.dry_run:
        print("  [dry-run] Not executing.")
        return

    # Estimated time warning
    est_minutes = (target_count * 3) / 60  # rough estimate
    print(f"  ⏱️  Estimated time: ~{est_minutes:.0f} minutes at {args.rate_limit} req/sec")
    print(f"  Running scan...\n")

    start = datetime.now(timezone.utc)
    result = subprocess.run(cmd)
    elapsed = (datetime.now(timezone.utc) - start).seconds

    print(f"\n  Scan completed in {elapsed}s")

    if output_path.exists():
        line_count = sum(1 for _ in output_path.open())
        print(f"  Output: {line_count} lines → {output_path}")

        if line_count == 0:
            print(f"  ℹ️  Zero findings for profile '{args.profile}' — null result is valid.")
        else:
            # Quick severity summary
            with open(output_path) as f:
                content = f.read()
            for sev in ['critical', 'high', 'medium']:
                count = content.lower().count(f'[{sev}]')
                if count:
                    print(f"  {'🔴' if sev=='critical' else '🟠' if sev=='high' else '🟡'} {sev.capitalize()}: {count}")

        print(f"\n  Next step — commit and verify:")
        print(f"  cd ~/esther-lab")
        print(f"  git add engagements/public/{args.program}/findings/$(basename {output_path})")
        print(f"  git commit -m \"Phase 2: nuclei {args.profile} scan {args.domain} — N findings\"")
        print(f"  git push")
        print(f"  gh api repos/FinkSecurity/esther-lab/commits?path=engagements/public/{args.program}/findings\\&per_page=1 --jq '.[0].sha[:9]'")
    else:
        print(f"  ⚠️  Output file not created — check nuclei errors above")


if __name__ == '__main__':
    main()
