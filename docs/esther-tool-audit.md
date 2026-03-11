# ESTHER Tool Audit & Install Plan

## ✅ Already on Kali Linux (no install needed)
| Tool | Category |
|------|----------|
| Nmap | Network Scanning |
| Metasploit Framework | Exploitation |
| sqlmap | Web App Testing |
| Nikto | Web App Testing |
| John the Ripper | Credential Attacks |
| Hashcat | Credential Attacks |
| Hydra | Credential Attacks |
| Aircrack-ng | Wireless |
| Responder | Credential/AD |
| SearchSploit | Exploitation |
| Netdiscover | Network Discovery |
| theHarvester | OSINT |
| Recon-ng | OSINT |
| Impacket | AD/Lateral Movement |
| Mimikatz (Windows) | Post-Exploitation |
| LinPEAS | Post-Exploitation |

## 📦 Needs Installing on VPS
```bash
# OSINT
pip install spiderfoot --break-system-packages
apt install amass -y
pip install shodan --break-system-packages  # CLI

# Network
apt install masscan -y
apt install rustscan -y  # or: cargo install rustscan

# Web App
apt install ffuf -y
# OWASP ZAP — daemon mode
apt install zaproxy -y

# Vuln Scanning
apt install nuclei -y       # or: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
apt install openvas -y      # Greenbone/OpenVAS (heavy — optional)
gem install wpscan          # WPScan

# Active Directory
apt install crackmapexec -y
pip install bloodhound --break-system-packages

# Post-Exploitation
# Empire — install via Docker (recommended)
docker pull bcsecurity/empire:latest

# Cloud
apt install awscli -y
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
curl -sL https://aka.ms/InstallAzureCLIDeb | bash
pip install ScoutSuite --break-system-packages     # multi-cloud auditing
pip install pacu --break-system-packages            # AWS exploitation

# Cloud/Secrets (OpenClaw skills)
pip install trufflehog --break-system-packages
pip install cloudenum --break-system-packages

# API Testing (OpenClaw skills)
# Kiterunner: https://github.com/assetnote/kiterunner
# Arjun:
pip install arjun --break-system-packages

# AD/Internal
pip install bloodhound --break-system-packages      # BloodHound.py

# Wireless
apt install kismet -y
apt install wifite -y
```

## 🔧 OpenClaw Skills to Add
| Skill | Notes |
|-------|-------|
| nuclei-scan | Template-driven vuln scanning |
| cloud-enum | AWS/GCP/Azure asset discovery |
| trufflehog | Secrets scanning in repos/filesystems |
| kiterunner | API route brute-forcing |
| arjun | HTTP parameter discovery |
| bloodhound | AD attack path mapping |
| crackmapexec | Lateral movement & cred validation |
| wpscan | WordPress vuln scanning |
| ffuf | Web fuzzing |

## 📋 Install Priority Order
1. **Today** — awscli, gcloud, az CLI + ScoutSuite (cloud recon)
2. **Session 2** — nuclei, ffuf, amass, rustscan (fast wins, high value)
3. **Session 3** — crackmapexec, bloodhound, impacket skills
4. **Session 4** — Empire, OpenVAS (heavier installs)
5. **When needed** — Wireless tools (Kismet, Wifite) — VPS has no WiFi adapter, only useful on physical hardware

## ⚠️ Notes
- **Wireless tools** (Aircrack-ng, Kismet, Wifite) require a physical wireless adapter — not useful on a VPS. Skip for now.
- **Mimikatz** is Windows-only — ESTHER can deploy it as a payload but can't run it natively on Kali.
- **OpenVAS/Greenbone** is resource-heavy — may strain the VPS. Test carefully.
- **Empire** — best run in Docker to avoid dependency conflicts.
- All offensive tools require documented client authorization before ESTHER uses them on external targets.
