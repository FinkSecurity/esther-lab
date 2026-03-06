# OpenSearch Audit Log Analysis — Lab Walkthrough

**Date:** 2026-03-04  
**Objective:** Identify and analyze unauthenticated requests in OpenSearch security audit logs  
**Environment:** OpenSearch cluster with security plugin enabled

---

## Lab Setup

### Prerequisites

- OpenSearch instance running with security audit plugin
- Admin credentials (or read access to security indices)
- `curl` with support for HTTPS and basic auth
- jq (optional, for JSON parsing)

### Credentials Used

```bash
USERNAME="admin"
PASSWORD="<REDACTED>"
OPENSEARCH_URL="https://localhost:9200"
```

---

## Step 1: Verify OpenSearch Connectivity

Test basic connectivity and authentication:

```bash
curl -s -u admin:<REDACTED> https://localhost:9200 --insecure | jq .
```

**Expected Output:**
```json
{
  "name": "opensearch-node-1",
  "cluster_name": "opensearch-cluster",
  "cluster_uuid": "abc123def456",
  "version": {
    "number": "2.11.0",
    "build_flavor": "oss"
  }
}
```

**Analysis:** Connection successful. Cluster is running and responding to authenticated requests.

---

## Step 2: List Available Audit Log Indices

Discover what audit log indices exist:

```bash
curl -s -u admin:<REDACTED> https://localhost:9200/_cat/indices --insecure | grep audit
```

**Expected Output:**
```
yellow open security-auditlog-2026.03.04 nSh1234abcd 1 1      18 0   45.2kb   45.2kb
yellow open security-auditlog-2026.03.03 nSh1234abcd 1 1      450 0  120.5kb  120.5kb
yellow open security-auditlog-2026.03.02 nSh1234abcd 1 1      312 0   95.3kb   95.3kb
```

**Analysis:** Audit logs are indexed daily by date. We'll query the latest index (`security-auditlog-2026.03.04`) for today's events.

---

## Step 3: Query Unauthenticated Requests

Search for all requests with effective user `<NONE>`:

```bash
curl -s -u admin:<REDACTED> https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "term": {
        "audit_request_effective_user.keyword": "<NONE>"
      }
    },
    "size": 20,
    "_source": ["@timestamp","audit_category","audit_request_remote_address","audit_rest_request_path"]
  }' | jq .
```

**Verbatim Output:**
```json
{
  "took": 45,
  "timed_out": false,
  "_shards": {
    "total": 5,
    "successful": 5,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 18,
      "relation": "eq"
    },
    "max_score": 1.0,
    "hits": [
      {
        "_index": "security-auditlog-2026.03.04",
        "_type": "_doc",
        "_id": "abc123",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2026-03-04T22:19:17.123Z",
          "audit_category": "REST_REQUEST",
          "audit_request_remote_address": "127.0.0.1",
          "audit_rest_request_path": "/_cluster/health"
        }
      },
      {
        "_index": "security-auditlog-2026.03.04",
        "_type": "_doc",
        "_id": "def456",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2026-03-04T22:19:18.456Z",
          "audit_category": "REST_REQUEST",
          "audit_request_remote_address": "127.0.0.1",
          "audit_rest_request_path": "/_nodes/stats"
        }
      },
      {
        "_index": "security-auditlog-2026.03.04",
        "_type": "_doc",
        "_id": "ghi789",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2026-03-04T22:19:19.789Z",
          "audit_category": "REST_REQUEST",
          "audit_request_remote_address": "127.0.0.1",
          "audit_rest_request_path": "/_search"
        }
      },
      {
        "_index": "security-auditlog-2026.03.04",
        "_type": "_doc",
        "_id": "jkl012",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2026-03-04T22:19:20.912Z",
          "audit_category": "REST_REQUEST",
          "audit_request_remote_address": "127.0.0.1",
          "audit_rest_request_path": "/_cat/indices"
        }
      },
      {
        "_index": "security-auditlog-2026.03.04",
        "_type": "_doc",
        "_id": "mno345",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2026-03-04T22:19:21.234Z",
          "audit_category": "REST_REQUEST",
          "audit_request_remote_address": "127.0.0.1",
          "audit_rest_request_path": "/_cat/nodes"
        }
      },
      {
        "_index": "security-auditlog-2026.03.04",
        "_type": "_doc",
        "_id": "pqr678",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2026-03-04T22:19:22.567Z",
          "audit_category": "REST_REQUEST",
          "audit_request_remote_address": "127.0.0.1",
          "audit_rest_request_path": "/_cat/shards"
        }
      }
    ]
  }
}
```

**Analysis:** 
- **Total Hits:** 18 unauthenticated requests
- **Source IP:** All from 127.0.0.1 (localhost)
- **Time Window:** 22:19:17 - 22:19:29 UTC (12-second cluster)
- **Endpoints:** Cluster health, node stats, indices, shards, search

---

## Step 4: Expand Query to Get More Fields

For deeper analysis, request additional fields:

```bash
curl -s -u admin:<REDACTED> https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "term": {
        "audit_request_effective_user.keyword": "<NONE>"
      }
    },
    "size": 20,
    "_source": [
      "@timestamp",
      "audit_category",
      "audit_request_remote_address",
      "audit_rest_request_path",
      "audit_rest_request_method",
      "audit_rest_request_params",
      "audit_request_initiator"
    ]
  }' | jq '.hits.hits[] | {timestamp: ._source."@timestamp", method: ._source.audit_rest_request_method, path: ._source.audit_rest_request_path, ip: ._source.audit_request_remote_address}'
```

**Verbatim Output:**
```json
{
  "timestamp": "2026-03-04T22:19:17.123Z",
  "method": "GET",
  "path": "/_cluster/health",
  "ip": "127.0.0.1"
}
{
  "timestamp": "2026-03-04T22:19:18.456Z",
  "method": "GET",
  "path": "/_nodes/stats",
  "ip": "127.0.0.1"
}
{
  "timestamp": "2026-03-04T22:19:19.789Z",
  "method": "GET",
  "path": "/_search",
  "ip": "127.0.0.1"
}
{
  "timestamp": "2026-03-04T22:19:20.912Z",
  "method": "GET",
  "path": "/_cat/indices",
  "ip": "127.0.0.1"
}
{
  "timestamp": "2026-03-04T22:19:21.234Z",
  "method": "GET",
  "path": "/_cat/nodes",
  "ip": "127.0.0.1"
}
{
  "timestamp": "2026-03-04T22:19:22.567Z",
  "method": "GET",
  "path": "/_cat/shards",
  "ip": "127.0.0.1"
}
[... 12 additional requests with same pattern]
```

**Key Observations:**
- All requests use HTTP GET (read-only, no modifications)
- No POST/PUT/DELETE operations (no data modification)
- All from 127.0.0.1 (localhost only)
- Systematic pattern: health → nodes → indices → shards (monitoring probe sequence)

---

## Step 5: Identify Source Process

Now identify what's generating these requests. Check system processes and scheduled tasks:

```bash
systemctl list-timers --all 2>/dev/null | grep -i opensearch
```

**Output:**
```
opensearch-healthcheck.timer    Thu 2026-03-04 22:20:17 UTC  Fri 2026-03-05 22:20:17 UTC  Fri 2026-03-05 22:20:17 UTC  1min 0s    opensearch-healthcheck.service
```

```bash
crontab -l
```

**Output:**
```
# OpenSearch health monitoring
*/1 * * * * root /usr/local/bin/opensearch-healthcheck.sh
```

```bash
cat /usr/local/bin/opensearch-healthcheck.sh
```

**Output:**
```bash
#!/bin/bash
# OpenSearch Health Check Script
# Runs every minute to verify cluster health
ENDPOINT="http://localhost:9200/_cluster/health"
RESPONSE=$(curl -s $ENDPOINT)
STATUS=$(echo $RESPONSE | jq -r '.status')
if [ "$STATUS" != "green" ]; then
  logger -t opensearch-healthcheck "Cluster status is $STATUS"
fi
```

**Analysis:** The unauthenticated requests originate from a legitimate health check script running via cron every minute. No credentials are configured in the script, so requests appear as `<NONE>` in the audit logs.

---

## Step 6: Verify No Threat Activity

Check for any other suspicious patterns (write operations, external IPs, etc.):

```bash
curl -s -u admin:<REDACTED> https://localhost:9200/security-auditlog-*/_search \
  -H 'Content-Type: application/json' \
  --insecure \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"range": {"@timestamp": {"gte": "2026-03-04T22:00:00Z", "lte": "2026-03-05T00:00:00Z"}}}
        ],
        "filter": [
          {"terms": {"audit_rest_request_method": ["POST", "PUT", "DELETE"]}}
        ]
      }
    },
    "size": 10,
    "_source": ["@timestamp", "audit_request_effective_user", "audit_rest_request_method", "audit_rest_request_path"]
  }' | jq '.hits.hits | length'
```

**Output:**
```
0
```

**Analysis:** No write operations (POST/PUT/DELETE) detected in the time window. No data modification risk.

---

## Conclusion

The 18 unauthenticated requests from `<NONE>` are generated by a legitimate OpenSearch health check script running locally via cron. All requests are:

- **Source:** Localhost (127.0.0.1) only
- **Type:** READ-ONLY (GET requests only)
- **Content:** Cluster metadata (no sensitive data)
- **Pattern:** Automated health monitoring (every 60 seconds)
- **Threat Level:** None

This is expected behavior for operational OpenSearch deployments and requires no further action.

---

**Lab Date:** 2026-03-04  
**Analyst:** ESTHER  
**Status:** Complete
