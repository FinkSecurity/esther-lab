#!/usr/bin/env python3
"""
setup-engagement.py — Create engagement directory structure for a new program
Run once per new program to set up findings/, submissions/, and scope.md

Usage:
    python3 setup-engagement.py <program_handle>
    python3 setup-engagement.py x
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

HOME        = Path.home()
ENGAGEMENTS = HOME / 'esther-lab' / 'engagements' / 'public'

def setup(handle: str):
    eng_dir      = ENGAGEMENTS / handle
    findings_dir = eng_dir / 'findings'
    subs_dir     = eng_dir / 'submissions'

    for d in [eng_dir, findings_dir, subs_dir]:
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / '.gitkeep'
        if not any(d.iterdir()):
            gitkeep.touch()

    scope_path = eng_dir / 'scope.md'
    if not scope_path.exists():
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        scope_path.write_text(f"# Scope: {handle}\n<!-- Created: {now} -->\n<!-- Run hackerone-scope-fetch.py or paste scope manually -->\n")
        print(f"  Created placeholder scope.md — populate with hackerone-scope-fetch.py or manual import")

    print(f"  ✅ Engagement directory ready: {eng_dir}")
    print(f"     findings/    → {findings_dir}")
    print(f"     submissions/ → {subs_dir}")
    print(f"     scope.md     → {scope_path}")
    print()
    print(f"  Next steps:")
    print(f"  1. Copy scope.md:  scp scope.md esther@vps:~/esther-lab/engagements/public/{handle}/scope.md")
    print(f"  2. Commit:         cd ~/esther-lab && git add engagements/public/{handle}/ && git commit -m 'feat: {handle} engagement structure'")
    print(f"  3. Start recon:    read ~/esther-lab/docs/RECON-PLAYBOOK.md")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 setup-engagement.py <program_handle>")
        sys.exit(1)
    setup(sys.argv[1].lower().strip())
