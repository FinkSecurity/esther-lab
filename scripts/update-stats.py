#!/usr/bin/env python3
"""
Fink Security — Stats Updater
Updates the date on stats.json without overwriting manually verified metrics.
Real metrics are set manually based on actual engagement data.
Run weekly via cron: 0 8 * * 1
"""

import os, json, datetime, subprocess

FINK_SITE  = os.path.expanduser("~/finksecurity-site")
STATS_FILE = os.path.join(FINK_SITE, "stats.json")
today      = datetime.date.today()

def update_stats():
    # Load existing stats — never overwrite verified metrics
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            stats = json.load(f)
    else:
        # Fallback if file missing — use last known good values
        stats = {
            "period":               "Last 30 Days",
            "cves_analyzed":        12,
            "hosts_enumerated":     465,
            "critical_findings":    0,
            "threat_intel_queries": 47,
        }

    # Only update the date
    stats["updated"] = today.strftime("%Y-%m-%d")

    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ stats.json date updated to {today} — metrics preserved")
    print(f"   CVEs: {stats['cves_analyzed']} | Hosts: {stats['hosts_enumerated']} | Critical: {stats['critical_findings']} | Intel: {stats['threat_intel_queries']}")

    try:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"],
                       cwd=FINK_SITE, check=True, capture_output=True)
        subprocess.run(["git", "add", "stats.json"],
                       cwd=FINK_SITE, check=True)
        subprocess.run(["git", "commit", "-m",
                        f"stats: update date {today.strftime('%Y-%m-%d')}"],
                       cwd=FINK_SITE, check=True)
        subprocess.run(["git", "push"], cwd=FINK_SITE, check=True)
        print("✅ Pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git error: {e}")

if __name__ == "__main__":
    update_stats()
