#!/usr/bin/env python3
"""
Post a tweet to @finksecurity via X API using tweepy OAuth 1.0a.
Usage: python3 post-tweet.py "tweet text here" [--dry-run]
"""

import sys
import os
import tweepy

def load_credentials():
    """Load X API credentials from ~/.openclaw/workspace/secrets.env"""
    env_file = os.path.expanduser("~/.openclaw/workspace/secrets.env")
    credentials = {}
    
    if not os.path.exists(env_file):
        raise FileNotFoundError(f"Credentials file not found: {env_file}")
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('X_API_KEY='):
                credentials['api_key'] = line.split('=', 1)[1].strip('"\'')
            elif line.startswith('X_API_SECRET='):
                credentials['api_secret'] = line.split('=', 1)[1].strip('"\'')
            elif line.startswith('X_ACCESS_TOKEN='):
                credentials['access_token'] = line.split('=', 1)[1].strip('"\'')
            elif line.startswith('X_ACCESS_TOKEN_SECRET='):
                credentials['access_token_secret'] = line.split('=', 1)[1].strip('"\'')
    
    required = ['api_key', 'api_secret', 'access_token', 'access_token_secret']
    missing = [k for k in required if k not in credentials]
    
    if missing:
        raise ValueError(f"Missing X API credentials in ~/.openclaw/.env: {', '.join(missing)}")
    
    return credentials

def post_tweet(tweet_text, dry_run=False):
    """
    Post a tweet to @finksecurity via X API.
    
    Args:
        tweet_text: The tweet content to post (max 280 chars)
        dry_run: If True, validate and preview without posting
    
    Returns:
        dict with 'success' bool and 'url' or 'error'
    """
    
    # Validate tweet length
    if len(tweet_text) > 280:
        return {
            'success': False,
            'error': f"Tweet is {len(tweet_text)} characters, max 280"
        }
    
    if dry_run:
        # DRY RUN: Validate credentials and preview tweet
        print(f"[DRY RUN] Tweet validation:")
        print(f"  Length: {len(tweet_text)}/280 characters")
        print(f"\n  Content preview:")
        print(f"  ─" * 40)
        print(f"  {tweet_text}")
        print(f"  ─" * 40)
        
        # Check if credentials are configured
        try:
            creds = load_credentials()
            print(f"\n  ✓ X API credentials loaded successfully")
            print(f"  ✓ API Key: {creds['api_key'][:10]}...")
            print(f"  ✓ Access Token: {creds['access_token'][:10]}...")
        except Exception as e:
            print(f"\n  ✗ Credential error: {e}")
            print(f"    Add X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN,")
            print(f"    and X_ACCESS_TOKEN_SECRET to ~/.openclaw/workspace/secrets.env")
            return {
                'success': False,
                'error': str(e),
                'dry_run': True
            }
        
        print(f"\n[DRY RUN] Ready to post. Run without --dry-run to post live.\n")
        return {
            'success': True,
            'url': None,
            'dry_run': True,
            'message': 'Dry run validation successful'
        }
    
    # LIVE MODE: Load credentials and post
    try:
        creds = load_credentials()
    except Exception as e:
        return {'success': False, 'error': f"Failed to load credentials: {e}"}
    
    try:
        print("[*] Initializing X API client...")
        
        # Initialize tweepy client with OAuth 1.0a
        client = tweepy.Client(
            consumer_key=creds['api_key'],
            consumer_secret=creds['api_secret'],
            access_token=creds['access_token'],
            access_token_secret=creds['access_token_secret']
        )
        
        print("[*] Authenticating with X API...")
        # Verify credentials work
        me = client.get_me()
        username = me.data.username
        print(f"[*] Authenticated as: @{username}")
        
        print(f"[*] Posting tweet...")
        response = client.create_tweet(text=tweet_text)
        
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/{username}/status/{tweet_id}"
        
        print(f"[✓] Tweet posted successfully!")
        print(f"    URL: {tweet_url}")
        
        return {
            'success': True,
            'url': tweet_url,
            'tweet_id': tweet_id,
            'message': 'Tweet posted successfully'
        }
    
    except tweepy.TweepyException as e:
        return {
            'success': False,
            'error': f"X API error: {e}",
            'message': f'Failed to post tweet: {e}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to post tweet: {e}'
        }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 post-tweet.py 'tweet text here' [--dry-run]")
        print("       python3 post-tweet.py 'text' --dry-run    # Validate without posting")
        sys.exit(1)
    
    tweet_text = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    print(f"Tweet content: {tweet_text}\n")
    
    result = post_tweet(tweet_text, dry_run=dry_run)
    
    if result['success']:
        print(f"\n✓ Success: {result.get('message')}")
        if result.get('url'):
            print(f"  URL: {result['url']}")
    else:
        print(f"\n✗ Error: {result.get('error')}")
        if not dry_run:
            sys.exit(1)
