# Fink Security — Client Engagement Template

This template covers all engagement types offered by Fink Security. Complete all sections before ESTHER begins any authorized testing.

---

## Engagement Details

| Field | Value |
|-------|-------|
| Client Name | |
| Client Contact | |
| Contact Email | |
| Contact Phone | |
| Engagement Type | |
| Start Date | |
| End Date | |
| Engagement ID | FS-YYYY-### |

---

## Engagement Type

Select all that apply:

- [ ] OSINT / Passive Reconnaissance
- [ ] External Network Penetration Test
- [ ] Web Application Penetration Test
- [ ] Internal Network Penetration Test
- [ ] Red Team Exercise
- [ ] Vulnerability Assessment
- [ ] Security Audit
- [ ] Threat Intelligence Gathering
- [ ] Social Engineering Assessment

---

## Scope — Authorized Targets

### In Scope

List all authorized targets explicitly. ESTHER will not act against any target not listed here.

```
Domain/IP/Range:
Domain/IP/Range:
Domain/IP/Range:
```

### Out of Scope

```
Domain/IP/Range:
Domain/IP/Range:
```

### Explicitly Prohibited

- [ ] Production database modification
- [ ] Data exfiltration beyond proof-of-concept
- [ ] Denial of service attacks
- [ ] Physical access attempts
- [ ] Social engineering of employees
- [ ] Third-party systems not owned by client

---

## Rules of Engagement

### Testing Hours
- [ ] 24/7 permitted
- [ ] Business hours only (specify): _______________
- [ ] Off-hours only (specify): _______________

### Notification Requirements
- [ ] Client notified before testing begins each day
- [ ] Client notified before each test phase
- [ ] No notification required

### Emergency Stop Contact
- Name: _______________
- Phone: _______________
- Email: _______________

### Escalation Threshold
ESTHER will pause and notify Adam via Telegram immediately if:
- [ ] Active intrusion detected from third party during engagement
- [ ] Critical vulnerability found that poses immediate risk
- [ ] System instability caused by testing
- [ ] Any finding that may have legal implications

---

## Authorization & Legal

### Statement of Authorization

> I/We, the undersigned, hereby authorize Fink Security and its autonomous agent ESTHER to perform security testing as defined in this document against the systems listed in the Scope section. This authorization is valid for the dates specified only.

**Client Authorized Signatory**
- Name: _______________
- Title: _______________
- Signature: _______________
- Date: _______________

**Fink Security**
- Authorized by: Adam Fink
- Date: _______________

---

## Deliverables

- [ ] Executive Summary Report
- [ ] Technical Findings Report
- [ ] CVSS-scored vulnerability list
- [ ] Remediation recommendations
- [ ] Retest after remediation
- [ ] Presentation to stakeholders

**Report delivery date:** _______________
**Report format:** [ ] PDF  [ ] Word  [ ] Online portal

---

## ESTHER Authorization Tier

Per ESTHER's three-tier authorization framework:

**Tier 1 — Pre-authorized (no approval needed):**
- Passive reconnaissance and OSINT
- DNS enumeration
- WHOIS lookups
- Public data gathering
- Port scanning (non-intrusive)

**Tier 2 — Engagement-authorized (this document):**
- Active vulnerability scanning
- Web application testing
- Exploitation of confirmed vulnerabilities
- Credential testing
- Network enumeration

**Tier 3 — Requires explicit Telegram approval:**
- Destructive actions
- Data exfiltration beyond PoC
- Persistence mechanisms
- Lateral movement in production
- Any action not covered above

---

## Notes

_______________________________________________
_______________________________________________
_______________________________________________

---

*Fink Security — Engagement ID: FS-YYYY-### | Confidential*
