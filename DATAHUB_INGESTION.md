# DataHub Database Ingestion

## Overview

The `dhub` CLI now supports **programmatic database ingestion** using the DataHub Python SDK. You can ingest PostgreSQL database metadata directly into DataHub without manually writing YAML files.

## Commands

### 1. List Available Databases
```bash
dhub datahub ingest-list-databases
```

Shows all PostgreSQL databases with their sizes and whether they're in the default ingestion list.

### 2. Run Ingestion from CLI (Localhost Mode)
```bash
# Ingest all databases (runs locally, uses localhost)
dhub datahub ingest-run

# Ingest specific databases
dhub datahub ingest-run -d employees_db -d customer_db

# Ingest without profiling (faster)
dhub datahub ingest-run --no-profiling

# Dry run (show config without running)
dhub datahub ingest-run --dry-run
```

**Features:**
- Pipeline runs **locally on your host machine**
- Uses `localhost:5432` for PostgreSQL (exposed port)
- Uses `localhost:8080` for DataHub API (exposed port)
- No Docker network required
- Automatically validates databases exist before ingestion
- Includes table profiling (row counts, statistics)
- Includes view lineage detection

### 3. Generate YAML Configs for DataHub UI
```bash
# Generate configs for DataHub UI ingestion (uses Docker network)
dhub datahub ingest-generate-config

# Generate for specific databases
dhub datahub ingest-generate-config -d employees_db -d customer_db

# Custom output directory
dhub datahub ingest-generate-config -o /path/to/configs

# Generate for localhost (rare - when PostgreSQL not in Docker)
dhub datahub ingest-generate-config --localhost-mode
```

**Use cases:**
- Upload to DataHub UI for scheduled ingestion
- Reference configurations
- Backup/version control for ingestion configs

## Architecture

### Database Structure
This project uses **separate databases**, not schemas:
```
PostgreSQL Server (container: postgres_db)
├── employees_db (database)
│   └── public (schema)
│       ├── employees
│       ├── departments
│       └── ...
├── customer_db (database)
│   └── public (schema)
│       ├── customer_profiles
│       └── ...
└── ...
```

### Network Configuration

**For CLI Ingestion (`dhub ingest-run`):**
- ✅ PostgreSQL must expose port 5432
- ✅ DataHub must expose port 8080
- ❌ Docker network NOT required

**For UI Ingestion (DataHub UI):**
- ✅ PostgreSQL must be on `datahub_network`
- ✅ Container name must be `postgres_db`

```yaml
# databases/postgresql/docker-compose.yaml
services:
  postgres:
    container_name: postgres_db
    ports:
      - "5432:5432"  # Required for CLI ingestion
    networks:
      - datahub_network  # Required for UI ingestion
    # ...

networks:
  datahub_network:
    external: true
    name: datahub_network
```

### Connection Flow (CLI Ingestion)

```
dhub CLI (host machine)
    ↓
DataHub Python SDK creates ingestion pipeline
    ↓
Pipeline runs LOCALLY on your host machine
    ↓
Connects via exposed ports:
  - PostgreSQL: localhost:5432
  - DataHub API: localhost:8080
```

**Key insight:** When you run `dhub datahub ingest-run`, the pipeline executes **locally on your host**, not inside containers. It uses `localhost` to connect to exposed Docker ports.

### Connection Flow (UI Ingestion)

```
DataHub UI → Upload YAML config
    ↓
Ingestion runs INSIDE DataHub containers
    ↓
Uses Docker network:
  - PostgreSQL: postgres_db:5432 (container name)
  - DataHub GMS: datahub-gms:8080 (internal service)
```

For UI-based ingestion, PostgreSQL **must** be on `datahub_network`.

## Configuration

All connection parameters come from `.env`:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# DataHub
DATAHUB_GMS_HOST=localhost
DATAHUB_GMS_PORT=8080
DATAHUB_TOKEN=eyJhbGc...  # Your DataHub API token
```

## Example Workflow

### Quick Start (CLI Ingestion)

```bash
# 1. Start DataHub
docker compose --profile quickstart up -d

# 2. Start PostgreSQL (just needs exposed port for CLI)
cd databases/postgresql
docker compose up -d
cd ../..

# 3. Generate demo data
dhub seed all --scale 0.5

# 4. List available databases
dhub datahub ingest-list-databases

# 5. Run ingestion from CLI (uses localhost)
dhub datahub ingest-run -d employees_db -d customer_db

# 6. View in DataHub UI
# http://localhost:9002 (username: datahub, password: datahub)
```

### Setup for UI Ingestion (Optional)

If you want to use DataHub UI for ingestion:

```bash
# 1. Ensure PostgreSQL is on datahub_network
docker network inspect datahub_network | grep postgres_db

# 2. If not found, PostgreSQL needs network config:
#    (Already configured in databases/postgresql/docker-compose.yaml)

# 3. Generate YAML configs for UI
dhub datahub ingest-generate-config

# 4. Upload configs to DataHub UI
#    Navigate to: Ingestion → Sources → Create New Source
#    Upload: ingest_configs/ingest_employees_db.yml
```

## Generated YAML Files

The generated YAML files use **Docker container names** by default:

```yaml
pipeline_name: pg_local_employees_db
source:
  type: postgres
  config:
    host_port: postgres_db:5432  # ← Container name, not localhost
    database: employees_db
    username: postgres
    password: postgres
    include_tables: true
    include_views: true
    schema_pattern:
      allow:
        - public
    profiling:
      enabled: true
      profile_table_level_only: false
    include_view_lineage: true
    include_view_column_lineage: true
sink:
  type: datahub-rest
  config:
    server: http://datahub-gms:8080  # ← Internal service, not localhost
    token: <your-token>
```

These configs work for:
- ✅ DataHub UI-based ingestion
- ✅ `dhub datahub ingest-run` (Python SDK)
- ✅ Official `datahub ingest` CLI (if run from within containers)

**For localhost mode** (rare, when PostgreSQL is NOT on datahub_network):
```bash
dhub datahub ingest-generate-config --localhost-mode
```

## Troubleshooting

### PostgreSQL Not Reachable from DataHub
**Issue:** Ingestion registered but cannot reach PostgreSQL

**Root Cause:** PostgreSQL and DataHub are on different Docker networks

**Solution:**
1. Verify PostgreSQL is on `datahub_network`:
   ```bash
   docker network inspect datahub_network | grep postgres_db
   ```
2. If not found, update `databases/postgresql/docker-compose.yaml`:
   ```yaml
   services:
     postgres:
       networks:
         - datahub_network

   networks:
     datahub_network:
       external: true
       name: datahub_network
   ```
3. Restart PostgreSQL:
   ```bash
   cd databases/postgresql
   docker compose down
   docker compose up -d
   ```

### DataHub Connection Error
**Issue:** `Failed to connect to DataHub`

**Solution:**
1. Verify DataHub is running: `docker compose --profile quickstart ps`
2. Check GMS health: `curl http://localhost:8080/health`
3. Verify token in `.env` is valid

### Database Not Found
**Issue:** `None of the specified databases exist`

**Solution:**
1. List available databases: `dhub datahub ingest-list-databases`
2. Verify init scripts ran: `dhub db tables -d employees_db`
3. Check PostgreSQL logs: `cd databases/postgresql && docker compose logs`

### Ingestion Shows Wrong Host
**Issue:** Config shows `localhost` instead of `postgres_db`

**Solution:**
By default, commands use Docker mode. If you see `localhost`, you may have used `--localhost-mode` flag. Remove it or use `--docker-mode` explicitly.

## Comparison: Python vs YAML Ingestion

| Feature | Python SDK (dhub ingest-run) | YAML + datahub CLI |
|---------|------------------------------|---------------------|
| Setup | Already configured via `.env` | Need to create YAML files |
| Validation | Validates databases before running | Fails during ingestion |
| Batching | Can loop through databases in script | Must run separately for each |
| Progress | Shows progress in CLI | Limited feedback |
| Debugging | Python exceptions | YAML validation errors |
| CI/CD | Good for automation | Good for GitOps |

**Recommendation:** Use Python SDK (`dhub ingest-run`) for development and ad-hoc ingestion. Use YAML files for production CI/CD pipelines.

## Next Steps

**Completed (✅):**
- Python-based ingestion via DataHub SDK
- YAML config generation
- Database listing and validation
- Connection parameter reuse from `.env`

**Future Enhancements:**
- Schedule automated ingestion (cron jobs)
- Incremental ingestion (only changed tables)
- Custom domain/tag assignment during ingestion
- Integration with DataHub domains/glossaries from CSV files
- Ingestion for other data sources (MySQL, Snowflake, etc.)

---
**Last Updated:** 2025-10-26
