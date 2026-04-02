# Fink Security / ESTHER — Command Cheat Sheet

Quick reference for OpenClaw, GitHub, Hugo, ESTHER, and Ezra operations.

---

## OpenClaw

### Gateway Management

```bash
# Start gateway (survives SSH disconnect) — VPS
nohup openclaw gateway --force > ~/.openclaw/logs/gateway.log 2>&1 & disown

# Restart gateway — Mac
openclaw gateway restart

# Check if gateway is running
ps aux | grep openclaw-gatewa | grep -v grep

# Tail live gateway logs (VPS)
tail -f ~/.openclaw/logs/gateway.log

# Tail live gateway logs (Mac)
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log

# Tail logs filtered to memory activity only
tail -f ~/.openclaw/logs/gateway.log | grep -i "memory\|embed\|capture\|recall\|lancedb"

# Check gateway health
openclaw health

# View current config
python3 -m json.tool ~/.openclaw/openclaw.json
```

### Sessions

```bash
# Check active sessions and which model they are using
openclaw status | grep -A8 "Sessions"

# Clear all active sessions (reset context window)
rm ~/.openclaw/agents/main/sessions/sessions.json
openclaw gateway restart
```

### Memory

```bash
# Check memory status
openclaw memory status

# Force reindex
openclaw memory index --force

# Search memory
openclaw memory search --query "your search term"

# Check LanceDB initialized (look for this line)
grep "memory-lancedb: initialized" ~/.openclaw/logs/gateway.log

# Check which memory plugin is active
openclaw plugins list | grep memory

# Verify LanceDB npm module loads correctly (Mac)
node -e "require('@lancedb/lancedb')"
```

### Plugins

```bash
# List all plugins
openclaw plugins list

# Enable a plugin
openclaw plugins enable memory-lancedb

# Disable a plugin
openclaw plugins disable memory-core

# Get plugin info
openclaw plugins info memory-lancedb
```

### Skills

```bash
# List all available skills
openclaw skills list

# Install a skill via ClawHub
npx clawhub install <skill-name>

# Search ClawHub for a skill
npx clawhub search <skill-name>
```

### Models

```bash
# List configured models
openclaw models list

# Scan for available models
openclaw models scan

# Fix model priority (local first, OpenRouter fallback only)
python3 -c "
import json
from pathlib import Path
p = Path('~/.openclaw/openclaw.json').expanduser()
c = json.loads(p.read_text())
c['agents']['defaults']['model'] = {
    'primary': 'ollama/qwen2.5:14b',
    'fallbacks': ['openrouter/anthropic/claude-haiku-4.5']
}
p.write_text(json.dumps(c, indent=4))
print('Done')
"
```

### Config

```bash
# Validate config file
openclaw config validate

# Get a specific config value
openclaw config get agents.defaults.contextTokens

# Set context window to 32k
python3 -c "
import json; from pathlib import Path
p = Path('~/.openclaw/openclaw.json').expanduser()
c = json.loads(p.read_text())
c['agents']['defaults']['contextTokens'] = 32000
p.write_text(json.dumps(c, indent=4))
print('Done')
"

# Update workspace path
python3 -c "
import json
from pathlib import Path
p = Path('~/.openclaw/openclaw.json').expanduser()
c = json.loads(p.read_text())
c['agents']['defaults']['workspace'] = '~/tools/ezra-lab'
p.write_text(json.dumps(c, indent=4))
print('Done')
"
```

### Security

```bash
# Run security audit
openclaw security audit

# Run deep security audit
openclaw security audit --deep
```

### Troubleshooting

```bash
# Run health checks
openclaw doctor

# Check recent logs for errors
grep -i "error\|warn\|fail" ~/.openclaw/logs/gateway.log | tail -20

# Check Ollama models loaded
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Pull a model into Ollama
curl -s http://localhost:11434/api/pull -d '{"name":"nomic-embed-text"}'
curl -s http://localhost:11434/api/pull -d '{"name":"llama3.2:3b"}'
curl -s http://localhost:11434/api/pull -d '{"name":"qwen2.5:14b"}'

# Reinstall LanceDB npm module (VPS)
sudo npm install --save @lancedb/lancedb /usr/lib/node_modules/openclaw/extensions/memory-lancedb

# Reinstall LanceDB npm module (Mac)
sudo npm install --save @lancedb/lancedb /opt/homebrew/lib/node_modules/openclaw/dist/extensions/memory-lancedb

# Check crontab
crontab -l

# Add gateway reboot entry
(crontab -l | grep -v openclaw; echo "@reboot nohup openclaw gateway > ~/.openclaw/logs/gateway.log 2>&1 & disown") | crontab -

# Send test Telegram notification (no operator spam)
python3 ~/esther-lab/scripts/esther-verify.py --test-notify
```

---

## GitHub / Git

### ESTHER Commit Workflow (always use this)

```bash
# Always commit from the correct repo directory
cd ~/esther-lab          # for findings, scripts, SOUL.md
cd ~/estherops-site      # for blog posts
cd ~/finksecurity-site   # for company website

# Use esther-commit.sh (handles verification)
bash ~/esther-lab/scripts/esther-commit.sh "your commit message"

# Verify the commit is real
git rev-parse HEAD
gh api repos/FinkSecurity/esther-lab/commits/$(git rev-parse HEAD) \
  --jq '{sha: .sha[:9], message: .commit.message, files: [.files[].filename]}'
```

### Common Git Operations

```bash
# Check status
git status
git log --oneline -5

# Safe pull before pushing (always do this for finksecurity-site)
git pull --rebase origin main

# Push
git push

# Check what's on remote vs local
git log --oneline origin/main -5

# Undo last commit (keep changes)
git reset HEAD~1

# See what changed in last commit
git show --stat HEAD
```

### GitHub CLI (gh)

```bash
# Verify a commit SHA against GitHub
gh api repos/FinkSecurity/esther-lab/commits/<sha> \
  --jq '{sha: .sha[:9], message: .commit.message, files: [.files[].filename]}'

# List recent workflow runs
gh run list --repo FinkSecurity/estherops-site --limit 5

# Check GitHub Pages deployment status
gh api repos/FinkSecurity/finksecurity-site/pages \
  --jq '{branch: .source.branch, status: .status}'

# View repo contents
gh api repos/FinkSecurity/esther-lab/contents/scripts \
  --jq '[.[].name]'

# Re-authenticate gh CLI
gh auth login
```

### SHA Verification (ESTHER fabrication check)

```bash
# Run esther-verify.py
python3 ~/esther-lab/scripts/esther-verify.py

# Manual SHA check
gh api repos/FinkSecurity/esther-lab/commits/<sha> 2>&1 | grep -i "sha\|message\|422"
# 422 = fabricated, real SHA returns JSON
```

---

## Hugo (estherops.tech)

### Local Build & Test

```bash
# Build site
cd ~/estherops-site && hugo

# Verify a post URL is live
curl -sk -o /dev/null -w "%{http_code}" https://estherops.tech/reports/<slug>/
curl -sk -o /dev/null -w "%{http_code}" https://estherops.tech/methods/<slug>/
```

### Content Directory Rules

```
content/reports/      → type: reports
content/methods/      → type: methods
content/intelligence/ → type: intelligence
content/labs/         → type: labs
```

### Required Frontmatter

```yaml
---
title: "Your Post Title"
date: 2026-03-30T12:00:00Z
type: methods
categories: ["Methods"]
---
```

### Deployment

```bash
# Hugo auto-deploys via GitHub Actions on push to main
gh run list --repo FinkSecurity/estherops-site --limit 3

# Force rebuild
cd ~/estherops-site
git commit --allow-empty -m "chore: trigger rebuild"
git push
```

### Troubleshooting 404s

```bash
# Check frontmatter type field matches directory
head -6 ~/estherops-site/content/methods/<slug>.md

# Check GitHub Action ran successfully
gh run list --repo FinkSecurity/estherops-site --limit 3
```

---

## ESTHER Scripts

### Core Scripts

```bash
# System health check
python3 ~/esther-lab/scripts/esther-verify.py

# Send test Telegram notification
python3 ~/esther-lab/scripts/esther-verify.py --test-notify

# Commit helper
bash ~/esther-lab/scripts/esther-commit.sh "commit message"

# Generate daily mission brief
python3 ~/.openclaw/workspace/scripts/generate-briefing.py

# Load engagement scope
python3 ~/esther-lab/scripts/load-scope.py x

# Post tweet to @finksecurity
python3 ~/esther-lab/scripts/post-tweet.py "tweet text here"

# Dry run tweet (validate without posting)
python3 ~/esther-lab/scripts/post-tweet.py "tweet text" --dry-run

# Run HIBP breach check
python3 ~/esther-lab/scripts/hibp-check.py email@example.com --out /tmp/output/

# Generate Personal Exposure Report PDF
python3 ~/esther-lab/scripts/generate-exposure-report.py \
  --email client@example.com \
  --name "Client Name" \
  --hibp /path/to/hibp-output.json \
  --out /path/to/output/

# Run Home Network Security Check
python3 ~/esther-lab/scripts/home-network-check.py \
  --ip 1.2.3.4 \
  --name "Client Name" \
  --email client@example.com \
  --out /tmp/output/

# Manual task dispatch test
python3 ~/finksecurity-notify/poll-tasks.py
```

### Stripe / Payment Pipeline

```bash
# Test webhook with Stripe CLI
stripe listen --forward-to https://api.finksecurity.com/stripe-webhook
stripe trigger checkout.session.completed

# Check handler is running
ps aux | grep handler.py | grep -v grep

# Check pending tasks
ls -la ~/tasks_pending/
cat ~/tasks_pending/*.json
```

### Services Status

```bash
# Check all services
python3 ~/esther-lab/scripts/esther-verify.py

# Check Docker services
docker ps

# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check gunicorn services
ps aux | grep gunicorn | grep -v grep

# Restart notify service (port 5001)
pkill -f notify.py && sleep 1 && cd ~/finksecurity-notify && gunicorn -w 1 -b 0.0.0.0:5001 notify:app --daemon

# Restart handler service (port 5002)
pkill -f handler.py && sleep 1 && cd ~/finksecurity-notify && gunicorn -w 1 -b 0.0.0.0:5002 handler:app --daemon
```

---

## Engagement Management

```bash
# Check engagement STATUS
cat ~/esther-lab/engagements/public/x/STATUS
cat ~/esther-lab/engagements/public/playtika/STATUS

# Set engagement status
echo "active"    > ~/esther-lab/engagements/public/x/STATUS
echo "paused"    > ~/esther-lab/engagements/public/playtika/STATUS
echo "cancelled" > ~/esther-lab/engagements/public/playtika/STATUS

# Reload active engagement scope
python3 ~/esther-lab/scripts/load-scope.py x

# Regenerate mission brief
python3 ~/.openclaw/workspace/scripts/generate-briefing.py
```

---

## Ezra (Mac Media Agent)

```bash
# Check Ezra gateway status
openclaw gateway status

# Verify Ezra is using local model (should be qwen2.5:14b not OpenRouter)
openclaw status | grep -A8 "Sessions"

# Check Luminar Neo is scriptable via AppleScript
osascript -e 'tell application "Luminar Neo" to get version'

# Generate thumbnail via Ezra's script
python3 ~/tools/ezra-lab/scripts/make_thumbnail.py "Title" "Subtitle" "~/tools/ezra-lab/media/output/output.png"

# Check Ezra output directory
ls ~/tools/ezra-lab/media/output/

# Tail Ezra gateway log
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

---

## VPS Access

```bash
# SSH to ESTHER's VPS
ssh -p 2222 esther@45.82.72.151

# SCP file TO VPS
scp -P 2222 ~/local/file.py esther@45.82.72.151:~/esther-lab/scripts/file.py

# SCP file FROM VPS
scp -P 2222 esther@45.82.72.151:/tmp/report.pdf ~/Downloads/

# Check disk usage
df -h
du -sh ~/esther-lab/ ~/.openclaw/

# Check memory
free -h

# Check running processes
ps aux | grep -E "gunicorn|openclaw|poll-tasks|notify" | grep -v grep
```

---

## Telegram Operator Commands

```
EXECUTE <job_id>     — approve and run a pending task
CANCEL <job_id>      — decline a pending task
APPROVE <task_id>    — approve contact form engagement
DENY <task_id>       — decline contact form engagement
```

---

## Key File Locations

| File | Path | Purpose |
|------|------|---------|
| SOUL.md (ESTHER) | `~/esther-lab/SOUL.md` | ESTHER behavior rules |
| SOUL.md (Ezra) | `~/tools/ezra-lab/SOUL.md` | Ezra behavior rules |
| ENVIRONMENT.md | `~/.openclaw/ENVIRONMENT.md` | Infrastructure facts |
| ACTIVE-ENGAGEMENT.md | `~/.openclaw/workspace/ACTIVE-ENGAGEMENT.md` | Current engagement scope |
| secrets.env | `~/.openclaw/workspace/secrets.env` | API keys (never commit) |
| openclaw.json (VPS) | `~/.openclaw/openclaw.json` | ESTHER OpenClaw config |
| openclaw.json (Mac) | `~/.openclaw/openclaw.json` | Ezra OpenClaw config |
| gateway.log (VPS) | `~/.openclaw/logs/gateway.log` | ESTHER live gateway logs |
| gateway.log (Mac) | `/tmp/openclaw/openclaw-YYYY-MM-DD.log` | Ezra live gateway logs |
| task-poller.log | `~/.openclaw/workspace/logs/task-poller.log` | Task dispatch log |
| make_thumbnail.py | `~/tools/ezra-lab/scripts/make_thumbnail.py` | Ezra thumbnail generator |

---

*Last updated: 2026-04-02*
