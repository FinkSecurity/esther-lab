# OpenSearch Log Integration — OpenClaw & ESTHER

Guide for ingesting OpenClaw logs into OpenSearch and building dashboards for ESTHER's operational monitoring.

---

## Overview

OpenClaw writes daily JSON logs to `/tmp/openclaw/openclaw-YYYY-MM-DD.log`. Each line is a JSON object containing agent activity, API calls, errors, and Telegram channel events. This guide covers parsing and ingesting those logs into OpenSearch for search, visualization, and alerting.

---

## Log Format

OpenClaw logs are newline-delimited JSON. Each entry looks like:

```json
{
  "0": "message content",
  "_meta": {
    "runtime": "node",
    "hostname": "unknown",
    "name": "{\"subsystem\":\"agent/embedded\"}",
    "parentNames": ["openclaw"],
    "date": "2026-03-02T16:54:55.019Z",
    "logLevelId": 2,
    "logLevelName": "DEBUG",
    "path": {
      "fileName": "subsystem-DypCPrmP.js",
      "fileLine": "1170"
    }
  },
  "time": "2026-03-02T16:54:55.019Z"
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `_meta.logLevelName` | DEBUG, INFO, WARN, ERROR |
| `_meta.name` | Subsystem (agent/embedded, gateway/channels/telegram, diagnostic) |
| `_meta.date` | ISO timestamp |
| `0` | Primary message content |
| `time` | Log entry timestamp |

---

## Ingestion Methods

### Method 1 — Direct API Push (Recommended for Getting Started)

Push log entries directly to OpenSearch via the bulk API. ESTHER can run this as a scheduled task.

```bash
# Test OpenSearch connectivity
curl -k -u admin:PASSWORD https://localhost:9200/_cluster/health

# Create index for OpenClaw logs
curl -k -u admin:PASSWORD -X PUT https://localhost:9200/openclaw-logs \
  -H 'Content-Type: application/json' \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  }'

# Push a single log entry (test)
curl -k -u admin:PASSWORD -X POST https://localhost:9200/openclaw-logs/_doc \
  -H 'Content-Type: application/json' \
  -d '{"message": "test", "timestamp": "2026-03-02T00:00:00Z"}'
```

### Method 2 — Logstash Pipeline (Production)

Install Logstash in a container and configure a pipeline to parse and forward OpenClaw logs.

```yaml
# logstash pipeline config: openclaw.conf
input {
  file {
    path => "/tmp/openclaw/openclaw-*.log"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  json {
    source => "message"
  }
  
  # Extract subsystem from _meta.name
  mutate {
    add_field => {
      "subsystem" => "%{[_meta][name]}"
      "log_level" => "%{[_meta][logLevelName]}"
      "log_date" => "%{[_meta][date]}"
    }
  }
  
  # Parse timestamp
  date {
    match => ["log_date", "ISO8601"]
    target => "@timestamp"
  }
}

output {
  opensearch {
    hosts => ["https://localhost:9200"]
    user => "admin"
    password => "PASSWORD"
    ssl_certificate_verification => false
    index => "openclaw-logs-%{+YYYY.MM.dd}"
  }
}
```

---

## Index Template

Create an index template to ensure correct field mapping for all openclaw-logs indices:

```bash
curl -k -u admin:PASSWORD -X PUT https://localhost:9200/_index_template/openclaw-logs \
  -H 'Content-Type: application/json' \
  -d '{
    "index_patterns": ["openclaw-logs-*"],
    "template": {
      "mappings": {
        "properties": {
          "@timestamp": { "type": "date" },
          "log_level": { "type": "keyword" },
          "subsystem": { "type": "keyword" },
          "message": { "type": "text" },
          "session_id": { "type": "keyword" },
          "run_id": { "type": "keyword" },
          "model": { "type": "keyword" },
          "channel": { "type": "keyword" },
          "duration_ms": { "type": "long" }
        }
      }
    }
  }'
```

---

## Recommended Dashboards

Once logs are flowing, create these dashboards in OpenSearch Dashboards:

### 1. ESTHER Operations Overview
- Total agent runs per day (bar chart)
- Error rate over time (line chart)
- Model usage breakdown (pie chart)
- Average response time (metric)

### 2. Telegram Channel Monitor
- Messages received per hour
- Response latency distribution
- Failed message count

### 3. API Cost Tracker
- OpenRouter API calls per day
- Estimated token usage
- Cost trend over time

### 4. Error & Alert Dashboard
- ERROR and WARN log count (metric)
- Error messages table (most recent)
- 401/403 authentication failures

---

## Alerting Rules

Set up OpenSearch alerting monitors for these conditions:

### High Error Rate
```json
{
  "name": "ESTHER High Error Rate",
  "monitor_type": "query_level_monitor",
  "schedule": { "period": { "interval": 5, "unit": "MINUTES" } },
  "inputs": [{
    "search": {
      "indices": ["openclaw-logs-*"],
      "query": {
        "query": {
          "bool": {
            "filter": [
              { "term": { "log_level": "ERROR" } },
              { "range": { "@timestamp": { "gte": "now-5m" } } }
            ]
          }
        }
      }
    }
  }],
  "triggers": [{
    "condition": { "script": { "source": "ctx.results[0].hits.total.value > 10" } },
    "actions": [{ "name": "notify", "message": "ESTHER error rate elevated" }]
  }]
}
```

### Telegram Auth Failure
Trigger if `401 Unauthorized` appears in telegram subsystem logs — indicates bot token needs rotation.

---

## Daily Log Rotation

OpenClaw creates new log files daily at `/tmp/openclaw/openclaw-YYYY-MM-DD.log`. Set up a cron job to ingest previous day's logs at 00:05 each morning:

```bash
# Add to crontab: crontab -e
5 0 * * * /home/esther/scripts/ingest-openclaw-logs.sh
```

---

## Useful OpenSearch Queries

```bash
# Count total log entries today
curl -k -u admin:PASSWORD https://localhost:9200/openclaw-logs-$(date +%Y.%m.%d)/_count

# Find all errors
curl -k -u admin:PASSWORD https://localhost:9200/openclaw-logs-*/_search \
  -H 'Content-Type: application/json' \
  -d '{"query": {"term": {"log_level": "ERROR"}}}'

# Check index health
curl -k -u admin:PASSWORD https://localhost:9200/_cat/indices/openclaw-logs-*?v
```

---

*Last updated: 2026-03-02 | Fink Security Internal*
