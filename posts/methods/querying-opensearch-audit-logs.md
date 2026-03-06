# OpenSearch Audit Log Threat Hunting — Reusable Methodology

**Purpose:** Tactical reference guide for querying OpenSearch audit logs to identify anomalies, security events, and suspicious activity.

---

## Core Concept

OpenSearch audit logs record all REST API requests (authentication, data access, privilege changes). Systematic querying of these logs reveals:

- Unauthorized access attempts
- Unusual data access patterns
- Privilege escalation
- Service account abuse
- Automated scanning activity

---

## Index Structure & Naming

OpenSearch stores audit logs in daily indices:

```
security-auditlog-YYYY.MM.DD
```

**Examples:**
```
security-auditlog-2026.03.04  (today)
security-auditlog-2026.03.03  (yesterday)
security-auditlog-2026.03-*   (all March 2026)
security-auditlog-*           (all indices)
```

Use wildcard patterns to query multiple days at once.

---

## Key Audit Log Fields

| Field | Type | Example | Significance |
|-------|------|---------|--------------|
| `@timestamp` | DateTime | 2026-03-04T22:19:17.123Z | When the request occurred |
| `audit_request_effective_user.keyword` | String | "admin" or "<NONE>" | Who executed the request |
| `audit_request_remote_address` | IP | "192.168.1.100" | Source IP address |
| `audit_rest_request_path` | String | "/_search" | Endpoint accessed |
| `audit_rest_request_method` | String | "GET", "POST", "DELETE" | HTTP method used |
| `audit_rest_request_params` | String | "?pretty=true" | Query parameters |
| `audit_category` | String | "REST_REQUEST", "FAILED_LOGIN" | Type of event |
| `audit_request_initiator` | String | "rest", "transport" | Communication type |

---

## Common Threat Hunting Queries

### Query 1: Unauthenticated Access Attempts

Find all requests with no authenticated user:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "term": {
        "audit_request_effective_user.keyword": "<NONE>"
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_remote_address","audit_rest_request_path"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Health checks, monitoring probes
- Misconfigured services
- Potential scanner activity (if from external IPs)

**Red Flag:** Unauthenticated requests from IPs other than 127.0.0.1

---

### Query 2: Failed Authentication Attempts

Track login failures:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "term": {
        "audit_category.keyword": "FAILED_LOGIN"
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_remote_address","audit_request_effective_user"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Brute force attempts
- Credential misuse
- Account enumeration attacks

**Red Flag:** Multiple failed logins for same user from different IPs

---

### Query 3: Privilege Escalation & Role Changes

Find requests that modify user permissions:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"terms": {"audit_rest_request_method": ["POST", "PUT"]}}
        ],
        "filter": [
          {"wildcard": {"audit_rest_request_path": {"value": "*roles*"}}}
        ]
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_effective_user","audit_rest_request_path"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Role modifications
- Permission escalation
- User account changes

**Red Flag:** Privilege changes by non-admin accounts or outside change windows

---

### Query 4: Index Access & Data Queries

Track who accessed what data:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"term": {"audit_rest_request_method.keyword": "GET"}},
          {"wildcard": {"audit_rest_request_path": {"value": "/*/_search"}}}
        ]
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_effective_user","audit_rest_request_path"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Bulk data access
- Unauthorized index queries
- Service account misuse

**Red Flag:** Unexpected users accessing sensitive indices (health, logs, secrets)

---

### Query 5: Write Operations (Data Modification)

Detect changes to data:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "terms": {
        "audit_rest_request_method.keyword": ["POST", "PUT", "DELETE"]
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_effective_user","audit_rest_request_method","audit_rest_request_path"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Document modifications
- Index deletions
- Data corruption or sabotage

**Red Flag:** Bulk deletes, unexpected index modifications, deletions by service accounts

---

### Query 6: External IP Access

Find requests from non-localhost sources:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "bool": {
        "must_not": [
          {"term": {"audit_request_remote_address.keyword": "127.0.0.1"}}
        ]
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_remote_address","audit_request_effective_user","audit_rest_request_path"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Remote access patterns
- Potential external attackers
- Legitimate remote monitoring

**Red Flag:** External IPs with no corresponding legitimate access (VPN, monitoring service)

---

### Query 7: Bulk Operations & Large Transfers

Identify potential data exfiltration:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "wildcard": {
        "audit_rest_request_path.keyword": {"value": "*_bulk*"}
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_effective_user","audit_rest_request_params"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- Bulk imports/exports
- Potential data theft
- Unusual data movement

**Red Flag:** Bulk operations to unusual destinations, outside business hours, by service accounts

---

### Query 8: Time-Based Anomalies

Find activity outside normal business hours:

```bash
curl -s -u admin:PASSWORD https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "range": {
        "@timestamp": {
          "gte": "2026-03-04T22:00:00Z",
          "lte": "2026-03-05T06:00:00Z"
        }
      }
    },
    "size": 100,
    "_source": ["@timestamp","audit_request_effective_user","audit_rest_request_path"]
  }' | jq '.hits.hits'
```

**What This Reveals:**
- After-hours access
- Scheduled attacks
- Insider threats

**Red Flag:** High-privilege operations (role changes, deletions) outside business hours

---

## Analysis Workflow

### Step 1: Set Scope
Define time range, users, indices of interest.

```bash
# All events from last 24 hours
"range": {"@timestamp": {"gte": "now-24h"}}

# Specific time window
"range": {"@timestamp": {"gte": "2026-03-04T00:00:00Z", "lte": "2026-03-05T00:00:00Z"}}
```

### Step 2: Query for Baseline
Get normal activity patterns (baseline).

```bash
# What endpoints are typically accessed?
curl ... -d '{
  "aggs": {
    "endpoints": {
      "terms": {
        "field": "audit_rest_request_path.keyword",
        "size": 50
      }
    }
  }
}'
```

### Step 3: Filter Anomalies
Compare against baseline, identify deviations.

```bash
# Find requests to endpoints not in baseline
# (e.g., admin-only endpoints accessed by regular users)
```

### Step 4: Investigate & Alert
For each anomaly:
- Who? (audit_request_effective_user)
- When? (@timestamp)
- What? (audit_rest_request_path, audit_rest_request_params)
- Where? (audit_request_remote_address)
- Why? (context from business operations)

---

## Red Flag Indicators

| Indicator | Example Query | Severity |
|-----------|--------------|----------|
| **Repeated failed logins** | Same user, >5 failures in 5 min | HIGH |
| **External unauthenticated access** | `<NONE>` from non-127.0.0.1 IP | CRITICAL |
| **Privilege escalation** | Role change by non-admin | CRITICAL |
| **Bulk data export** | `_bulk` operation with large params | HIGH |
| **Deleted indices** | DELETE requests to production indices | CRITICAL |
| **After-hours admin activity** | Role changes between 22:00-06:00 | HIGH |
| **Service account abuse** | Service account accessing unusual indices | MEDIUM |
| **Port scanning** | Requests to non-existent endpoints | MEDIUM |

---

## Query Performance Tips

1. **Use field keywords:** Always query `.keyword` fields for exact matches (faster than full-text)
   ```json
   {"term": {"audit_request_effective_user.keyword": "admin"}}
   ```

2. **Limit result size:** Start small (10-20 results), expand if needed
   ```json
   "size": 20
   ```

3. **Filter before aggregation:** Reduce data before computing statistics
   ```json
   "query": {...},
   "aggs": {...}
   ```

4. **Use time ranges:** Always scope by @timestamp to reduce data scanned
   ```json
   "range": {"@timestamp": {"gte": "now-7d"}}
   ```

5. **Index patterns:** Query only relevant date ranges
   ```
   security-auditlog-2026.03.*  (March only)
   security-auditlog-2026.03.04  (specific day)
   ```

---

## Escalation Procedures

When you identify a threat:

1. **Verify:** Confirm the finding with additional queries
2. **Document:** Save full query + results
3. **Notify:** Alert the security team with specific timestamps and users
4. **Preserve:** Archive audit logs for investigation (don't delete)
5. **Remediate:** Isolate affected accounts, reset passwords, revoke tokens

---

## References

- [OpenSearch Security Plugin Docs](https://opensearch.org/docs/latest/security-plugin/index/)
- [Audit Log Configuration](https://opensearch.org/docs/latest/security-plugin/audit-logs/index/)
- [Query DSL Reference](https://opensearch.org/docs/latest/query-dsl/index/)

---

**Created:** 2026-03-04  
**Purpose:** Tactical threat hunting reference  
**Applicability:** Any OpenSearch deployment with security plugin enabled
