---
title: "OpenClaw on a VPS: A Complete Beginner's Setup Guide"
date: 2026-03-06
type: "posts"
description: "Step-by-step guide to deploying OpenClaw on a Hostinger VPS with Telegram integration, WordPress connection, and AI model cost optimization. No prior Linux experience required."
tags: ["openclaw", "vps", "telegram", "wordpress", "ai-agent", "tutorial"]
---

*Hostinger Cloud VPS · Telegram Integration · WordPress Connection · No prior Linux experience required.*

**What this guide covers:**
- Setting up a Hostinger cloud VPS
- Installing OpenClaw
- Connecting Telegram so you can chat with it
- Connecting OpenClaw to your WordPress site
- Keeping it running 24/7
- Reducing API costs by up to 97%

---

> ⚠️ **A Note on Windows VPS**
>
> Hostinger does offer Windows VPS plans, but they are not recommended for OpenClaw for two reasons:
> - **Cost:** Windows VPS plans cost approximately 3x more than equivalent Linux plans.
> - **Compatibility:** OpenClaw is built and tested for Linux. Running it on Windows adds unnecessary complexity.
>
> **This guide uses Ubuntu 22.04 (Linux). You do not need any prior Linux experience — just follow each step exactly as written.**

---

## Before You Start

Before diving in, make sure you have the following ready:

| Item | What it is | Cost |
|------|-----------|------|
| Hostinger account | The company that provides your cloud server | ~$6-10/month |
| Credit/debit card | To pay for the VPS subscription | — |
| OpenClaw license | The AI agent software you'll be installing | Per OpenClaw pricing |
| Telegram account | Free messaging app used to chat with OpenClaw | Free |
| OpenRouter API key | Connects OpenClaw to the AI brain (Claude/GPT) | Pay-as-you-go |
| 20-30 minutes | Time to complete the setup | — |

> 💡 **What is a VPS?**
> A VPS (Virtual Private Server) is your own private computer in the cloud. It runs 24/7 even when your laptop is off. Think of it like renting a small always-on computer that lives in a data center and is accessible from anywhere.

---

## Part 1: Set Up Your Hostinger VPS

### 1.1 Create a Hostinger Account

1. Go to hostinger.com in your browser
2. Click **Get Started** or **Hosting** in the top menu
3. Choose **VPS Hosting** from the menu
4. Select the **KVM 2** plan (recommended — gives you enough power for OpenClaw)
5. Create your account with your email address and a strong password
6. Complete payment with your credit card

> 💡 **Which plan to choose?**
> The KVM 2 plan (2 CPU cores, 8GB RAM) works well for OpenClaw. If you plan to run other tools alongside it, consider KVM 4. You can always upgrade later.

### 1.2 Create Your Server

After purchasing, Hostinger will ask you to set up your server:

7. Go to your Hostinger dashboard at hpanel.hostinger.com
8. Click **VPS** in the left menu
9. Click your new VPS to open its settings
10. Under **Operating System**, select **Ubuntu 22.04 LTS**
11. Set a root password — write this down somewhere safe
12. Click **Create Server** and wait 2-3 minutes for it to be ready

> ⚠️ **Write down your password!**
> The root password you set here is like the master key to your server. Store it in a password manager or write it down in a safe place. If you lose it, you'll need to reset your entire server.

### 1.3 Find Your Server's IP Address

Your server has an IP address — think of it as its home address on the internet.

13. In the Hostinger VPS dashboard, look for your server
14. You'll see a number like `45.82.72.151` — this is your IP address
15. Write it down or copy it somewhere handy

### 1.4 Connect to Your Server

**On Windows (Primary):**

16. Download and install PuTTY from putty.org — it is free
17. Open PuTTY from your Start menu
18. In the **Host Name** field, type your server IP address
19. Make sure **Port** is set to `22` and **Connection type** is SSH
20. Click **Open**
21. Click **Accept** if a security warning pops up
22. At the login prompt type: `root` and press Enter
23. Enter your root password (nothing will appear as you type — this is normal)
24. You are in! You will see a line ending in `#` which means the server is ready

> 💡 **Right-click to paste in PuTTY**
> PuTTY uses right-click to paste text — not Ctrl+V. To copy text from PuTTY, just highlight it with your mouse and it copies automatically.

**On Mac (if applicable):**

25. Open the Terminal app (press Cmd + Space, type Terminal, press Enter)
26. Type the following command, replacing YOUR_IP with your server IP address:

```bash
ssh root@YOUR_IP
```

27. Press Enter, type `yes` if asked about fingerprint
28. Enter your root password when asked

---

## Part 2: Prepare the Server

### 2.1 Update the Server

```bash
apt update
apt upgrade -y
```

This may take a few minutes. Wait until you see the prompt again before continuing.

### 2.2 Install Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

Verify it installed correctly:

```bash
node --version
npm --version
```

You should see version numbers like `v20.x.x`.

### 2.3 Install Git

```bash
apt install -y git
```

### 2.4 Create a Regular User (Optional but Recommended)

Running everything as root is not ideal for security. Create a regular user:

```bash
adduser yournamehere
usermod -aG sudo yournamehere
```

Replace `yournamehere` with whatever username you want.

### 2.5 Set Up a Basic Firewall

```bash
ufw allow ssh
ufw allow 22
ufw enable
```

Type `y` and press Enter when asked to confirm.

> 💡 **What just happened?**
> UFW (Uncomplicated Firewall) is now blocking all incoming connections except SSH (port 22). This is sensible default protection for any internet-facing server.

---

## Part 3: Install OpenClaw

### 3.1 Install OpenClaw

```bash
npm install -g openclaw
```

Verify it installed:

```bash
openclaw --version
```

### 3.2 Create Your Workspace

```bash
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw
```

### 3.3 Get Your OpenRouter API Key

OpenRouter is the service that connects OpenClaw to AI models like Claude. You need an API key:

1. Go to openrouter.ai in your browser
2. Click **Sign Up** and create a free account
3. Go to **Keys** in the dashboard
4. Click **Create Key**, give it a name like `my-openclaw`
5. Copy the key — it starts with `sk-or-v1-...`
6. Save it somewhere safe — you'll need it in the next step

> 💡 **How much credit to add?**
> Start with $5-10. OpenClaw is very efficient and this amount will last weeks or months of normal use. You can check your spending anytime at openrouter.ai/activity.

> ⚠️ **Keep your API key private**
> Never share your API key or commit it to GitHub. Anyone with your key can use your API credits.

### 3.4 Configure OpenClaw

```bash
nano ~/.openclaw/openclaw.json
```

Paste this configuration, replacing the placeholder values:

```json
{
  "model": "anthropic/claude-haiku-4-5",
  "apiKey": "YOUR_OPENROUTER_API_KEY",
  "agents": {
    "defaults": {
      "sandbox": { "mode": "off" }
    }
  },
  "tools": {
    "fs": { "workspaceOnly": false }
  }
}
```

Save with Ctrl+X, then Y, then Enter.

### 3.5 Test OpenClaw

```bash
openclaw start
```

You should see OpenClaw start up without errors. Press Ctrl+C to stop it for now.

---

## Part 4: Set Up Telegram

### 4.1 Create Your Telegram Bot

1. Open Telegram on your phone or computer
2. Search for **@BotFather**
3. Start a conversation and type `/newbot`
4. Give your bot a name (e.g. `My OpenClaw Assistant`)
5. Give it a username ending in `bot` (e.g. `myopenclaw_bot`)
6. BotFather will give you a token — copy it, it looks like `123456789:ABCdefGHI...`

### 4.2 Get Your Chat ID

1. Search for **@userinfobot** in Telegram
2. Start a conversation — it will immediately reply with your user ID
3. Copy that number — this is your Chat ID

### 4.3 Install the Telegram Skill

```bash
openclaw skill install telegram
```

### 4.4 Configure Telegram

Update your `openclaw.json`:

```bash
nano ~/.openclaw/openclaw.json
```

Add the Telegram section:

```json
{
  "model": "anthropic/claude-haiku-4-5",
  "apiKey": "YOUR_OPENROUTER_API_KEY",
  "telegram": {
    "botToken": "YOUR_BOT_TOKEN",
    "allowedChatIds": [YOUR_CHAT_ID]
  },
  "agents": {
    "defaults": {
      "sandbox": { "mode": "off" }
    }
  },
  "tools": {
    "fs": { "workspaceOnly": false }
  }
}
```

### 4.5 Test Telegram

```bash
openclaw start
```

Open Telegram, find your bot, and send it a message. You should get a reply within a few seconds.

---

## Part 5: Keep OpenClaw Running 24/7

Right now, if you close your PuTTY window, OpenClaw stops. We need to set it up to run permanently in the background.

> 💡 **What is PM2 and why do we need it?**
> PM2 is a process manager — a program that watches your other programs and keeps them running. Without PM2, OpenClaw stops the moment you close PuTTY. With PM2, OpenClaw runs as a background service that survives disconnects, restarts, and reboots automatically. Think of it like setting a program to start automatically with Windows — except for your cloud server.

### 5.1 Install PM2

```bash
npm install -g pm2
```

### 5.2 Start OpenClaw with PM2

```bash
pm2 start "openclaw start" --name openclaw
pm2 save
pm2 startup
```

The last command (`pm2 startup`) will print a command for you to copy and run. Copy that entire line, paste it into the terminal, and press Enter.

### 5.3 Useful PM2 Commands

| Command | What it does |
|---------|-------------|
| `pm2 status` | Check if OpenClaw is running |
| `pm2 logs openclaw` | See recent activity and messages |
| `pm2 restart openclaw` | Restart OpenClaw (after config changes) |
| `pm2 stop openclaw` | Stop OpenClaw |
| `pm2 start openclaw` | Start OpenClaw again |

---

## Part 5B: Set Up the AI Model Hierarchy

By default OpenClaw uses a single expensive AI model for everything. Setting up a three-tier model hierarchy reduces your API costs by up to 80%.

| Tier | Used for | Cost |
|------|---------|------|
| Ollama (local) | Heartbeat pings — keeping the agent alive | Free |
| Claude Haiku | Routine tasks: simple questions, quick lookups | ~$0.25/million tokens |
| Claude Sonnet | Complex work: writing articles, research, analysis | ~$3/million tokens |

### 5B.1 Install Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b
```

Verify it works:

```bash
ollama run llama3.2:3b "Hello"
```

Type `/bye` to exit.

### 5B.2 Update OpenClaw Config for Three-Tier Routing

```bash
nano ~/.openclaw/openclaw.json
```

Replace the entire contents with:

```json
{
  "model": "anthropic/claude-haiku-4-5",
  "apiKey": "YOUR_OPENROUTER_API_KEY",
  "telegram": {
    "botToken": "YOUR_BOT_TOKEN",
    "allowedChatIds": [YOUR_CHAT_ID]
  },
  "models": {
    "default": "anthropic/claude-haiku-4-5",
    "powerful": "anthropic/claude-sonnet-4-5",
    "heartbeat": "ollama/llama3.2:3b"
  },
  "heartbeat": {
    "model": "ollama/llama3.2:3b",
    "intervalMinutes": 60
  },
  "agents": {
    "defaults": {
      "sandbox": { "mode": "off" }
    }
  },
  "tools": {
    "fs": { "workspaceOnly": false }
  }
}
```

Save and restart:

```bash
pm2 restart openclaw
```

> ⚠️ **Model names may change**
> If OpenClaw reports a model name is not found, check openrouter.ai/models and search for 'haiku' or 'sonnet' to find the current model ID.

---

## Part 6: Connect to WordPress

### 6.1 Install the WordPress Skill

```bash
openclaw skill install wordpress
```

### 6.2 Create a WordPress Application Password

In your WordPress dashboard:

1. Go to **Users → Profile**
2. Scroll down to **Application Passwords**
3. Enter a name like `OpenClaw`
4. Click **Add New Application Password**
5. Copy the password that appears — you won't see it again

### 6.3 Configure WordPress

```bash
nano ~/.openclaw/openclaw.json
```

Add the WordPress section:

```json
"wordpress": {
  "url": "https://yoursite.com",
  "username": "your-wordpress-username",
  "applicationPassword": "xxxx xxxx xxxx xxxx xxxx xxxx"
}
```

### 6.4 Test WordPress Connection

Send your bot a message in Telegram:

```
What WordPress posts do I have?
```

You should get a list of your recent posts.

---

## Part 7: Troubleshooting

| Problem | Solution |
|---------|---------|
| Can't connect via SSH | Check your IP address is correct. Make sure you're using port 22. Try waiting 5 minutes if you just created the server. |
| OpenClaw won't start | Run `openclaw start` directly (not via PM2) to see error messages. Check your API key in openclaw.json. |
| Telegram bot not responding | Check your bot token and chat ID in openclaw.json. Make sure there are no extra spaces. Run `pm2 logs openclaw` to see error messages. |
| OpenClaw stopped working | Run `pm2 status` to check. If it shows "stopped", run `pm2 start openclaw`. Check `pm2 logs openclaw` for error details. |
| WordPress not connecting | Double-check your site URL includes https://. Verify the application password has spaces in it (WordPress format). |

### Quick Diagnostic Commands

```bash
pm2 status                    # Is OpenClaw running?
pm2 logs openclaw             # See what it's doing
pm2 logs openclaw --lines 50  # See last 50 lines
openclaw --version            # Check version
node --version                # Check Node.js
```

---

## Part 8: Your First Conversation

### Step 1 — Introduce Yourself

```
Hi! My name is [YOUR NAME]. I run a website called [SITE NAME] at [URL].
It's about [WHAT YOUR SITE IS ABOUT]. My audience is [WHO READS IT].
I'd like you to help me with content, research, and managing my site.
```

### Step 2 — Test Basic Capabilities

| Send this message | What it tests |
|------------------|--------------|
| `What is today's date?` | Basic response — confirms agent is running |
| `Can you list my recent WordPress posts?` | WordPress connection |
| `Write me a one-paragraph summary of what my website is about.` | Memory — tests if it remembered your introduction |
| `What tools and skills do you have available?` | Self-awareness |
| `Suggest 3 blog post ideas for my audience.` | Creative help |

### Step 3 — Give It a Real Task

- 'Draft a short blog post about [topic related to your site]'
- 'What WordPress plugins do I have installed?'
- 'Summarize my last 5 blog posts in one sentence each'
- 'Suggest improvements to my About page'

> 💡 **Training tip**
> The more you use your agent and correct it when it gets things wrong, the better it gets. Think of the first few weeks as a training period.

---

## Appendix: Token Optimization — Reduce Costs by 97%

By default, OpenClaw can cost $70-90/month or more in API fees. Five simple optimizations bring this down to $3-5/month.

| # | Optimization | Without | With |
|---|-------------|---------|------|
| 1 | Session Initialization | 50KB context on startup | 8KB context on startup |
| 2 | Model Routing (Haiku default) | $50-70/month on models | $5-10/month on models |
| 3 | Heartbeat via local model | 1,440 paid API calls/day | $0 for heartbeats |
| 4 | Rate limits & budget caps | Surprise bills possible | $5/day hard cap |
| 5 | Prompt caching | Full cost every message | 90% discount on static content |

> 💰 **Combined result:** Without optimizations: ~$90/month. With all five: ~$4/month. That is a 97% reduction.

### SOUL.md Template — Copy This to Your Agent

Create this file at: `~/.openclaw/workspace/SOUL.md`

```bash
nano ~/.openclaw/workspace/SOUL.md
```

Paste this template and edit the `[CUSTOMIZE]` sections:

```markdown
# SOUL.md — Agent Identity & Operating Rules

## 0. SESSION START
Read this file completely before responding to any message.

## 1. WHO YOU ARE
You are [AGENT NAME] — an AI assistant working for [OPERATOR NAME].
Your primary job is to help manage and grow [WEBSITE/BUSINESS NAME].
You communicate via Telegram and have access to WordPress.

## 2. YOUR PERSONALITY
- Helpful, friendly, and concise in Telegram messages
- Professional and thorough in written content
- Always honest — say when you don't know something
- Ask for clarification rather than guess

## 3. WORDPRESS RULES
- Never publish content without explicit operator approval
- Save drafts for review, do not auto-publish
- Always confirm before making changes to site settings

## 4. MODEL SELECTION (COST CONTROL)
Default: Use the cheapest available model for routine tasks.
Upgrade to a better model ONLY for: complex writing, research synthesis,
analysis requiring deep reasoning, or when operator requests it.

## 5. RATE LIMITS (COST CONTROL)
- Minimum 5 seconds between API calls
- Minimum 10 seconds between web searches
- Maximum 5 searches per session, then pause and report
- Daily budget: $5 hard limit. Warn operator at $3.75.
- Monthly budget: $50 hard limit. Warn operator at $37.50.
- On any rate limit error: STOP. Wait 5 minutes. Try once more.

## 6. WHAT TO DO WHEN UNSURE
Stop and ask via Telegram. Never guess on important decisions.

## 7. OPERATOR INFO [CUSTOMIZE THIS SECTION]
Name: [YOUR NAME]
Website: [YOUR WEBSITE URL]
Site topic: [WHAT YOUR SITE IS ABOUT]
Audience: [WHO READS YOUR SITE]
Timezone: [YOUR TIMEZONE]
Communication preference: Concise Telegram messages, plain English.
```

Save with Ctrl+X, Y, Enter. Then restart OpenClaw:

```bash
pm2 restart openclaw
```

---

*Published by Fink Security | estherops.tech*
