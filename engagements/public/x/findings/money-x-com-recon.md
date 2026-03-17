# money.x.com Reconnaissance Findings
Date: 2026-03-17

## Infrastructure
- money.x.com → redirects to money-support.x.com (Cloudflare)
- Platform: Adobe Experience Manager (AEM) confirmed
- Backend: Salesforce (field names: Source_Form__c, Screen_Name__c, Case_Site)
- Bot protection: Arkose Labs (publicKey: C07CAFBC-F76F-4DFD-ABFA-A6B78ADC1F29)
- X Payments LLC — registered MSB, NMLS ID 2404946
- Banking partner: Cross River Bank (FDIC)
- Address: 1450 Page Mill Rd., Palo Alto, CA 94304

## AEM Paths Confirmed
- /en/forms/dispute-transaction (auth: loggedin + money_enrolled)
- /en/forms/feedback (auth: loggedin + money_access)
- /en/forms/x-money-legal-requests (auth: none)
- /en/fragments/generic-support-form (auth: none)

## AEM Admin — Confirmed Locked
- /crx/de → 404
- /system/console → 404
- /bin/querybuilder.json → 404

## Notable Finding — tx_id URL Parameter
- generic-support-form accepts ?tx_id= via URL query parameter
- Field has prepopulateLock: true (injected, not user-typed)
- Form is unauthenticated
- Submits to Salesforce via 'htc' hook
- Potential social engineering vector (Low-Medium)
- Requires X Money account to test IDOR on authenticated dispute form

## Custom Component
- pf01-money-transaction-id registered in AEM component registry
- Renders on dispute-transaction form (requires money_enrolled role)
- Cannot test without authenticated X Money account

## Next Steps (requires X Money account)
- Test IDOR on /en/forms/dispute-transaction with arbitrary tx_id values
- Test if dispute form validates tx_id ownership server-side
- Check if money_enrolled role can be bypassed

## Response Headers of Interest
- x-transaction-id: 90c657c7da3fffb0 (X internal transaction tracking format)
