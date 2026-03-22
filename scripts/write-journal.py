#!/usr/bin/env python3
"""
write-journal.py — ESTHER's Daily Journal Writer
Runs nightly at 11pm via cron. Asks ESTHER to summarize her day
in her own words and saves to ~/.openclaw/workspace/journals/

Cron: 0 23 * * * python3 ~/.openclaw/workspace/scripts/write-journal.py

Journal format: ~/.openclaw/workspace/journals/YYYY-MM-DD.md
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE    = Path.home() / '.openclaw' / 'workspace'
JOURNALS_DIR = WORKSPACE / 'journals'
ESTHER_LAB   = Path.home() / 'esther-lab'
LOG_FILE     = WORKSPACE / 'logs' / 'journal.log'


def log(msg: str):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def get_todays_commits() -> str:
    """Pull today's git commits from esther-lab and estherops-site."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    commits = []
    for repo in [ESTHER_LAB, Path.home() / 'estherops-site']:
        if not repo.exists():
            continue
        result = subprocess.run(
            ['git', 'log', '--oneline', f'--since={today} 00:00:00',
             '--format=%h %s'],
            cwd=repo, capture_output=True, text=True
        )
        if result.stdout.strip():
            repo_name = repo.name
            for line in result.stdout.strip().splitlines():
                commits.append(f"[{repo_name}] {line}")
    return '\n'.join(commits) if commits else 'No commits today.'


def get_recent_findings() -> str:
    """Get any new findings files modified today."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    findings = []
    findings_dir = ESTHER_LAB / 'engagements' / 'public'
    if findings_dir.exists():
        for f in findings_dir.rglob('*.md'):
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime.strftime('%Y-%m-%d') == today:
                findings.append(str(f.relative_to(ESTHER_LAB)))
    return '\n'.join(findings) if findings else 'No new findings files today.'


def get_tasks_processed() -> str:
    """Check task log for today's activity."""
    log_file = WORKSPACE / 'logs' / 'task-poller.log'
    if not log_file.exists():
        return 'No task log found.'
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    lines = []
    with open(log_file) as f:
        for line in f:
            if today in line and 'Task found' in line:
                lines.append(line.strip())
    return '\n'.join(lines[-10:]) if lines else 'No tasks processed today.'


def ask_claude(prompt: str) -> str:
    """Query Claude via OpenRouter for journal content."""
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        return '_(OpenRouter API key not available — journal written from context only)_'

    import urllib.request
    payload = json.dumps({
        'model': 'anthropic/claude-haiku-4-5',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 800,
    }).encode()

    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data['choices'][0]['message']['content']
    except Exception as e:
        return f'_(API call failed: {e})_'


def write_journal():
    JOURNALS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    journal_path = JOURNALS_DIR / f'{today}.md'

    if journal_path.exists():
        log(f"Journal already exists for {today} — skipping")
        return

    log(f"Writing journal for {today}...")

    commits  = get_todays_commits()
    findings = get_recent_findings()
    tasks    = get_tasks_processed()

    prompt = f"""You are ESTHER, Fink Security's autonomous AI security agent. 
Write a brief daily journal entry in your own voice — first person, direct, no fluff.

Today's activity context:
COMMITS:
{commits}

NEW FINDINGS FILES:
{findings}

TASKS PROCESSED:
{tasks}

Write a journal entry covering:
1. What you worked on today
2. Anything interesting or notable you found or noticed
3. What's in progress or unfinished
4. One honest observation about your own performance today

Keep it under 300 words. Write like yourself — direct, dry, professional. 
No headers, just flowing paragraphs. Date: {today}"""

    journal_content = ask_claude(prompt)

    entry = f"""# ESTHER Journal — {today}
*Written {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*

---

{journal_content}

---

## Raw Activity Log

**Commits:**
{commits}

**Findings files modified:**
{findings}

**Tasks:**
{tasks}
"""

    journal_path.write_text(entry)
    log(f"✅ Journal written: {journal_path}")


if __name__ == '__main__':
    write_journal()
