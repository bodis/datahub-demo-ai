# CLAUDE.md - Project Context

## Project Overview
DataHub demonstration project with CLI tools for database operations and fake data generation.

**Purpose**: Demonstrate DataHub metadata management by:
1. Running local PostgreSQL with 6 business domain schemas
2. Generating/managing test data via CLI
3. Ingesting metadata into DataHub
4. Showing lineage, discovery, and governance features

## Key Architecture

```
DataHub Stack (docker-compose.yml)
    ↓
PostgreSQL Demo DB (databases/postgresql/)
    ↓
DHub CLI (dhub/) ← Python package with Typer + Rich
```

## Important Files

### Configuration
- `.env` - Active config (PostgreSQL + DataHub settings)
- `.env.example` - Template with all options
- `pyproject.toml` - Python project (uv package manager)

### Database
- `databases/postgresql/docker-compose.yaml` - PostgreSQL container
- `databases/postgresql/init-scripts/*.sql` - 6 schemas:
  - `01_init_employees_db.sql`
  - `02_init_customer_db.sql`
  - `03_init_accounts_db.sql`
  - `04_init_insurance_db.sql`
  - `05_init_loans_db.sql`
  - `06_init_compliance_db.sql`

### CLI Application
- `dhub/cli.py` - Main entry point
- `dhub/config.py` - Config class (loads .env)
- `dhub/db.py` - Database utilities (psycopg3)
- `dhub/commands/db.py` - Database commands
- `dhub/commands/generate.py` - Faker data generation

## CLI Commands Structure

```bash
dhub
├── version                           # Show version
├── db                                # Database operations
│   ├── test                         # Test connection
│   ├── tables                       # List all tables
│   ├── query "SQL"                  # Execute SQL
│   └── info                         # DB info
└── generate                          # Fake data generation
    ├── users <count> [--insert]     # Generate users
    ├── companies <count>            # Generate companies
    ├── addresses <count>            # Generate addresses
    └── custom <method> --count N    # Any Faker method
```

## Common Workflows

### Start PostgreSQL Demo DB
```bash
cd databases/postgresql
docker compose up -d
cd ../..
dhub db test
dhub db tables
```

### Generate Test Data
```bash
# Just display
dhub generate users 10

# Insert into DB
dhub generate users 100 --create-table --insert
```

### Start DataHub
```bash
docker compose --profile quickstart up -d
# Wait ~2-3 minutes for health checks
# UI: http://localhost:9002 (datahub/datahub)
```

### Ingest Metadata
```bash
datahub ingest -c ingest.yml
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Package Manager | uv | Fast Python package installer |
| CLI Framework | Typer | Type-safe CLI with auto-completion |
| Terminal UI | Rich | Beautiful tables, colors, progress |
| Database | PostgreSQL 16 | Demo database |
| DB Driver | psycopg3 | PostgreSQL adapter |
| Fake Data | Faker | Generate realistic test data |
| Config | python-dotenv | Load .env files |
| DataHub | Acryl Data | Metadata platform |

## Environment Variables

**PostgreSQL** (from `.env`):
- `POSTGRES_HOST=localhost`
- `POSTGRES_PORT=5432`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_DB=mydb`

**DataHub**:
- `DATAHUB_GMS_HOST=localhost`
- `DATAHUB_GMS_PORT=8080`
- `DATAHUB_TOKEN=<jwt_token>`

## Package Installation

```bash
# Install CLI package (editable mode)
uv pip install -e .

# With dev dependencies
uv pip install -e ".[dev]"
```

## Code Organization

```python
# Adding new CLI command group
# 1. Create dhub/commands/mycommand.py
import typer
from rich.console import Console

app = typer.Typer()

@app.command()
def hello():
    """Say hello."""
    console.print("[green]Hello![/green]")

# 2. Register in dhub/cli.py
from dhub.commands import db, generate, mycommand
app.add_typer(mycommand.app, name="mycommand", help="...")
```

## Database Schema Summary

All 6 schemas are initialized on first PostgreSQL start:

1. **employees** - HR system (departments, employees, salaries)
2. **customer** - CRM (customers, contacts, interactions)
3. **accounts** - Banking (accounts, transactions)
4. **insurance** - Policies, claims, coverage
5. **loans** - Loan applications, payments
6. **compliance** - Regulatory tracking, audits

## Troubleshooting Quick Ref

**CLI not found**: `uv pip install -e .`

**DB connection fails**:
- Check PostgreSQL: `cd databases/postgresql && docker compose ps`
- Check .env settings

**DataHub not starting**:
- `docker compose --profile quickstart logs -f`
- Wait for health checks (can take 2-3 min)

**Import errors**: `uv pip list` to check installed packages

## Dependencies

```toml
faker>=22.0.0           # Fake data generation
psycopg[binary]>=3.2.0  # PostgreSQL driver
typer>=0.12.0           # CLI framework
rich>=13.7.0            # Terminal formatting
python-dotenv>=1.0.0    # Environment variables
shellingham>=1.5.0      # Shell detection for completion
```

## Key Patterns

**Database connection**:
```python
from dhub.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")
        results = cur.fetchall()  # Returns dict rows
```

**Rich output**:
```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Results")
table.add_column("Name", style="green")
console.print(table)
```

**Config access**:
```python
from dhub.config import config

db_url = config.get_postgres_connection_string()
datahub_url = config.get_datahub_url()
```

## Future Extensions Ideas
- DataHub API commands (create datasets, add lineage)
- Data validation rules
- Schema comparison tools
- Ingestion automation
- Custom data quality checks

---
**Last Updated**: 2025-10-25
**Package**: dhub v0.1.0
