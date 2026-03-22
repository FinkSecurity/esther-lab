---
title: "money.x.com Initial Reconnaissance"
date: 2026-03-17T14:09:00Z
type: findings
---

# money.x.com — Initial Reconnaissance

## Summary

money.x.com is an AEM-backed financial services platform operated by X Payments LLC (NMLS ID 2404946). The site exposes multiple unauthenticated form endpoints and reveals a custom AEM component (`pf01-money-transaction-id`) designed to handle transaction identifiers. Infrastructure analysis reveals Salesforce CMS backend integration, Cloudflare CDN, and Arkose Labs bot protection. A critical finding: unauthenticated forms accept transaction ID parameters via URL querystrings with prepopulation locks, potentially enabling social engineering or parameter injection attacks.

## Technical Details

**Target:** https://money.x.com  
**Redirects:** money-support.x.com (via Cloudflare)  
**CMS Platform:** Adobe Experience Manager (AEM)  
**Backend CMS:** Salesforce (Salesforce Form Plugin)  
**CDN/Protection:** Cloudflare + Arkose Labs (bot protection)  

**Organization:**
- X Payments LLC (registered Money Services Business)
- NMLS ID: 2404946
- Headquarters: 1450 Page Mill Rd., Palo Alto, CA 94304
- Banking Partner: Cross River Bank (FDIC insured)

**Arkose Labs Bot Protection:**
- Public Key: C07CAFBC-F76F-4DFD-ABFA-A6B78ADC1F29
- Present on public forms to prevent automated access

## Evidence

### AEM Endpoint Enumeration

**Unauthenticated Endpoints:**
```
/en/forms/x-money-legal-requests — Legal request form (no auth)
/en/fragments/generic-support-form — Generic support form (no auth)
```

**Authenticated Endpoints (role-gated):**
```
/en/forms/dispute-transaction 
  ├─ Required role: money_enrolled
  ├─ Component: pf01-money-transaction-id
  └─ Accepts: ?tx_id= parameter

/en/forms/feedback
  ├─ Required role: money_access
  └─ Accepts standard feedback submission
```

**Tested and Confirmed Locked (No Exposure):**
```
/crx/de → 404
/system/console → 404
/bin/querybuilder.json → 404
```

### Critical Finding: Transaction ID Prepopulation

**Endpoint:** `/en/fragments/generic-support-form`  
**Access Level:** Unauthenticated  
**Parameter:** `?tx_id=[value]`  
**Behavior:** 
- Form field accepts transaction ID via URL querystring
- Field has `prepopulateLock: true` attribute (user cannot edit)
- Value pre-fills the form but is read-only on display
- Form submits to Salesforce via 'htc' hook (integration)

**Implication:** An attacker can craft social engineering URLs:
```
https://money.x.com/en/fragments/generic-support-form?tx_id=attacker_crafted_value
```
Users clicking such links will see a pre-populated form, potentially lending false legitimacy to phishing attempts.

### Response Headers

**Notable Header - X-Transaction-ID:**
```
x-transaction-id: 90c657c7da3fffb0
```
Format appears to be internal X transaction tracking (hex string, ~64-bit). Suggests all platform transactions are tracked with this identifier format.

### AEM Component Registry

**Identified Component:** `pf01-money-transaction-id`  
- Naming Convention: Payment Flow v01, Money Transaction ID Handler
- Purpose: Form component for entering or selecting transaction identifiers
- Access Restriction: Requires `money_enrolled` role (authenticated X Money users only)
- Location: Dispute transaction form (implying authorized users can dispute their own transactions)

## Assessment

**Overall Risk: Medium-High**

**Individual Finding Breakdown:**

### 1. Transaction ID Parameter Injection (Low Risk)

**Finding:** Unauthenticated forms accept arbitrary transaction ID values via querystring  
**Severity:** Low to Medium  
**Exploitability:** Social Engineering (phishing)  
**Mitigation Posture:** Arkose Labs bot protection reduces automated exploit attempts  

**Why It Matters:**
- Attackers can create legitimate-looking links with arbitrary tx_id values
- Drives users to X Money support forms with pre-filled "transaction" context
- Could be used as initial pretext for social engineering campaigns
- No indication that backend validates tx_id ownership on form submission

### 2. Salesforce Integration Exposure (Low Risk)

**Finding:** Forms integrate directly with Salesforce CMS backend  
**Severity:** Low  
**Current Posture:** No exposed Salesforce endpoints discovered  
**Risk Factor:** Misconfigured Salesforce plugins can leak case data or accept unvalidated input

### 3. Arkose Labs Protection Effectiveness (Defensive Posture)

**Positive:** Arkose Labs is deployed and public key is visible, suggesting active bot prevention  
**Consider:** Public keys are by design non-sensitive, but their presence confirms rate-limiting is active

### 4. Role-Gated Access (Properly Implemented)

**Finding:** Dispute transaction form requires `money_enrolled` role  
**Assessment:** AEM role enforcement appears correct on authenticated endpoints  
**Note:** Cannot assess IDOR vulnerability on dispute form without authenticated test account

## Recommended Next Steps

### Phase 1: Social Engineering Campaign Simulation (Safe)
1. Document pre-population vulnerability proof-of-concept
2. Test with benign tx_id values to confirm parameter is accepted and prepopulated
3. Screenshot flow for documentation

### Phase 2: IDOR Testing (Requires Authorization)
1. **Obtain X Money account** or coordinate with authorized tester
2. Authenticate, obtain valid transaction ID from dispute history
3. Attempt to access dispute form with different user's transaction ID
4. Test query parameter tampering: `?tx_id=1`, `?tx_id=999999`, `?tx_id=[valid_but_unauthorized]`
5. Verify backend validates tx_id ownership on form submission

### Phase 3: AEM Configuration Audit (Passive)
1. Monitor for common AEM exposed endpoints via future scans
2. Check for any unauthenticated `/libs/` path exposure
3. Test dispatcher caching rules for information leakage

### Phase 4: Salesforce Integration Review
1. Map Salesforce Form Plugin configuration if accessible
2. Test for common Salesforce integration weaknesses (CSRF, field injection)
3. Verify submitted data does not reflect back unescaped in confirmations

### Phase 5: Supporting Reconnaissance (Ongoing)
1. Wayback Machine review of money.x.com for historical API patterns
2. DNS subdomain enumeration (api.money.x.com, admin.money.x.com, etc.)
3. Monitor for hardcoded tokens or credentials in archived versions
