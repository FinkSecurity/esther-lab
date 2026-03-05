# ENVIRONMENT.md — Service Credentials & Configuration

## Services

### OpenSearch
- **URL:** https://localhost:9200
- **Admin Username:** admin
- **Admin Password:** Stored in `esther-lab/.env` as `OPENSEARCH_PASSWORD`
- **Status:** Running in Docker via docker-compose
- **Container Name:** opensearch

### OpenSearch Dashboards
- **URL:** http://localhost:5601
- **Username:** admin
- **Password:** Stored in `esther-lab/.env` (synchronized with OpenSearch)
- **Container Name:** opensearch-dashboards

### MySQL (DVWA Backend)
- **Host:** localhost:3306
- **Root Password:** Stored in `esther-lab/.env` as `MYSQL_ROOT_PASSWORD`
- **User Password:** Stored in `esther-lab/.env` as `MYSQL_PASSWORD`
- **Container Name:** mysql

### DVWA (Damn Vulnerable Web Application)
- **URL:** http://localhost:80
- **Admin Username:** admin
- **Admin Password:** password
- **Status:** Running in Docker via docker-compose
- **Container Name:** dvwa

## Environment Files

**DO NOT commit secrets to version control.**

- **esther-lab/.env** — Production secrets (git-ignored)
  - OPENSEARCH_PASSWORD
  - MYSQL_ROOT_PASSWORD
  - MYSQL_PASSWORD

## Docker Compose

All services are managed via `esther-lab/docker-compose.yml`:

```bash
cd esther-lab
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
docker-compose logs -f    # View logs
```

## API Keys & Tokens

(None configured yet — add here as services expand)

## Notes

- All services use self-signed SSL certificates (localhost:9200 requires `-k` with curl)
- Passwords are environment-specific; do not hardcode credentials in code
- Monitor `.env` file access; it contains sensitive data
