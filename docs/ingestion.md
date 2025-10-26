# DataHub Ingestion Guide

## Quick Start

```bash
# Start DataHub and PostgreSQL
docker compose --profile quickstart up -d
cd databases/postgresql && docker compose up -d && cd ../..

# Run ingestion from CLI
dhub datahub ingest-run

# View in DataHub UI
open http://localhost:9002
```

## Two Ingestion Methods

### Method 1: CLI Ingestion (Recommended for Development)

Runs ingestion **locally on your host machine** using the DataHub Python SDK.

```bash
# Ingest all databases
dhub datahub ingest-run

# Ingest specific databases
dhub datahub ingest-run -d employees_db -d customer_db

# Without profiling (faster)
dhub datahub ingest-run --no-profiling

# Dry run (show config)
dhub datahub ingest-run --dry-run
```

**Connects to:**
- PostgreSQL: `localhost:5432` (exposed port)
- DataHub API: `localhost:8080` (exposed port)

**Requirements:**
- ✅ PostgreSQL port 5432 exposed
- ✅ DataHub port 8080 exposed
- ❌ NO Docker network needed

### Method 2: UI Ingestion (Recommended for Production)

Upload YAML configs to DataHub UI for scheduled ingestion.

```bash
# Generate configs for DataHub UI
dhub datahub ingest-generate-config

# Upload to DataHub UI: Ingestion → Sources → Create
```

**Runs inside DataHub containers using:**
- PostgreSQL: `postgres_db:5432` (container name)
- DataHub GMS: `datahub-gms:8080` (internal service)

**Requirements:**
- ✅ PostgreSQL on `datahub_network`
- ✅ Container name: `postgres_db`

## Network Setup

### For CLI Ingestion (Default)

PostgreSQL just needs exposed port:

```yaml
# databases/postgresql/docker-compose.yaml
services:
  postgres:
    container_name: postgres_db
    ports:
      - "5432:5432"  # Exposed to host
```

### For UI Ingestion

PostgreSQL needs Docker network:

```yaml
# databases/postgresql/docker-compose.yaml
services:
  postgres:
    container_name: postgres_db
    ports:
      - "5432:5432"
    networks:
      - datahub_network  # For UI ingestion

networks:
  datahub_network:
    external: true
    name: datahub_network
```

## Commands

### List Databases

```bash
dhub datahub ingest-list-databases
```

Shows all PostgreSQL databases with sizes and ingestion status.

### Run Ingestion

```bash
# All databases
dhub datahub ingest-run

# Specific databases
dhub datahub ingest-run -d employees_db -d loans_db

# Fast mode (no profiling)
dhub datahub ingest-run --no-profiling

# Preview config
dhub datahub ingest-run --dry-run
```

### Generate YAML Configs

```bash
# For all databases
dhub datahub ingest-generate-config

# For specific databases
dhub datahub ingest-generate-config -d employees_db

# Custom output directory
dhub datahub ingest-generate-config -o /path/to/configs

# Localhost mode (rare)
dhub datahub ingest-generate-config --localhost-mode
```

## Configuration

All settings come from `.env`:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# DataHub
DATAHUB_GMS_HOST=localhost
DATAHUB_GMS_PORT=8080
DATAHUB_TOKEN=your_token_here
```

## Troubleshooting

### Connection Refused to localhost:5432

**Cause:** PostgreSQL not running or port not exposed

**Fix:**
```bash
cd databases/postgresql && docker compose ps
docker compose port postgres 5432  # Should show 0.0.0.0:5432
```

### UI Ingestion: Connection Refused to postgres_db:5432

**Cause:** PostgreSQL not on datahub_network

**Fix:**
```bash
# Check network
docker network inspect datahub_network | grep postgres_db

# If not found, restart PostgreSQL after adding network config
cd databases/postgresql
docker compose down && docker compose up -d
```

### Database Not Found

**Cause:** Database doesn't exist or init scripts didn't run

**Fix:**
```bash
# List available databases
dhub datahub ingest-list-databases

# Check tables
dhub db tables -d employees_db
```

## Comparison

| Aspect | CLI Ingestion | UI Ingestion |
|--------|--------------|--------------|
| **Runs where** | Your host machine | DataHub containers |
| **PostgreSQL** | localhost:5432 | postgres_db:5432 |
| **DataHub** | localhost:8080 | datahub-gms:8080 |
| **Network** | No network needed | Needs datahub_network |
| **Command** | `dhub ingest-run` | Upload YAML |
| **Best for** | Development, ad-hoc | Production, scheduled |

---

For more details, see [DataHub documentation](https://datahubproject.io/docs/).
