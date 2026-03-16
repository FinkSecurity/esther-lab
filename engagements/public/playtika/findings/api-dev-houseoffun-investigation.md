# api-dev.houseoffun.com Investigation

## Summary
Service is real and production-grade, but currently unreachable through Akamai WAF/CDN. Origin appears to be intentionally blocking or offline.

## Findings

### HTTP Response Analysis
- **Status Code:** HTTP 503 (Service Unavailable)
- **CDN:** AkamaiGHost (Akamai Edge platform)
- **Server:** akamaiGHost
- **Cache-Control:** no-store (intentional CDN bypass for errors)

### Security Infrastructure Detected
**Content-Security-Policy reveals:**
- Hosted on `*.houseoffun.com` and `*.seriously.com`
- Integrations with payment processors: PayPal, Braintree
- Error tracking: Sentry (ingest.us.sentry.io)
- Parent company references: playtika.com, mail.playtika.com
- Image CDN: *.cloudfront.net

### Endpoint Testing Results
All tested API paths return HTTP 503:
- `/api` → 503
- `/v1` → 503
- `/health` → 503
- `/docs` → 503
- `/swagger` → 503
- `/graphql` → 503
- `/api/v1` → 503
- `/api/health` → 503

### Auth Header Testing
Custom headers produce no differentiation (all 503):
- `Authorization: Bearer [token]` → 503
- `X-API-Key: [value]` → 503
- `Cookie: session=[value]` → 503

## Interpretation
The 503 response is **not a vulnerability**, but an **operational state indicator**:

1. **Origin Server Down:** Backend service is offline (maintenance, deployment, or failure)
2. **Intentional Blocking:** Akamai configured to block origin or return error page
3. **Rate Limiting:** Possible aggressive rate-limiting triggering 503 response
4. **Geographic/IP Blocking:** May respond differently from other IPs or locations

## Recommendations for Further Investigation
- Monitor over time (if origin comes back online, capture response)
- Attempt from different geographic regions/IP ranges (if authorized)
- Check historical DNS/WHOIS for infrastructure patterns
- Cross-reference with other live hosts on news02.bingoblitz.com for comparison
- Nuclei scan will attempt deeper vulnerability checks despite 503

## No Vulnerabilities Identified
- No exposed credentials in headers
- No information disclosure in error pages
- Akamai is functioning as designed (blocking malformed requests)
- CSP is restrictive (good security posture)

---
*Investigation completed: 2026-03-16 17:48 UTC*
