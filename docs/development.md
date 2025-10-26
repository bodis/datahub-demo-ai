# Development Guide

## Project Overview

DataHub demonstration project with CLI tools for database operations and metadata management.

**Purpose**: Demonstrate DataHub capabilities by:
1. Running local PostgreSQL with 6 business domain databases
2. Generating realistic test data via CLI
3. Ingesting metadata into DataHub
4. Managing cross-database relationships and business metadata

## Architecture

```
DataHub Stack (docker-compose.yml)
    ↓
PostgreSQL Databases (databases/postgresql/)
    ↓
DHub CLI (dhub/) ← Python package with Typer + Rich
```

## Key Files

### Configuration
- `.env` - Active config (PostgreSQL + DataHub settings)
- `.env.example` - Template with all options
- `pyproject.toml` - Python project (uv package manager)

### Databases
- `databases/postgresql/docker-compose.yaml` - PostgreSQL container
- `databases/postgresql/init-scripts/*.sql` - 6 database schemas

### CLI Application
- `dhub/cli.py` - Main entry point
- `dhub/config.py` - Config class (loads .env)
- `dhub/db.py` - Database utilities (psycopg3)
- `dhub/commands/` - Command modules

### Data Generators
- `dhub/data_generators/orchestrator.py` - Main coordinator with 5-phase pipeline
- `dhub/data_generators/employees.py` - Employee, training, reviews
- `dhub/data_generators/customers.py` - Customers, accounts, transactions
- `dhub/data_generators/loans.py` - Loans, applications, collateral

## CLI Commands

```bash
dhub
├── version                     # Show version
├── db                         # Database operations
│   ├── list                  # List databases
│   ├── test                  # Test connections
│   ├── tables                # List tables
│   ├── query                 # Execute SQL
│   └── info                  # Database info
├── seed                       # Demo data generation
│   ├── all                   # Generate all data
│   ├── status                # Show record counts
│   └── clear                 # Truncate data
└── datahub                    # DataHub operations
    ├── ingest-run            # Run ingestion
    ├── list-tables           # View metadata
    ├── import-domains        # Import domains from CSV
    ├── import-glossaries     # Import glossaries from CSV
    ├── register-structured-properties  # Register property definitions
    └── update-column-metadata  # Apply structured properties from YAML
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Package Manager | uv |
| CLI Framework | Typer |
| Terminal UI | Rich |
| Database | PostgreSQL 16 |
| DB Driver | psycopg3 |
| Fake Data | Faker |
| Config | python-dotenv |
| DataHub | Acryl Data |

## Environment Variables

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# DataHub
DATAHUB_GMS_HOST=localhost
DATAHUB_GMS_PORT=8080
DATAHUB_TOKEN=<jwt_token>
```

## Package Installation

```bash
# Install CLI package
uv pip install -e .

# With dev dependencies
uv pip install -e ".[dev]"
```

## Adding New CLI Commands

1. Create `dhub/commands/mycommand.py`:

```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def hello():
    """Say hello."""
    console.print("[green]Hello![/green]")
```

2. Register in `dhub/cli.py`:

```python
from dhub.commands import mycommand

app.add_typer(mycommand.app, name="mycommand", help="...")
```

## Database Schemas

All 6 databases are initialized on first PostgreSQL start:

1. **employees_db** (6 tables) - HR system
2. **customer_db** (6 tables) - CRM system
3. **accounts_db** (4 tables) - Banking operations
4. **loans_db** (6 tables) - Loan management
5. **insurance_db** (5 tables) - Insurance products
6. **compliance_db** (7 tables) - Regulatory compliance

## Data Generation System

### Seed Command

```bash
dhub seed all --scale 0.1    # Quick demo
dhub seed all --scale 1.0    # Base requirements
dhub seed status             # Show record counts
```

### 5-Phase Generation Pipeline

1. **Foundation**: departments, employees, training_programs, customers
2. **Core Banking**: accounts, account_relationships, transactions
3. **CRM**: interactions, surveys, complaints, campaigns
4. **Employee Development**: training, reviews, assignments
5. **Loan Products**: applications, loans, collateral, schedules

### Scale Factor Design

- **Fixed datasets** (don't scale): Departments (12), Training Programs (16)
- **Scalable datasets** (multiply by scale): Employees (base 150), Customers (base 1200)
- Maintains relationships (e.g., 75% customers have accounts, 35% apply for loans)

## Key Patterns

### Database Connection

```python
from dhub.db import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")
        results = cur.fetchall()  # Returns dict rows
```

### Rich Output

```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Results")
table.add_column("Name", style="green")
console.print(table)
```

### Config Access

```python
from dhub.config import config

db_url = config.get_postgres_connection_string()
datahub_url = config.get_datahub_url()
```

## Troubleshooting

**CLI not found**: `uv pip install -e .`

**DB connection fails**:
- Check PostgreSQL: `cd databases/postgresql && docker compose ps`
- Check .env settings

**DataHub not starting**:
- `docker compose --profile quickstart logs -f`
- Wait for health checks (2-3 min)

## Documentation

- [ingestion.md](ingestion.md) - DataHub ingestion guide
- [structured_properties.md](structured_properties.md) - Cross-database FK documentation
- [datahub.md](datahub.md) - Domains & glossaries management
- [data_generation.md](data_generation.md) - Data generation details

---

**Last Updated**: 2025-10-27
