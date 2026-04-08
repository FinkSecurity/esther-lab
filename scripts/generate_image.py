#!/usr/bin/env python3
"""
generate_image.py — Fink Security AI Image Generator for Ezra
Uses fal.ai FLUX.1 to generate high quality base images,
then overlays Fink Security branding with Pillow.

Usage:
    python3 generate_image.py --prompt "dark cybersecurity hacker scene" --title "x.ai Phase 5" --subtitle "Defense-in-Depth" --out media/output/thumbnail.png
    python3 generate_image.py --prompt "abstract network topology dark" --title "Home Network Security" --out media/output/home-network.png

Requires:
    pip install requests Pillow
    FAL_API_KEY in secrets.env or environment
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ── Brand Colors ──────────────────────────────────────────────────
BG_DARK    = '#0a0a12'
CYAN       = '#22d3ee'
CYAN_LIGHT = '#67e8f9'
MUTED      = '#94a3b8'
WHITE      = '#f3f4f6'

# ── Load API key ──────────────────────────────────────────────────
def load_api_key() -> str:
    key = os.environ.get('FAL_API_KEY', '')
    if key:
        return key
    # Try secrets.env in workspace
    for secrets_path in [
        Path(__file__).parent.parent / 'secrets.env',
        Path.home() / 'tools' / 'ezra-lab' / 'secrets.env',
        Path.home() / '.openclaw' / 'workspace' / 'secrets.env',
    ]:
        if secrets_path.exists():
            for line in secrets_path.read_text().splitlines():
                if line.startswith('FAL_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    return ''


def generate_image_fal(prompt: str, api_key: str, width: int = 1280, height: int = 720) -> bytes:
    """Generate image using fal.ai FLUX.1 schnell model."""

    # Submit request
    headers = {
        'Authorization': f'Key {api_key}',
        'Content-Type': 'application/json'
    }

    payload = {
        'prompt': prompt,
        'image_size': {'width': width, 'height': height},
        'num_inference_steps': 4,
        'num_images': 1,
        'enable_safety_checker': True
    }

    print(f'  🎨 Generating image with FLUX.1...')
    print(f'  Prompt: {prompt[:80]}...' if len(prompt) > 80 else f'  Prompt: {prompt}')

    # Use queue endpoint for async generation
    response = requests.post(
        'https://queue.fal.run/fal-ai/flux/schnell',
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code not in (200, 201):
        raise Exception(f'fal.ai submission failed: {response.status_code} {response.text[:200]}')

    data = response.json()
    request_id = data.get('request_id')
    status_url = data.get('status_url') or f'https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id}/status'
    result_url = data.get('response_url') or f'https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id}'

    print(f'  Request ID: {request_id}')

    # Poll for completion
    max_wait = 120
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(3)
        elapsed += 3

        status_resp = requests.get(status_url, headers=headers, timeout=15)
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status', '')
            print(f'  Status: {status} ({elapsed}s)')

            if status == 'COMPLETED':
                break
            elif status in ('FAILED', 'ERROR'):
                raise Exception(f'Image generation failed: {status_data}')

    # Fetch result
    result_resp = requests.get(result_url, headers=headers, timeout=15)
    if result_resp.status_code != 200:
        raise Exception(f'Failed to fetch result: {result_resp.status_code}')

    result_data = result_resp.json()
    images = result_data.get('images', [])
    if not images:
        raise Exception(f'No images in response: {result_data}')

    image_url = images[0].get('url', '')
    if not image_url:
        raise Exception('No image URL in response')

    print(f'  ✅ Image generated: {image_url[:60]}...')

    # Download image
    img_resp = requests.get(image_url, timeout=30)
    if img_resp.status_code != 200:
        raise Exception(f'Failed to download image: {img_resp.status_code}')

    return img_resp.content


def overlay_branding(
    image_bytes: bytes,
    title: str,
    subtitle: str = '',
    output_path: Path = None,
    width: int = 1280,
    height: int = 720
) -> Path:
    """Overlay Fink Security branding on generated image."""

    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img = img.resize((width, height), Image.LANCZOS)
    draw = ImageDraw.Draw(img, 'RGBA')

    # Dark gradient overlay at bottom for text readability
    for y in range(height // 2, height):
        alpha = int(180 * (y - height // 2) / (height // 2))
        draw.rectangle([0, y, width, y + 1], fill=(10, 10, 18, alpha))

    # Top cyan bar
    draw.rectangle([0, 0, width, 4], fill=CYAN)

    # Bottom cyan bar
    draw.rectangle([0, height - 4, width, height], fill=CYAN)

    # Load fonts
    try:
        font_title = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 72)
        font_sub   = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 36)
        font_brand = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title
        font_brand = font_title

    # Title position (lower third)
    title_y = height - 180 if subtitle else height - 130

    # Title shadow
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    tx = (width - tw) // 2
    draw.text((tx + 2, title_y + 2), title, font=font_title, fill=(0, 0, 0, 180))
    draw.text((tx, title_y), title, font=font_title, fill=CYAN)

    # Subtitle
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox[2] - bbox[0]
        sx = (width - sw) // 2
        draw.text((sx, title_y + 85), subtitle, font=font_sub, fill=MUTED)

    # Fink Security watermark (bottom right)
    watermark = 'FINK SECURITY'
    bbox = draw.textbbox((0, 0), watermark, font=font_brand)
    ww = bbox[2] - bbox[0]
    draw.text((width - ww - 20, height - 35), watermark, font=font_brand, fill='#0e7490')

    # Shield icon (simple geometric — bottom right)
    sx, sy = width - 30, height - 60
    shield_pts = [
        (sx, sy - 20), (sx + 20, sy - 20),
        (sx + 20, sy - 5), (sx + 10, sy + 5),
        (sx, sy - 5)
    ]
    draw.polygon(shield_pts, fill=CYAN, outline=CYAN_LIGHT)

    # Save
    if output_path is None:
        output_path = Path('media/output/generated-thumbnail.png')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), 'PNG', quality=95)
    print(f'  ✅ Saved: {output_path}')
    return output_path


def build_prompt(title: str, subtitle: str = '', style: str = 'cybersecurity') -> str:
    """Build an effective FLUX.1 prompt for security content thumbnails."""

    base_styles = {
        'cybersecurity': (
            'dark cyberpunk aesthetic, deep navy and black background, '
            'glowing cyan neon accents, digital network grid lines, '
            'abstract circuit board patterns, cinematic lighting, '
            'professional tech photography style, 4k ultra detailed, '
            'no text, no watermarks'
        ),
        'hacking': (
            'dark hacker room aesthetic, multiple monitors with green terminal text, '
            'dramatic side lighting, deep shadows, cinematic noir style, '
            'professional photography, ultra detailed, no text'
        ),
        'network': (
            'abstract digital network topology, glowing nodes and connections, '
            'deep space dark background, cyan and blue light trails, '
            'futuristic visualization, 4k render, no text'
        ),
        'data': (
            'abstract data visualization, flowing particles, dark background, '
            'neon cyan data streams, professional tech aesthetic, '
            'cinematic render, ultra detailed, no text'
        ),
    }

    style_prompt = base_styles.get(style, base_styles['cybersecurity'])
    topic_hint = title.lower().replace(' ', ' ')

    return f'{topic_hint} concept, {style_prompt}'


def main():
    parser = argparse.ArgumentParser(description='Fink Security AI Thumbnail Generator')
    parser.add_argument('--prompt',   help='Custom image prompt (optional — auto-generated if not provided)')
    parser.add_argument('--title',    required=True, help='Main title text overlay')
    parser.add_argument('--subtitle', default='',    help='Subtitle text overlay')
    parser.add_argument('--style',    default='cybersecurity',
                        choices=['cybersecurity', 'hacking', 'network', 'data'],
                        help='Visual style preset')
    parser.add_argument('--out',      default='media/output/thumbnail.png', help='Output file path')
    parser.add_argument('--width',    default=1280, type=int)
    parser.add_argument('--height',   default=720,  type=int)
    parser.add_argument('--no-overlay', action='store_true', help='Skip branding overlay, save raw image only')
    args = parser.parse_args()

    # Load API key
    api_key = load_api_key()
    if not api_key:
        print('❌ FAL_API_KEY not found in environment or secrets.env')
        sys.exit(1)

    # Build prompt
    prompt = args.prompt or build_prompt(args.title, args.subtitle, args.style)

    output_path = Path(args.out)

    print(f'')
    print(f'🎨 Fink Security Image Generator')
    print(f'   Title:    {args.title}')
    print(f'   Subtitle: {args.subtitle or "(none)"}')
    print(f'   Style:    {args.style}')
    print(f'   Output:   {output_path}')
    print(f'')

    try:
        # Generate image
        image_bytes = generate_image_fal(prompt, api_key, args.width, args.height)

        if args.no_overlay:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)
            print(f'  ✅ Raw image saved: {output_path}')
        else:
            overlay_branding(image_bytes, args.title, args.subtitle, output_path, args.width, args.height)

        print(f'')
        print(f'✅ Done — {output_path}')

    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
