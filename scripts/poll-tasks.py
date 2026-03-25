#!/usr/bin/env python3
"""
poll-tasks.py — ESTHER Task Poller
Checks ~/tasks_pending/ for new client jobs and dispatches them.

Run via cron every 5 minutes:
  */5 * * * * python3 ~/.openclaw/workspace/scripts/poll-tasks.py

Or run manually: python3 poll-tasks.py
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TASKS_DIR   = Path.home() / 'tasks_pending'
ESTHER_LAB  = Path.home() / 'esther-lab'
LOG_FILE    = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'task-poller.log'

# Actions ESTHER knows how to handle autonomously
AUTONOMOUS_ACTIONS = [
    'personal_exposure_report',
    'breach_credential_check',
    'home_network_check',
]

# Actions that require Operator approval before executing
APPROVAL_REQUIRED_ACTIONS = [
    'digital_footprint_audit',
    'social_media_osint',
    'harassment_investigation',
    'basic_privacy_pack',
    'full_digital_shield',
    'complete_protection',
    'manual_review',
]


def log(msg: str):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def sanitize_target(target: str) -> str:
    """
    Sanitize target string before passing to CLI tools.
    Strips shell metacharacters — treats instruction_payload as untrusted.
    """
    import re
    # Allow only email addresses and domain names
    sanitized = re.sub(r'[^a-zA-Z0-9@.\-_+]', '', target)
    return sanitized[:256]


def mark_in_progress(task_path: Path, task: dict):
    """Mark task as in-progress to prevent double-execution."""
    task['instruction_payload']['status'] = 'in_progress'
    task['instruction_payload']['started_at'] = datetime.now(timezone.utc).isoformat()
    task_path.write_text(json.dumps(task, indent=2))


def mark_awaiting_approval(task_path: Path, task: dict):
    """Mark task as awaiting operator approval."""
    task['instruction_payload']['status'] = 'awaiting_approval'
    task_path.write_text(json.dumps(task, indent=2))


def process_task(task_path: Path):
    """Process a single pending task."""
    try:
        task    = json.loads(task_path.read_text())
        job_id  = task['task_metadata']['job_id']
        action  = task['instruction_payload']['action']
        target  = sanitize_target(task['instruction_payload']['target'])
        client  = task['client_context']['client_email']
        service = task['client_context']['service_name']
    except (KeyError, json.JSONDecodeError) as e:
        log(f"❌ Malformed task file {task_path.name}: {e}")
        return

    log(f"📋 Task found: {job_id} — {service} for {client}")

    # Check if already being processed
    status = task.get('instruction_payload', {}).get('status', 'pending')
    if status in ('in_progress', 'awaiting_approval', 'completed'):
        log(f"⏭️  Skipping {job_id} — status: {status}")
        return

    # Route based on action type
    if action in AUTONOMOUS_ACTIONS:
        log(f"🦂 Auto-dispatching: {action} for {target}")
        mark_in_progress(task_path, task)
        dispatch_autonomous(job_id, action, target, client, task)

    elif action in APPROVAL_REQUIRED_ACTIONS:
        log(f"⏳ Awaiting approval: {action} for {target}")
        mark_awaiting_approval(task_path, task)
        # Operator must send: EXECUTE <job_id> via Telegram

    else:
        log(f"❓ Unknown action: {action} — marking for manual review")
        mark_awaiting_approval(task_path, task)


def dispatch_autonomous(job_id: str, action: str, target: str,
                        client: str, task: dict):
    """
    Dispatch an autonomous task to the appropriate script.
    Creates engagement directory and runs the appropriate script.
    """
    engagement_dir = ESTHER_LAB / 'engagements' / 'clients' / job_id
    engagement_dir.mkdir(parents=True, exist_ok=True)

    # Write job context for the script
    context_file = engagement_dir / 'job-context.json'
    context_file.write_text(json.dumps({
        'job_id':  job_id,
        'action':  action,
        'target':  target,
        'client':  client,
        'service': task['client_context']['service_name'],
    }, indent=2))

    log(f"📁 Engagement dir: {engagement_dir}")

    # Dispatch to appropriate script
    script_map = {
        'personal_exposure_report': 'generate-exposure-report.py',
        'breach_credential_check':  'hibp-check.py',
        'home_network_check':       'home-network-check.py',  # TODO: create
    }

    script = script_map.get(action)
    if not script:
        log(f"❌ No script mapped for action: {action}")
        return

    script_path = Path.home() / '.openclaw' / 'workspace' / 'scripts' / script
    if not script_path.exists():
        log(f"❌ Script not found: {script_path}")
        return

    log(f"🚀 Running: {script} --target {target} --job-id {job_id}")
    try:
        result = subprocess.run(
            ['python3', str(script_path),
             '--target', target,
             '--job-id', job_id,
             '--output-dir', str(engagement_dir)],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            log(f"✅ {job_id} completed successfully")
        else:
            log(f"⚠️  {job_id} completed with errors: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        log(f"⏰ {job_id} timed out after 5 minutes")
    except Exception as e:
        log(f"❌ {job_id} failed: {e}")


def main():
    if not TASKS_DIR.exists():
        log("No tasks_pending directory — nothing to do")
        return

    pending = sorted(
        [f for f in TASKS_DIR.glob('task_*.json')
         if not f.parent.name == 'completed'],
        key=lambda p: p.stat().st_mtime
    )

    if not pending:
        return  # Silent exit when no tasks — don't spam logs

    log(f"🦂 Found {len(pending)} pending task(s)")
    for task_path in pending:
        process_task(task_path)


if __name__ == '__main__':
    main()
