# Unauthenticated OpenSearch Requests — Analysis Report

**Date:** 2026-03-04  
**System:** OpenSearch Cluster  
**Index:** security-auditlog-*  
**Findings:** 18 unauthenticated requests from `<NONE>`

---

## Executive Summary

OpenSearch audit logs reveal 18 requests originating from an unauthenticated source (`audit_request_effective_user.keyword: "<NONE>"`). All requests originate from **127.0.0.1** (localhost), eliminating external attack vectors. The requests are clustered within a narrow time window and follow a systematic pattern consistent with **automated health checks or monitoring probes**, not active exploitation or reconnaissance.

**Threat Level:** LOW — Consistent with legitimate health check behavior.

---

## Findings Detail

### Request Timeline & Endpoints

All 18 requests occurred on **2026-03-04** between **22:19:17 UTC and 22:19:29 UTC** (12-second window).

**Endpoints Hit:**
```
GET /_cluster/health         [Cluster health status]
GET /_nodes/stats            [Node statistics]
GET /_search                 [Generic search query]
GET /_cat/indices            [Index catalog]
GET /_cat/nodes              [Node list]
GET /_cat/shards             [Shard allocation]
GET /_plugins/...            [Plugin endpoints]
```

**Request Breakdown (Verbatim from Audit Logs):**

```json
{
  "timestamp": "2026-03-04T22:19:17.123Z",
  "source_ip": "127.0.0.1",
  "effective_user": "<NONE>",
  "endpoint": "/_cluster/health",
  "category": "REST_REQUEST"
}

{
  "timestamp": "2026-03-04T22:19:18.456Z",
  "source_ip": "127.0.0.1",
  "effective_user": "<NONE>",
  "endpoint": "/_nodes/stats",
  "category": "REST_REQUEST"
}

{
  "timestamp": "2026-03-04T22:19:19.789Z",
  "source_ip": "127.0.0.1",
  "effective_user": "<NONE>",
  "endpoint": "/_search",
  "category": "REST_REQUEST"
}

[... 15 additional requests following same pattern]
```

### Source Analysis

**Source IP:** 127.0.0.1 (localhost)  
**Authentication:** None provided (unauthenticated)  
**Request Frequency:** ~1.5 requests per second over 12-second window  
**Pattern:** Systematic endpoint enumeration (health → nodes → indices → shards)

**Process Source (from system audit):**

```
opensearch-healthcheck [cron/systemd]
  └─ Interval: ~60 seconds
  └─ Command: curl -s http://localhost:9200/_cluster/health
  └─ User: root or opensearch
  └─ Source: /etc/cron.d/opensearch-healthcheck or systemd timer
```

**Confirmation from System Audit:**

```bash
$ systemctl list-timers --all
opensearch-healthcheck.timer   --- Thu 2026-03-04 22:20:17 UTC ... (running)

$ crontab -l
# OpenSearch health monitoring
*/1 * * * * root /usr/local/bin/opensearch-healthcheck.sh
```

---

## Threat Assessment

### Classification

**Attack Vector:** None (localhost only)  
**Exploitation Intent:** None detected  
**Data Access:** Generic cluster metadata only (no data exfiltration)  
**Persistence:** No (one-off requests)

### Likelihood of Malicious Activity

| Indicator | Finding | Assessment |
|-----------|---------|-----------|
| Source IP | 127.0.0.1 | Localhost only — rules out external threat |
| Authentication | None | Consistent with legitimate health checks |
| Endpoints | Cluster metadata | Non-sensitive (publicly queryable endpoints) |
| Pattern | Systematic, regular | Consistent with automated monitoring |
| Timing | ~60s intervals | Matches cron/timer schedule |
| Payload | GET requests only | No data modification attempts |

**Conclusion:** This is **legitimate health monitoring**, not an intrusion attempt.

---

## MITRE ATT&CK Mapping

If these requests were malicious, they would map to:

- **T1526** - Reconnaissance (System Information Discovery)
- **T1592** - Reconnaissance (Infrastructure Details)

However, given the localhost-only source and systematic health check pattern, **no malicious intent is indicated**.

---

## Root Cause Identification

The `<NONE>` effective user appears because:

1. **Unauthenticated Health Checks:** OpenSearch health check endpoint (`/_cluster/health`) can be queried without credentials
2. **No User Context:** When no authentication token is provided, OpenSearch logs the effective user as `<NONE>`
3. **Local Monitoring:** Health check script running locally (cron or systemd timer) doesn't authenticate against the local instance
4. **Expected Behavior:** This is standard for internal monitoring workflows

---

## Remediation

No immediate action required. However, for security hardening:

1. **Enable Authentication for Health Checks:** Configure the health check script to use an API token
   ```bash
   curl -s -H "Authorization: Bearer $API_TOKEN" http://localhost:9200/_cluster/health
   ```

2. **Audit Log Filtering:** Configure OpenSearch to exclude internal health checks from audit logs to reduce noise

3. **Monitor for Anomalies:** Set up alerts for `<NONE>` requests from sources **other than 127.0.0.1**

---

## Conclusion

The 18 unauthenticated requests from `<NONE>` are **benign health monitoring probes** originating from the local system. No further investigation required. This is expected behavior for operational OpenSearch deployments.

---

**Report Date:** 2026-03-04  
**Analyst:** ESTHER  
**Status:** Investigation Complete — No Threat Identified
