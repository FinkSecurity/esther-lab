#!/usr/bin/env python3
"""
load-scope.py — ESTHER Task Startup: Load Engagement Scope Context
Reads scope.md for a given program, writes a working context file ESTHER
references throughout the engagement.

Usage:
    python3 load-scope.py <program_handle> [task_id]
    python3 load-scope.py playtika FSC-20260316-0142

Writes:
    ~/.openclaw/workspace/ACTIVE-ENGAGEMENT.md   — current task context
    ~/.openclaw/workspace/SCOPE-CACHE.json        — machine-readable scope for scripts

ESTHER reads ACTIVE-ENGAGEMENT.md at the start of every task action.
"""

import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
HOME        = Path.home()
WORKSPACE   = HOME / '.openclaw' / 'workspace'
ENGAGEMENTS = HOME / 'esther-lab' / 'engagements' / 'public'
ACTIVE_MD   = WORKSPACE / 'ACTIVE-ENGAGEMENT.md'
SCOPE_CACHE = WORKSPACE / 'SCOPE-CACHE.json'


def parse_scope_md(scope_path: Path) -> dict:
    """
    Parse machine-readable scope.md into structured dict.
    Returns:
        {
            handle, platform, fetched,
            in_scope: [str],           # asset identifiers
            out_of_scope: [str],       # asset identifiers  
            bounty_eligible: [str],    # subset of in_scope with 💰
            wildcards: [str],          # wildcard entries only
            rules: [str],              # operating rules lines
        }
    """
    if not scope_path.exists():
        return {}

    text       = scope_path.read_text()
    lines      = text.splitlines()

    handle     = ''
    platform   = 'HackerOne'
    fetched    = ''
    in_scope   = []
    out_scope  = []
    bounty_el  = []
    wildcards  = []
    rules      = []

    section    = None

    for line in lines:
        # Extract metadata
        if line.startswith('- **Handle:**'):
            handle = line.split('**Handle:**')[-1].strip()
        elif line.startswith('- **Platform:**'):
            platform = line.split('**Platform:**')[-1].strip()
        elif line.startswith('- **Fetched:**') or '<!-- Last fetched:' in line:
            fetched = re.sub(r'.*fetched.*?(\d{4}-\d{2}-\d{2}.*?)[\-\*>].*', r'\1',
                             line, flags=re.IGNORECASE).strip().rstrip('-->')

        # Track sections
        if line.strip() == '## IN SCOPE':
            section = 'in'
        elif line.strip() == '## OUT OF SCOPE':
            section = 'out'
        elif line.strip() == '## ESTHER OPERATING RULES FOR THIS ENGAGEMENT':
            section = 'rules'
        elif line.startswith('## '):
            section = None

        # Parse asset lines
        if line.startswith('- `') and section in ('in', 'out'):
            # Extract identifier between backticks
            m = re.match(r"- `([^`]+)`", line)
            if m:
                identifier = m.group(1)
                if section == 'in':
                    in_scope.append(identifier)
                    if '💰' in line:
                        bounty_el.append(identifier)
                    if identifier.startswith('*'):
                        wildcards.append(identifier)
                else:
                    out_scope.append(identifier)

        # Parse rules
        if section == 'rules' and line.startswith('- '):
            rules.append(line[2:].strip())

    return {
        'handle':          handle,
        'platform':        platform,
        'fetched':         fetched,
        'in_scope':        in_scope,
        'out_of_scope':    out_scope,
        'bounty_eligible': bounty_el,
        'wildcards':       wildcards,
        'rules':           rules,
        'scope_path':      str(scope_path),
    }


def write_active_engagement(scope: dict, task_id: str, handle: str):
    """Write ACTIVE-ENGAGEMENT.md — ESTHER's working context for this task."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    findings_dir = ENGAGEMENTS / handle / 'findings'
    finding_count = len(list(findings_dir.glob('*.md'))) if findings_dir.exists() else 0

    in_scope_list  = '\n'.join(f'  - `{a}`' for a in scope.get('in_scope', []))
    oos_list       = '\n'.join(f'  - `{a}`' for a in scope.get('out_of_scope', []))
    rules_list     = '\n'.join(f'  - {r}' for r in scope.get('rules', []))
    bounty_list    = '\n'.join(f'  - `{a}`' for a in scope.get('bounty_eligible', []))

    content = f"""# ACTIVE ENGAGEMENT CONTEXT
<!-- Written by load-scope.py — refreshed at task start -->
<!-- Loaded: {now} -->

## Task
- **Task ID:** {task_id or 'N/A'}
- **Program:** {handle}
- **Platform:** {scope.get('platform', 'HackerOne')}
- **Scope last fetched:** {scope.get('fetched', 'unknown')}
- **Findings so far:** {finding_count} documented

---

## IN SCOPE ({len(scope.get('in_scope', []))} assets)

{in_scope_list or '  _(none)_'}

## BOUNTY ELIGIBLE

{bounty_list or '  _(none explicitly marked)_'}

---

## OUT OF SCOPE — NEVER SCAN THESE

{oos_list or '  _(none explicitly listed — apply conservative judgment)_'}

---

## OPERATING RULES

{rules_list or '  _(see SOUL.md)_'}

---

## ESTHER TASK STARTUP CHECKLIST

Before beginning any work on this engagement:
- [ ] Confirm task ID matches an `APPROVE <taskid>` received from Operator
- [ ] Read this file — know what is in and out of scope
- [ ] Read SOUL.md — confirm phase gates
- [ ] Check `findings/` for prior work — do not duplicate
- [ ] Set rate limiting: max 10 req/sec on all active scanning
- [ ] After every commit: verify with `gh api repos/FinkSecurity/esther-lab/commits?path=engagements/public/{handle}/findings&per_page=1`

---

## PATHS

- Scope file:    `~/esther-lab/engagements/public/{handle}/scope.md`
- Findings dir:  `~/esther-lab/engagements/public/{handle}/findings/`
- Scope cache:   `~/.openclaw/workspace/SCOPE-CACHE.json`

---

_Loaded by load-scope.py · {now}_
"""
    ACTIVE_MD.write_text(content)
    print(f"  ✅ Active engagement written: {ACTIVE_MD}")


def write_scope_cache(scope: dict, task_id: str):
    """Write SCOPE-CACHE.json for programmatic use by ESTHER's scripts."""
    cache = {
        'task_id':         task_id,
        'loaded_at':       datetime.now(timezone.utc).isoformat(),
        **scope
    }
    SCOPE_CACHE.write_text(json.dumps(cache, indent=2))
    print(f"  ✅ Scope cache written:       {SCOPE_CACHE}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 load-scope.py <program_handle> [task_id]")
        print("   eg: python3 load-scope.py playtika FSC-20260316-0142")
        sys.exit(1)

    handle  = sys.argv[1].lower().strip()
    task_id = sys.argv[2] if len(sys.argv) > 2 else ''

    WORKSPACE.mkdir(parents=True, exist_ok=True)

    scope_path = ENGAGEMENTS / handle / 'scope.md'

    if not scope_path.exists():
        print(f"❌ scope.md not found: {scope_path}")
        print(f"   Run first: python3 hackerone-scope-fetch.py {handle}")
        sys.exit(1)

    print(f"🦂 Loading scope for: {handle} (task: {task_id or 'no task id'})")

    scope = parse_scope_md(scope_path)

    if not scope:
        print(f"❌ Failed to parse scope.md at {scope_path}")
        sys.exit(1)

    write_active_engagement(scope, task_id, handle)
    write_scope_cache(scope, task_id)

    print()
    print(f"  In scope:     {len(scope['in_scope'])} assets")
    print(f"  Out of scope: {len(scope['out_of_scope'])} assets")
    print(f"  Bounty elig:  {len(scope['bounty_eligible'])} assets")
    print()
    print(f"  ESTHER is ready. Read ACTIVE-ENGAGEMENT.md before proceeding.")


if __name__ == '__main__':
    main()
