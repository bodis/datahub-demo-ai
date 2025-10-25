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

## Data Generation System

### Seed Command
```bash
dhub seed all --scale 0.1          # Quick demo (120 customers, 15 employees)
dhub seed all --scale 1.0          # Base requirements (1200, 150)
dhub seed status                   # Show record counts
dhub seed clear --confirm          # Truncate all data
```

### Architecture
```
dhub/data_generators/
├── id_manager.py         # Cross-database ID tracking
├── employees.py          # Phase 1: Employees & departments
├── customers.py          # Phase 1-2: Customers & accounts
└── orchestrator.py       # Main coordinator with scale_factor
```

### Scale Factor Design
- **Fixed datasets** (don't scale): Departments (12), Training Programs (16-20), Branch Codes (15-20)
- **Scalable datasets** (multiply by scale): Employees (base 150), Customers (base 1200), Accounts (proportional)
- `scale_factor` parameter multiplies base counts while maintaining relationships

### Implementation Status
**Phase 1-2 (✅ 40%)**: employees_db (departments, employees, training), customer_db (profiles), accounts_db (customers, accounts)

**Phase 3-6 (❌ 60%)**: Transactions, Loans, Insurance, Interactions, Campaigns, Compliance (KYC, AML, Audit)

### Extending with New Phases
```python
# 1. Create generator in dhub/data_generators/loans.py
class LoanGenerator:
    def __init__(self, id_manager, scale_factor=1.0):
        self.base_applications = 400
        self.num_applications = int(self.base_applications * scale_factor)

    def generate_applications(self, customers):
        # 35% of customers apply
        applicants = random.sample(customers, k=int(len(customers) * 0.35))
        # Generate applications, store IDs in id_manager

# 2. Add to orchestrator.py
from dhub.data_generators.loans import LoanGenerator

def _generate_loans(self):
    loan_gen = LoanGenerator(self.id_manager, self.scale_factor)
    applications = loan_gen.generate_applications(self.customers)
    # Bulk insert with executemany()
```

### Key Relationships Maintained
- `customer_id`: accounts_db.customers ↔ customer_db.customer_profiles ↔ compliance_db.kyc_records
- `employee_id`: Referenced as assigned_agent_id, loan_officer_id, processed_by, etc.
- `account_id`: Links to transactions, loans (linked_account_id), insurance
- All FKs tracked in `IDManager` for referential integrity

### Data Generator Pattern
1. Calculate scaled count: `int(BASE_COUNT * scale_factor)`
2. Generate records with Faker + realistic distributions
3. Store IDs in `id_manager` for cross-references
4. Bulk insert with `executemany()` (batches of 500-1000)
5. Maintain fixed percentages (e.g., 75% customers have accounts, 25% multiple)

See `docs/data_generation.md` for full details.

## Future Extensions Ideas
- Complete Phases 3-6 (transactions, loans, insurance, compliance)
- DataHub API commands (create datasets, add lineage)
- Data validation rules
- Schema comparison tools
- Ingestion automation

---
**Last Updated**: 2025-10-25
**Package**: dhub v0.1.0
