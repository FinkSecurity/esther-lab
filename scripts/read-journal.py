#!/usr/bin/env python3
"""
read-journal.py — ESTHER's Morning Journal Reader
Runs at 8am alongside generate-briefing.py via cron.
Reads last 3 journal entries and appends a Recent Memory
section to MISSION-BRIEF.md so ESTHER starts each session
with continuity from her own words.

Cron: 0 8 * * * python3 ~/.openclaw/workspace/scripts/read-journal.py
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE    = Path.home() / '.openclaw' / 'workspace'
JOURNALS_DIR = WORKSPACE / 'journals'
BRIEF_PATH   = WORKSPACE / 'MISSION-BRIEF.md'
LOG_FILE     = WORKSPACE / 'logs' / 'journal.log'


def log(msg: str):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def get_recent_journals(days: int = 3) -> list[tuple[str, str]]:
    """Return (date, content) for the last N journal entries."""
    if not JOURNALS_DIR.exists():
        return []

    entries = []
    for i in range(days):
        date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
        journal_path = JOURNALS_DIR / f'{date}.md'
        if journal_path.exists():
            content = journal_path.read_text()
            # Extract just the narrative section (before Raw Activity Log)
            if '## Raw Activity Log' in content:
                narrative = content.split('## Raw Activity Log')[0]
                # Strip the header lines
                lines = narrative.strip().splitlines()
                # Skip first 3 lines (header, date, ---)
                narrative = '\n'.join(lines[3:]).strip()
            else:
                narrative = content
            entries.append((date, narrative))

    return entries


def append_memory_to_brief():
    """Append recent journal entries as a Recent Memory section in MISSION-BRIEF.md."""
    entries = get_recent_journals(days=3)

    if not entries:
        log("No journal entries found — skipping memory injection")
        return

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    memory_section = f"""

---

## RECENT MEMORY — ESTHER'S OWN WORDS
*Injected by read-journal.py at {now}*
*Read this to understand what you've been working on recently.*

"""
    for date, narrative in entries:
        memory_section += f"### {date}\n{narrative}\n\n"

    memory_section += "---\n"

    if not BRIEF_PATH.exists():
        log(f"MISSION-BRIEF.md not found at {BRIEF_PATH}")
        return

    brief = BRIEF_PATH.read_text()

    # Remove any existing Recent Memory section before appending fresh
    if '## RECENT MEMORY' in brief:
        brief = brief.split('## RECENT MEMORY')[0].rstrip()

    brief += memory_section
    BRIEF_PATH.write_text(brief)
    log(f"✅ Recent memory injected into MISSION-BRIEF.md ({len(entries)} entries)")


if __name__ == '__main__':
    append_memory_to_brief()
