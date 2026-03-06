---
title: "GitHub for Complete Beginners: A Friendly Guide"
date: 2026-03-05
draft: false
tags: [git, github, tutorial, beginner]
---

# GitHub for Complete Beginners: A Friendly Guide

Welcome! You've probably heard the word "GitHub" thrown around, maybe you need to use it for work or a project, and you have no idea where to start. That's completely normal. We'll walk through this together, step by step, without any confusing jargon.

By the end of this guide, you'll understand what GitHub is, how to create an account, and how to push your first project online.

---

## What Is Git and GitHub? (They're Not the Same Thing!)

Here's the confusion most people have: **Git** and **GitHub** are different things.

**Git** is a tool that runs on your computer. It's like a "save system" for your code. You know how video games let you save your progress at checkpoints? Git does that for code. Every time you make changes, you can save a version. If you mess something up, you can go back to an earlier version. You can also see exactly what changed between saves.

**GitHub** is a website where you can store your Git projects online. It's like cloud storage, but specifically built for code. You upload your projects to GitHub so:
- Your code is backed up on the internet
- Other people can see your work
- You can collaborate with teammates
- Your projects stay safe even if your computer breaks

Think of it like this: **Git is the camera, GitHub is Instagram**. Git captures your work. GitHub shares it with the world.

### Why Does This Matter?

Version control (the fancy name for what Git does) saves you from disaster. Ever written something, deleted it by accident, and couldn't get it back? With Git, you never lose work. Ever had code that worked yesterday but broke today? You can see exactly what changed and revert it. Working with others? Git helps you merge everyone's changes without losing anything.

---

## Creating Your First GitHub Account

Let's get you set up on GitHub.

### Step 1: Go to GitHub.com

Open your browser and go to **https://github.com**. You'll see a sign-up form. It's right there on the homepage.

### Step 2: Choose Your Username

Pick a username. This is what people will see in your GitHub URL. Some ideas:
- Your name or initials
- A professional-sounding version of a nickname
- Something short and memorable

**Important:** You can change this later, so don't stress too much about it.

### Step 3: Enter Your Email

Use an email you check regularly. GitHub will send you a verification link.

### Step 4: Create a Password

Make it strong (mix of letters, numbers, symbols). Use a password manager if you have one.

### Step 5: Verify Your Email

GitHub will send you an email. Click the link to verify. This proves you own the email address.

That's it! You're now a GitHub user. Congratulations! 🎉

---

## Your First Repository

A **repository** (or "repo") is just a folder where your project lives. Think of it as a project container. It holds all your code, documentation, and history.

### Creating a New Repo on GitHub

1. Log into GitHub
2. Click the **+** icon in the top-right corner
3. Click **New repository**
4. Fill in the details:

**Repository name:** Something descriptive (e.g., `my-first-website`, `recipe-app`, `notes`)

**Description:** Optional, but helpful. One line explaining what this project is.

**Public vs Private:**
- **Public:** Anyone on the internet can see your code. Great for learning, sharing, and showcasing your work.
- **Private:** Only you (and people you invite) can see it. Better for personal projects or work.

For your first repo, pick **Public** so you can share it with friends.

**Initialize with a README:** Check this box. A README is a file that explains your project. It's the first thing people see.

5. Click **Create repository**

Congratulations! Your first repo exists. 🎉

### What Does Your README Look Like?

GitHub automatically creates a file called `README.md`. It looks like this:

```markdown
# My First Website

This is a project where I'm learning web development.

## How to use it

Just open index.html in your browser.

## Credits

I learned from YouTube tutorials and my friend Alex.
```

That's it. Don't overthink it. A README is just a friendly introduction to your project.

---

## The Three Commands You'll Use Every Day

Here's where Git comes in. You've created a repo on GitHub, but now you need to add your code. This is where the magic happens.

### First: Install Git

Download Git from **https://git-scm.com**. Follow the installer. It takes 2 minutes. Done!

### Second: Clone the Repo to Your Computer

"Clone" means download your GitHub repo to your computer so you can work on it.

Go to your GitHub repo and click the green **Code** button. Copy the URL it shows you (it looks like `https://github.com/yourname/repo-name.git`).

Open your terminal/command prompt on your computer and run:

```bash
git clone https://github.com/yourname/repo-name.git
cd repo-name
```

You now have a folder on your computer with your project. Inside it, Git is watching. Ready to track changes.

### Third: The Three Daily Commands

Now you make changes. You add a file, edit code, whatever. Then you use these three commands:

#### Command 1: `git add`

This tells Git: "Hey, I've made changes. Get ready to save them."

```bash
git add .
```

The `.` means "add everything I changed." You could also add specific files:

```bash
git add index.html
git add styles/main.css
```

**In plain English:** You've finished editing a few files. You're telling Git "I'm done with these changes, prepare to save them."

#### Command 2: `git commit -m "message"`

This saves your changes with a label.

```bash
git commit -m "Add navigation menu to homepage"
```

The message in quotes should describe what you did. Be specific. "Fix bug" is vague. "Fix bug where login button didn't submit form" is clear.

**In plain English:** You're saving a checkpoint. Like in a video game, you're saying "Remember this moment, here's what I did."

#### Command 3: `git push`

This sends your changes to GitHub (the internet).

```bash
git push
```

Once you push, your changes are on GitHub. Anyone who clones your repo will see your latest work.

**In plain English:** You're uploading your checkpoint to GitHub so it's backed up and others can see it.

### Putting It All Together

Here's a real example. You edited two files and want to save them to GitHub:

```bash
# Tell Git to prepare your changes
git add .

# Save with a description
git commit -m "Update homepage styling and fix typo in header"

# Upload to GitHub
git push
```

Done. Your changes are now on GitHub. You can see them at your repo URL.

---

## Cloning a Repo (Getting Someone Else's Code)

What if you want to work on someone else's project? Or use their code as a starting point?

You **clone** it. This downloads a full copy to your computer, including all the history.

### How to Clone

1. Go to a GitHub repo (any repo)
2. Click the green **Code** button
3. Copy the URL
4. In your terminal, run:

```bash
git clone https://github.com/someone/their-project.git
cd their-project
```

Now you have the entire project on your computer. You can edit it, run it, modify it.

### When You'd Clone

- You want to contribute to an open-source project
- A friend shared their code and you want to run it locally
- You're using someone's template to start your own project

---

## GitHub Pages: Publish a Website for Free

GitHub offers something cool: free website hosting. If you have an HTML project, GitHub can publish it automatically.

### Enabling Pages

1. Go to your repo settings (click **Settings** tab)
2. Scroll down to **Pages** (on the left sidebar)
3. Under **Source**, select the branch where your code is (usually **main**)
4. Click **Save**

That's it. GitHub will publish your site at:

```
https://username.github.io/repo-name
```

So if your username is `alice` and repo is `portfolio`, your site is at:

```
https://alice.github.io/portfolio
```

### How It Works

Every time you push to GitHub, if your repo has `index.html`, GitHub automatically publishes it. So your website updates automatically with every push.

---

## Adding a Custom Domain

Your GitHub Pages site works at `username.github.io/repo-name`, but what if you want your own domain like `alice.com`?

### Step 1: Buy a Domain

You need a domain name. We use **Porkbun** (porkbun.com). Register your domain there (it costs about $10/year).

### Step 2: Add the Domain to GitHub

1. Go to your repo **Settings**
2. Find **Pages** again
3. Under **Custom domain**, type your domain (e.g., `alice.com`)
4. Click **Save**

GitHub will create a file called `CNAME` in your repo. Don't delete it.

### Step 3: Point Your Domain to GitHub

This is the technical part. You need to tell your domain provider (Porkbun) where to send traffic.

In Porkbun:

1. Find your domain in your dashboard
2. Click **Manage**
3. Find **DNS Records** or **Advanced DNS**
4. Add a **CNAME record**:
   - **Name:** `www`
   - **Type:** CNAME
   - **Value:** `username.github.io`

So if your username is `alice`, you'd put `alice.github.io`.

### Step 4: Wait for DNS to Propagate

This is the annoying part: it can take a few minutes to a few hours for the change to take effect worldwide. DNS is like a phone book on the internet, and it takes time for updates to spread.

Once it works, visiting `alice.com` will show your GitHub Pages site.

### Troubleshooting

- **Domain isn't working after an hour?** Double-check your DNS record spelling
- **Getting a security warning?** Give it another hour. Sometimes certificates need time to update
- **Changed your domain?** Delete the old CNAME record in GitHub Pages, add the new one, update DNS

---

## GitHub Actions: Automatic Deployment

GitHub can automatically do things when you push code. This is called an **Action**. Think of it as "a robot that runs tasks for you automatically."

Common uses:
- Run tests when you push code
- Deploy your website when you update it
- Send you a notification when someone contributes

### A Simple Real Example

Let's say you have a website and you want it to automatically rebuild whenever you push changes.

You create a file in your repo at:

```
.github/workflows/deploy.yml
```

Inside it, you write:

```yaml
name: Deploy Website

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build site
        run: npm run build
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

This says:

- **When:** Every time you push to the `main` branch
- **What:** Run `npm run build` (or whatever builds your site) and deploy it

Now, whenever you push, the robot automatically rebuilds and deploys. No manual steps.

### In Plain English

You create a file that says "When I push code, automatically do these steps for me." It's like setting an alarm that triggers your deployment.

---

## Common Beginner Mistakes (And How to Fix Them)

### Mistake 1: Forgot to Push

You committed your changes locally but didn't push. You think they're on GitHub, but they're not.

**How to fix:** Just run `git push`. Your changes will upload.

**How to avoid:** Make it a habit: `add` → `commit` → `push`. Don't close your terminal until you've pushed.

### Mistake 2: Merge Conflicts

You and a teammate edited the same file, and now Git doesn't know which version to keep.

**What it looks like:**

```
<<<<<<< HEAD
My version of the code
=======
Their version of the code
>>>>>>> their-branch
```

**How to fix:** Edit the file. Keep what you want, delete what you don't. Then `add`, `commit`, and `push` again.

**How to avoid:** Communicate with teammates about who's editing what. Commit small changes frequently so conflicts are rare.

### Mistake 3: Committed a Password or API Key

Oh no! You pushed sensitive information to GitHub. Anyone can see it now.

**How to fix:**

1. **Immediately:** Rotate the password/key. Change it in your services.
2. **Clean up:** Use `git-filter-branch` or tools like BFG Repo-Cleaner to remove it from history
3. **Prevent:** Use `.gitignore` (see below)

**How to avoid:** Create a `.gitignore` file in your repo:

```
# .gitignore
.env
passwords.txt
secrets.yml
node_modules/
```

Anything listed here won't be added to Git. So if you have a `.env` file with API keys, it won't be pushed.

### Mistake 4: Pushed to the Wrong Branch

You pushed to `main` when you meant to push to a `dev` branch. Now your unfinished code is live.

**How to fix:** If you haven't gone live, revert the commit on `main`:

```bash
git revert HEAD
git push
```

This creates a new commit that undoes your last commit.

**How to avoid:** Check your current branch before pushing:

```bash
git branch
```

The one with a `*` is your current branch.

---

## Glossary: 15 Essential Terms

Here are the terms you'll hear when using GitHub. Bookmark this if you need to!

**Repository (Repo):** A folder where your project lives. Contains all your files and their history.

**Branch:** A separate copy of your code where you can make changes without affecting the main code. Like creating a "what if" scenario.

**Commit:** A saved checkpoint of your code. Each commit has a message describing what changed.

**Push:** Upload your commits to GitHub (the internet).

**Pull:** Download commits from GitHub to your computer. Opposite of push.

**Clone:** Download a full copy of a repo from GitHub to your computer. Used when you're accessing a repo for the first time.

**Fork:** Copy someone else's repo to your own GitHub account. Used when you want to modify their project.

**Merge:** Combine changes from one branch into another. "Merge my feature branch into main" means take my changes and put them in the main code.

**Pull Request (PR):** A proposal to change someone's code. You say "I made changes, please review and merge them." It's how collaboration happens on GitHub.

**Workflow:** A set of automated tasks (Action) that runs when something happens, like a push.

**Action:** An automated task that runs inside your repo. Can build, test, deploy, or do anything programmable.

**GitHub Pages:** Free website hosting provided by GitHub. Automatically deploys your HTML/CSS/JS.

**CNAME:** A DNS record that points one domain name to another. Used to attach a custom domain to GitHub Pages.

**SSH Key:** A security credential that proves it's you. Lets you push code without entering your password every time.

**PAT (Personal Access Token):** Another security credential. Like a password, but specific to GitHub. You create it instead of sharing your main password.

---

## You're Ready!

Seriously. You've read this guide, and you know more about GitHub than most people starting out. The best way to learn is by doing:

1. Create a repo
2. Add a file
3. Commit it
4. Push it
5. See it on GitHub

Repeat that a few times, and it becomes automatic.

Mistakes are normal. Deleting branches, pushing the wrong thing, committing sensitive files — everyone does this. GitHub makes it easy to fix. There's almost nothing you can do that's truly irreversible.

Welcome to the community. You've got this. 💪

---

## Next Steps

Once you're comfortable with the basics:

- Learn about **branches** for working on features separately
- Explore **pull requests** for collaborating with others
- Set up **SSH keys** so you don't have to enter passwords
- Check out **open-source projects** and contribute to one

---

**Written:** 2026-03-05  
**Last Updated:** 2026-03-05  
**For:** Complete beginners to Git and GitHub  
**Questions?** The GitHub Docs (docs.github.com) are excellent and beginner-friendly.
