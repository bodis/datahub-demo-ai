# DataHub Ingestion Modes Explained

## Two Ways to Ingest Metadata

### Mode 1: CLI Ingestion (dhub ingest-run)

**How it works:**
```
Your Terminal (host machine)
    ↓
dhub datahub ingest-run
    ↓
Python SDK creates Pipeline
    ↓
Pipeline.run() executes LOCALLY on your host
    ↓
Connects to:
  - PostgreSQL: localhost:5432 (exposed port)
  - DataHub API: localhost:8080 (exposed port)
```

**Usage:**
```bash
# Default mode - uses localhost
dhub datahub ingest-run -d employees_db

# This is what happens:
# 1. Pipeline runs on your host machine
# 2. Connects to PostgreSQL at localhost:5432
# 3. Extracts table metadata
# 4. Sends to DataHub API at localhost:8080
```

**Network Requirements:**
- ✅ PostgreSQL port 5432 exposed to host
- ✅ DataHub port 8080 exposed to host
- ❌ NO Docker network needed

**Configuration:**
```yaml
source:
  config:
    host_port: localhost:5432  # Uses exposed port
sink:
  config:
    server: http://localhost:8080  # Uses exposed port
```

---

### Mode 2: DataHub UI Ingestion

**How it works:**
```
DataHub UI (browser)
    ↓
Create Ingestion Source
    ↓
Upload YAML config
    ↓
DataHub runs ingestion INSIDE its containers
    ↓
Connects to:
  - PostgreSQL: postgres_db:5432 (Docker network)
  - DataHub GMS: datahub-gms:8080 (internal service)
```

**Usage:**
```bash
# Generate configs for DataHub UI
dhub datahub ingest-generate-config -d employees_db

# This creates YAML files using Docker network:
# - postgres_db:5432 (container name)
# - datahub-gms:8080 (internal service)
```

**Network Requirements:**
- ✅ PostgreSQL on datahub_network
- ✅ Container name: postgres_db
- ❌ Exposed ports NOT used (runs inside containers)

**Configuration:**
```yaml
source:
  config:
    host_port: postgres_db:5432  # Docker container name
sink:
  config:
    server: http://datahub-gms:8080  # Internal service
```

---

## When to Use Each Mode

### Use CLI Ingestion When:
- ✅ Running from your development machine
- ✅ Quick ad-hoc ingestion
- ✅ Scripting/automation from host
- ✅ Testing ingestion locally

### Use UI Ingestion When:
- ✅ Setting up scheduled ingestion in DataHub
- ✅ Team members need to run ingestion without CLI
- ✅ Centralized ingestion management
- ✅ Production ingestion workflows

---

## Command Reference

### CLI Ingestion (Localhost Mode - Default)

```bash
# Run ingestion from your host
dhub datahub ingest-run

# Specific databases
dhub datahub ingest-run -d employees_db -d customer_db

# Without profiling (faster)
dhub datahub ingest-run --no-profiling

# See config before running
dhub datahub ingest-run --dry-run
```

### Generate Configs for UI Ingestion

```bash
# Generate YAML files for DataHub UI
dhub datahub ingest-generate-config

# These files use Docker network (postgres_db:5432)
# Upload to DataHub UI: Ingestion → Sources → Create
```

### Force CLI to Use Docker Network (Rare)

```bash
# Only if you're running dhub from inside a container
dhub datahub ingest-run --docker-mode
```

---

## Network Configuration Summary

### For CLI Ingestion (dhub ingest-run)

**PostgreSQL docker-compose.yaml:**
```yaml
services:
  postgres:
    container_name: postgres_db
    ports:
      - "5432:5432"  # ← Exposes to host
    # No network needed for CLI ingestion!
```

### For UI Ingestion

**PostgreSQL docker-compose.yaml:**
```yaml
services:
  postgres:
    container_name: postgres_db
    ports:
      - "5432:5432"
    networks:
      - datahub_network  # ← Required for UI ingestion

networks:
  datahub_network:
    external: true
    name: datahub_network
```

---

## Troubleshooting

### Error: "Failed to connect to DataHub with DataHubRestEmitter: configured to talk to http://datahub-gms:8080"

**Cause:** CLI ingestion is trying to use Docker network mode

**Fix:**
```bash
# Don't use --docker-mode flag (localhost is default)
dhub datahub ingest-run  # ✅ Uses localhost
```

### Error: "connection refused to localhost:5432"

**Cause:** PostgreSQL port not exposed or PostgreSQL not running

**Fix:**
```bash
# Check PostgreSQL is running
cd databases/postgresql && docker compose ps

# Check port is exposed
docker compose port postgres 5432
# Should show: 0.0.0.0:5432
```

### UI Ingestion Shows "connection refused to postgres_db:5432"

**Cause:** PostgreSQL not on datahub_network

**Fix:**
```bash
# Check network
docker network inspect datahub_network | grep postgres_db

# If not found, update docker-compose.yaml and restart
cd databases/postgresql
docker compose down && docker compose up -d
```

---

## Summary

| Aspect | CLI Ingestion | UI Ingestion |
|--------|--------------|--------------|
| **Where it runs** | Your host machine | DataHub containers |
| **PostgreSQL connection** | localhost:5432 | postgres_db:5432 |
| **DataHub connection** | localhost:8080 | datahub-gms:8080 |
| **Needs Docker network** | ❌ No | ✅ Yes |
| **Command** | `dhub ingest-run` | Upload YAML to UI |
| **Best for** | Development, ad-hoc | Production, scheduled |

**Key Insight:** The ingestion code runs in different places depending on the method, so they need different network configurations!

---
**Last Updated:** 2025-10-26
