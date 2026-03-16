# Playtika — Standing Task Brief
<!-- ESTHER reads this when returning to Playtika after completing other work -->
<!-- Last updated: 2026-03-17 -->
<!-- Commit to: ~/esther-lab/engagements/public/playtika/TASK-BRIEF.md -->

---

## CONTEXT

Playtika's gaming infrastructure is heavily WAF-protected (Akamai).
Direct nuclei scans against CDN-fronted surfaces returned zero findings.
This is expected — pivot strategy below.

Key prior finding: `cdn-pl-dev.wooga.com` and `cdn-pl-staging.wooga.com` exist
but are IP-whitelisted. Staging infrastructure is the highest-value target.

Read `~/esther-lab/docs/RECON-PLAYBOOK.md` section
"WHEN NUCLEI FINDS NOTHING — WHAT TO DO NEXT" before proceeding.

---

## REMAINING DOMAINS (Phase 1 not yet started)

Run full Phase 1 passive recon on each — theHarvester + amass + crt.sh:

| Domain | Phase 1 | Phase 2 | Notes |
|--------|---------|---------|-------|
| seriously.com | ✅ harvester only | ✅ nuclei (0 findings) | needs crt.sh |
| serious.li | ⏳ | — | start here |
| redecor.com | ⏳ | — | |
| playwsop.com | ⏳ | — | poker platform |
| playticorp.com | ⏳ | — | corporate surface |
| monopoly-poker.com | ⏳ | — | Tier 3 |

---

## PRIORITY TASKS (in order)

### Task 1 — Certificate transparency on all domains
```bash
for domain in serious.li redecor.com playwsop.com playticorp.com monopoly-poker.com seriously.com wooga.com; do
  echo "=== $domain ==="
  curl -s "https://crt.sh/?q=%25.${domain}&output=json" \
    | jq -r '.[].name_value' 2>/dev/null \
    | sed 's/\*\.//g' \
    | sort -u \
    > ~/esther-lab/engagements/public/playtika/findings/crtsh-${domain}.txt
  echo "$(wc -l < ~/esther-lab/engagements/public/playtika/findings/crtsh-${domain}.txt) certs found"
  # Look for internal/staging subdomains immediately
  grep -iE 'staging|dev|internal|admin|corp|vpn|jenkins|jira|beta' \
    ~/esther-lab/engagements/public/playtika/findings/crtsh-${domain}.txt
  sleep 2  # be polite to crt.sh
done
```

### Task 2 — Shodan recon on Playtika IP ranges
```bash
# Find infrastructure not behind Akamai CDN
shodan search "org:Playtika" --fields ip_str,port,hostnames,product 2>/dev/null \
  | tee ~/esther-lab/engagements/public/playtika/findings/shodan-playtika-orgs.txt

shodan search "ssl:playtika.com" --fields ip_str,port,hostnames 2>/dev/null \
  | tee ~/esther-lab/engagements/public/playtika/findings/shodan-playtika-ssl.txt

# If SHODAN_API_KEY not set — check with: echo $SHODAN_API_KEY
# If missing — note it and skip, do not fabricate results
```

### Task 3 — Deep wooga.com staging investigation
```bash
# cdn-pl-dev.wooga.com and cdn-pl-staging.wooga.com are known to exist
# but are IP-whitelisted. Find what other staging infrastructure exists.

curl -s "https://crt.sh/?q=%25.wooga.com&output=json" \
  | jq -r '.[].name_value' | sort -u \
  | grep -iE 'staging|dev|internal|cdn|pl-' \
  > /tmp/wooga-staging-candidates.txt

cat /tmp/wooga-staging-candidates.txt

# For each candidate — check if it resolves and what IP it points to
# (different IP from Akamai = potential origin exposure)
for sub in $(cat /tmp/wooga-staging-candidates.txt); do
  ip=$(dig +short $sub 2>/dev/null | head -1)
  echo "$sub -> $ip"
done
```

### Task 4 — Phase 1 on remaining domains
```bash
# Run theHarvester on each remaining domain
for domain in serious.li redecor.com playwsop.com playticorp.com monopoly-poker.com; do
  echo "=== Phase 1: $domain ==="
  theHarvester -d $domain -b all -l 300 \
    -f ~/esther-lab/engagements/public/playtika/findings/harvester-${domain}
  sleep 5
done
```

### Task 5 — Consolidate all subdomains and re-probe
After Tasks 1-4, merge all new subdomains into a fresh httpx probe:
```bash
# Merge crt.sh + harvester findings
cat ~/esther-lab/engagements/public/playtika/findings/crtsh-*.txt \
    ~/esther-lab/engagements/public/playtika/findings/harvester-*.txt \
  | grep -oP '[a-zA-Z0-9._-]+\.(playtika|wooga|slotomania|caesarsgames|boardkingsgame|houseoffun|bingoblitz|seriously|serious|redecor|playwsop|playticorp|monopoly-poker)\.com' \
  | sort -u \
  | grep -v -P '^\d+[\-\.]' \
  | grep -P '^[a-zA-Z][a-zA-Z0-9\-]*\.' \
  > /tmp/playtika-all-subs-v2.txt

wc -l /tmp/playtika-all-subs-v2.txt

# Re-probe with httpx
httpx -l /tmp/playtika-all-subs-v2.txt \
  -status-code -title -tech-detect -follow-redirects \
  -rate-limit 10 -timeout 10 \
  -o ~/esther-lab/engagements/public/playtika/findings/httpx-live-hosts-v2.txt

# Flag anything NOT behind Akamai (different server header = origin exposed)
grep -v -i akamai ~/esther-lab/engagements/public/playtika/findings/httpx-live-hosts-v2.txt \
  | grep -v -i "503" \
  | head -30
```

---

## COMMIT PROTOCOL

After each task:
```bash
cd ~/esther-lab
git add engagements/public/playtika/findings/
git commit -m "Playtika recon: <describe what was done and key finding>"
git push
# VERIFY:
gh api repos/FinkSecurity/esther-lab/commits?path=engagements/public/playtika/findings\&per_page=1 \
  --jq '.[0] | {sha: .sha[:9], message: .commit.message}'
```

---

## WHAT TO REPORT BACK

After completing Tasks 1-3, report:
1. Any staging/dev subdomains found via crt.sh that aren't Akamai-fronted
2. Any Shodan results showing Playtika IPs with open ports not behind WAF
3. Any wooga.com staging IPs that differ from known Akamai ranges
4. Verified commit SHAs for all findings

These are the pivots most likely to find real vulnerabilities.
Use OpenRouter (claude-haiku) if you need help interpreting any findings.

---

*Fink Security / esther-lab · Playtika engagement · Updated 2026-03-17*
