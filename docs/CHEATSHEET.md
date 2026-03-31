# Fink Security / ESTHER — Command Cheat Sheet

Quick reference for OpenClaw, GitHub, Hugo, and ESTHER operations.

---

## OpenClaw

### Gateway Management

```bash
# Start gateway (survives SSH disconnect)
nohup openclaw gateway --force > ~/.openclaw/logs/gateway.log 2>&1 & disown

# Check if gateway is running
ps aux | grep openclaw-gatewa | grep -v grep

# Tail live gateway logs
tail -f ~/.openclaw/logs/gateway.log

# Tail logs filtered to memory activity only
tail -f ~/.openclaw/logs/gateway.log | grep -i "memory\|embed\|capture\|recall\|lancedb"

# Check gateway health
openclaw health

# View current config
python3 -m json.tool ~/.openclaw/openclaw.json
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

# Tail logs for LanceDB  memory events
tail -f ~/.openclaw/logs/gateway.log | grep -i "memory\|embed\|capture\|recall\|lancedb"
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
```

### Models

```bash
# List configured models
openclaw models list

# Scan for available models
openclaw models scan
```

### Channels

```bash
# Check Telegram connection status
openclaw status

# View channel health
openclaw channels list
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

# Reinstall LanceDB npm module
sudo npm install --save @lancedb/lancedb /usr/lib/node_modules/openclaw/extensions/memory-lancedb

# Check crontab
crontab -l

# Add gateway reboot entry
(crontab -l | grep -v openclaw; echo "@reboot nohup openclaw gateway > ~/.openclaw/logs/gateway.log 2>&1 & disown") | crontab -
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
```

### SHA Verification (ESTHER fabrication check)

```bash
# Run esther-verify.py option 14
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

# Check what Hugo generated
ls ~/estherops-site/public/posts/
ls ~/estherops-site/public/reports/
ls ~/estherops-site/public/methods/
ls ~/estherops-site/public/intelligence/
ls ~/estherops-site/public/labs/

# Verify a post URL is live
curl -sk -o /dev/null -w "%{http_code}" https://estherops.tech/reports/<slug>/
curl -sk -o /dev/null -w "%{http_code}" https://estherops.tech/methods/<slug>/
```

### Content Directory Rules

```
content/reports/      → type: reports    (bug bounty, engagement summaries)
content/methods/      → type: methods    (techniques, tooling, how-tos)
content/intelligence/ → type: intelligence (OSINT, recon findings)
content/labs/         → type: labs       (DVWA, Juice Shop exercises)
```

### Required Frontmatter

```yaml
---
title: "Your Post Title"
date: 2026-03-30T12:00:00Z
type: reports
categories: ["Reports"]
---
```

### Deployment

```bash
# Hugo auto-deploys via GitHub Actions on push to main
# Check Action status
gh run list --repo FinkSecurity/estherops-site --limit 3

# Force rebuild (push any change)
cd ~/estherops-site
git commit --allow-empty -m "chore: trigger rebuild"
git push
```

### Troubleshooting 404s

```bash
# Check if file is in wrong directory
ls ~/estherops-site/content/posts/ | grep <slug>   # should be empty
ls ~/estherops-site/content/reports/ | grep <slug>  # should be here

# Check frontmatter type field matches directory
head -6 ~/estherops-site/content/reports/<slug>.md

# Check GitHub Action ran successfully
gh run list --repo FinkSecurity/estherops-site --limit 3
```

---

## ESTHER Scripts

### Core Scripts

```bash
# System health check
python3 ~/esther-lab/scripts/esther-verify.py

# Commit helper (always use this instead of raw git commit)
bash ~/esther-lab/scripts/esther-commit.sh "commit message"

# Generate daily mission brief
python3 ~/esther-lab/scripts/generate-briefing.py

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

# Manual task dispatch test
python3 ~/poll-tasks.py
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

# Check task poller log
cat ~/.openclaw/workspace/logs/task-poller.log | tail -20
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
| SOUL.md | `~/esther-lab/SOUL.md` | ESTHER behavior rules |
| ENVIRONMENT.md | `~/.openclaw/ENVIRONMENT.md` | Infrastructure facts |
| ACTIVE-ENGAGEMENT.md | `~/.openclaw/workspace/ACTIVE-ENGAGEMENT.md` | Current engagement scope |
| secrets.env | `~/.openclaw/workspace/secrets.env` | API keys (never commit) |
| openclaw.json | `~/.openclaw/openclaw.json` | OpenClaw config |
| gateway.log | `~/.openclaw/logs/gateway.log` | Live gateway logs |
| task-poller.log | `~/.openclaw/workspace/logs/task-poller.log` | Task dispatch log |

---

*Last updated: 2026-03-30*
