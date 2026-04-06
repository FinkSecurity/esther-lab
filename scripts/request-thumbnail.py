#!/usr/bin/env python3
"""
request-thumbnail.py — ESTHER thumbnail request relay
Sends a structured thumbnail request to the Fink Security Ops group chat.
Ezra's listener picks this up, generates the image, SCPs it to the VPS,
and confirms back to the group.

Usage:
    python3 request-thumbnail.py --slug xiaomi-phase4 --title "Xiaomi Phase 4" \
        --subtitle "Manual Web App Testing" --prompt "dark cyberpunk IDOR attack visualization"

    python3 request-thumbnail.py --slug xiaomi-phase4 --title "Xiaomi Phase 4" \
        --subtitle "Manual Web App Testing" --prompt "dark cyberpunk IDOR attack visualization" \
        --wait  # blocks until Ezra confirms, then exits 0
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN     = os.environ.get('TELEGRAM_BOT_TOKEN', '')
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '-5225506150')
THUMBNAIL_DIR = Path('/home/esther/estherops-site/static/thumbnails')

REQUEST_TAG   = '🖼️ THUMBNAIL_REQUEST'
READY_TAG     = '✅ THUMBNAIL_READY'
POLL_INTERVAL = 10   # seconds between confirmation polls
POLL_TIMEOUT  = 300  # 5 minutes max wait


def send_message(text: str) -> bool:
    """Send a message to the group chat via ESTHER's bot."""
    if not BOT_TOKEN:
        print('[ERROR] TELEGRAM_BOT_TOKEN not set', file=sys.stderr)
        return False

    r = requests.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        json={'chat_id': GROUP_CHAT_ID, 'text': text},
        timeout=10
    )
    if r.status_code != 200:
        print(f'[ERROR] Telegram sendMessage failed: {r.text}', file=sys.stderr)
        return False
    return True


def get_updates(offset: int = 0) -> list:
    """Poll for new messages in the group."""
    r = requests.get(
        f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates',
        params={'offset': offset, 'timeout': 10, 'chat_id': GROUP_CHAT_ID},
        timeout=20
    )
    if r.status_code != 200:
        return []
    return r.json().get('result', [])


def wait_for_confirmation(slug: str) -> bool:
    """
    Poll group chat for THUMBNAIL_READY confirmation from Ezra.
    Returns True if confirmed within timeout, False otherwise.
    """
    print(f'[INFO] Waiting for Ezra to confirm thumbnail: {slug}')
    deadline = time.time() + POLL_TIMEOUT
    offset   = 0

    # Get current update offset so we only look at NEW messages
    updates = get_updates()
    if updates:
        offset = updates[-1]['update_id'] + 1

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        updates = get_updates(offset)

        for update in updates:
            offset = update['update_id'] + 1
            msg    = update.get('message', {})
            text   = msg.get('text', '')

            if READY_TAG in text and slug in text:
                print(f'[OK] Ezra confirmed thumbnail ready: {slug}')
                return True

        elapsed = int(time.time() - (deadline - POLL_TIMEOUT))
        print(f'[INFO] Still waiting... ({elapsed}s elapsed)')

    print(f'[TIMEOUT] No confirmation received within {POLL_TIMEOUT}s', file=sys.stderr)
    return False


def verify_thumbnail_on_disk(slug: str) -> bool:
    """Confirm the file actually landed on disk after Ezra's SCP."""
    path = THUMBNAIL_DIR / f'{slug}.png'
    return path.exists()


def main():
    parser = argparse.ArgumentParser(description='Request thumbnail from Ezra via Telegram group')
    parser.add_argument('--slug',     required=True,  help='Post slug (e.g. xiaomi-phase4)')
    parser.add_argument('--title',    required=True,  help='Image title text')
    parser.add_argument('--subtitle', default='',     help='Image subtitle text (optional)')
    parser.add_argument('--prompt',   required=True,  help='Image generation prompt (topic description)')
    parser.add_argument('--wait',     action='store_true', help='Block until Ezra confirms, then verify on disk')
    args = parser.parse_args()

    # Build full prompt with brand style injected
    full_prompt = (
        f'dark cyberpunk, cyan #22d3ee accent color, dark background #0a0a12, '
        f'{args.prompt}, Fink Security branding, no warm tones, no orange'
    )

    # Structured request message — Ezra's listener keys on THUMBNAIL_REQUEST tag
    msg = (
        f'{REQUEST_TAG}\n'
        f'slug: {args.slug}\n'
        f'title: {args.title}\n'
        f'subtitle: {args.subtitle}\n'
        f'prompt: {full_prompt}'
    )

    print(f'[INFO] Sending thumbnail request to group chat for slug: {args.slug}')
    if not send_message(msg):
        sys.exit(1)
    print('[OK] Request sent')

    if args.wait:
        confirmed = wait_for_confirmation(args.slug)
        if not confirmed:
            print('[ERROR] Timed out waiting for Ezra', file=sys.stderr)
            sys.exit(1)

        # Final disk check
        if verify_thumbnail_on_disk(args.slug):
            print(f'[OK] Thumbnail verified on disk: {THUMBNAIL_DIR}/{args.slug}.png')
            sys.exit(0)
        else:
            print(f'[ERROR] Ezra confirmed but file not found: {THUMBNAIL_DIR}/{args.slug}.png', file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
