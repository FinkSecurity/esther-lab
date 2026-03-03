# Fink Security — Lab Infrastructure

ESTHER's local lab environment for security research, penetration testing practice, and tool development. All containers run on the Fink Security VPS (45.82.72.151) and are accessible via SSH tunnel only.

---

## Container Stack

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| ollama | ollama/ollama | 11434 | Local LLM heartbeat (llama3.2:3b) |
| dvwa | vulnerables/web-dvwa | 80 | Damn Vulnerable Web App — pentest practice |
| dvwa-db | mysql:5.7 | 3306 | DVWA database (internal) |
| juice-shop | bkimminich/juice-shop | 3000 | OWASP Juice Shop — web vuln practice |
| opensearch | opensearchproject/opensearch | 9200 | Log ingestion and security monitoring |
| opensearch-dashboards | opensearchproject/opensearch-dashboards | 5601 | OpenSearch UI |
| portainer | portainer/portainer-ce | 9000 | Docker management UI |

---

## Accessing Lab Services (SSH Tunnel)

All lab services are firewalled and not exposed to the internet. Access via SSH tunnel from your MacBook.

### One-time SSH config setup (MacBook)

Add to `~/.ssh/config`:

```
Host esther-tunnel
  HostName 45.82.72.151
  User esther
  Port 2222
  IdentityFile ~/.ssh/esther_vps
  LocalForward 5601 localhost:5601
  LocalForward 9000 localhost:9000
  LocalForward 9200 localhost:9200
  LocalForward 80 localhost:80
  LocalForward 3000 localhost:3000
```

Then run: `ssh esther-tunnel`

All services become available at localhost on your MacBook.

### Service URLs (after tunnel is active)

| Service | URL | Credentials |
|---------|-----|-------------|
| DVWA | http://localhost:80 | admin / password |
| Juice Shop | http://localhost:3000 | — |
| OpenSearch API | https://localhost:9200 | admin / (see secrets) |
| OpenSearch Dashboards | http://localhost:5601 | admin / (see secrets) |
| Portainer | http://localhost:9000 | (set on first login) |
| Ollama API | http://localhost:11434 | — |

---

## Docker Management

```bash
# View all running containers
sudo docker ps

# Start full stack
cd ~/.openclaw/workspace/esther-lab
sudo docker compose up -d

# Stop full stack
sudo docker compose down

# Restart single container
sudo docker restart CONTAINER_NAME

# View container logs
sudo docker logs -f CONTAINER_NAME

# Shell into container
sudo docker exec -it CONTAINER_NAME bash
```

---

## DVWA Setup (first time)

1. Open http://localhost:80
2. Login: admin / password
3. Click "Create / Reset Database"
4. Login again after reset
5. Set Security Level to desired level (Low for initial practice)

---

## Juice Shop Notes

- No setup required — ready immediately on port 3000
- Score board at: http://localhost:3000/#/score-board
- All OWASP Top 10 vulnerabilities present
- Good for web app pentest practice and blog content

---

## MITRE ATT&CK Lab Targets

| Target | Relevant Techniques |
|--------|-------------------|
| DVWA | SQL Injection (T1190), XSS, Command Injection, File Upload |
| Juice Shop | Broken Auth (T1078), IDOR, XXE, Insecure Deserialization |

---

## Troubleshooting

**Container won't start:**
```bash
sudo docker logs CONTAINER_NAME
sudo docker inspect CONTAINER_NAME
```

**Port conflict:**
```bash
sudo ss -tlnp | grep PORT
```

**OpenSearch unhealthy:**
```bash
curl -k -u admin:PASSWORD https://localhost:9200/_cluster/health
```

**Full stack restart:**
```bash
sudo docker compose down
sudo docker compose up -d
sudo docker ps
```

---

*Last updated: 2026-03-02 | Fink Security Internal*
