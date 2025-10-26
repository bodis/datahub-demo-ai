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
- `dhub/commands/seed.py` - Demo data seeding

### Data Generators
- `dhub/data_generators/id_manager.py` - Cross-database ID tracking
- `dhub/data_generators/unique_generator.py` - Unique value generation with deduplication
- `dhub/data_generators/employees.py` - Employee, training, reviews, assignments
- `dhub/data_generators/customers.py` - Customers, accounts, transactions, CRM
- `dhub/data_generators/loans.py` - Loan applications, loans, collateral, schedules
- `dhub/data_generators/orchestrator.py` - Main coordinator with 5-phase pipeline

## CLI Commands Structure

```bash
dhub
├── version                           # Show version
├── db                                # Database operations
│   ├── list                         # List all databases
│   ├── test [--database DB]         # Test connection(s)
│   ├── tables [--database DB]       # List tables
│   ├── query "SQL" [--database DB]  # Execute SQL
│   └── info [--database DB]         # Database info
└── seed                              # Demo data generation
    ├── all [--scale N]              # Generate demo data
    ├── status                       # Show record counts
    └── clear --confirm              # Truncate all data
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

1. **employees_db** (6 tables) - HR system
   - departments, employees, training_programs
   - employee_training, performance_reviews, employee_assignments

2. **customer_db** (6 tables) - CRM system
   - customer_profiles, interactions, satisfaction_surveys
   - complaints, campaigns, campaign_responses

3. **accounts_db** (4 tables) - Banking operations
   - customers, accounts, account_relationships, transactions

4. **loans_db** (6 tables) - Loan management
   - loan_applications, loans, collateral
   - repayment_schedule, loan_guarantors, risk_assessments

5. **insurance_db** (5 tables) - Insurance products (not yet implemented)
   - policies, claims, beneficiaries, coverage, premium_payments

6. **compliance_db** (7 tables) - Regulatory compliance (not yet implemented)
   - kyc_records, aml_checks, suspicious_activity_reports
   - regulatory_reports, audit_logs, compliance_rules, rule_violations

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
dhub seed all --scale 0.1          # Quick demo (~5,000 records)
dhub seed all --scale 1.0          # Base requirements (~60,000 records)
dhub seed status                   # Show record counts
dhub seed clear --confirm          # Truncate all data
```

### Architecture
```
dhub/data_generators/
├── id_manager.py            # Cross-database ID tracking & role mapping
├── unique_generator.py      # Unique value generation (prevents duplicates)
├── employees.py             # Employees, training, reviews, assignments
├── customers.py             # Customers, accounts, transactions, CRM
├── loans.py                 # Complete loan lifecycle & risk assessment
└── orchestrator.py          # 5-phase pipeline with retry logic
```

### 5-Phase Generation Pipeline

**Phase 1: Foundation Data**
- departments, employees, training_programs
- customers (master + profiles)

**Phase 2: Core Banking Products**
- accounts, account_relationships
- transactions (10-20x accounts)

**Phase 3: CRM & Customer Engagement**
- interactions, satisfaction_surveys
- complaints, campaigns, campaign_responses

**Phase 4: Employee Development** (NEW)
- employee_training (2-4 programs per employee)
- performance_reviews (1-3 annual reviews)
- employee_assignments (customer portfolios + branch coverage)

**Phase 5: Loan Products** (NEW)
- loan_applications (~35% of customers apply)
- loans (with realistic amortization)
- collateral, repayment_schedule
- loan_guarantors, risk_assessments

### Scale Factor Design
- **Fixed datasets** (don't scale): Departments (12), Training Programs (16), Branch Codes (20)
- **Scalable datasets** (multiply by scale): Employees (base 150), Customers (base 1200), Loans (proportional)
- `scale_factor` parameter multiplies base counts while maintaining relationships

### Implementation Status
**Phases 1-5 (✅ 85% Complete)**:
- ✅ employees_db (6/6 tables populated)
- ✅ customer_db (6/6 tables populated)
- ✅ accounts_db (4/4 tables populated)
- ✅ loans_db (6/6 tables populated)

**Phases 6-7 (❌ 15% Remaining)**:
- ⬜ insurance_db (0/5 tables)
- ⬜ compliance_db (0/7 tables)

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
- `customer_id`: accounts_db.customers ↔ customer_db.customer_profiles ↔ loans_db.loan_applications
- `employee_id`: Referenced as assigned_agent_id, officer_id, approved_by, assessed_by, reviewer_id, handled_by, processed_by
- `account_id`: Links to transactions, account_relationships, loans (linked_account_id)
- `application_id`: Links loan_applications ↔ loans
- `loan_id`: Links loans → collateral, repayment_schedule, loan_guarantors, risk_assessments
- `program_id`: Links training_programs ↔ employee_training
- All FKs tracked in `IDManager` for referential integrity

### Data Generator Pattern
1. **Calculate scaled count**: `int(BASE_COUNT * scale_factor)`
2. **Generate unique values**: Use `UniqueValueGenerator` for emails, phones (prevents duplicates)
3. **Generate records**: Faker + realistic distributions (weighted random selections)
4. **Store IDs**: Track in `id_manager` for cross-database references
5. **Bulk insert**: Use `executemany()` with batches of 1,000 for large datasets
6. **Maintain percentages**: Fixed ratios (e.g., 75% customers have accounts, 35% apply for loans)
7. **Retry on errors**: Automatic retry with generator reset on constraint violations

See `docs/data_generation.md` for full details.

## Future Extensions Ideas
- ✅ ~~Complete loan products (Phase 5)~~ - DONE
- ⬜ Complete insurance products (Phase 6)
- ⬜ Complete compliance tracking (Phase 7)
- ⬜ DataHub API commands (create datasets, add lineage)
- ⬜ Data validation rules
- ⬜ Schema comparison tools
- ⬜ Ingestion automation
- ⬜ Real-time data generation for streaming demos

## Recent Changes

**2025-10-26**:
- ✅ Added `unique_generator.py` for duplicate-free email/phone generation
- ✅ Implemented Phase 4: Employee Development (training, reviews, assignments)
- ✅ Implemented Phase 5: Loan Products (applications, loans, collateral, schedules, guarantors, risk assessments)
- ✅ Extended `employees.py` with 3 new generator methods
- ✅ Created `loans.py` generator with complete loan lifecycle
- ✅ Updated orchestrator with 5-phase pipeline and retry logic
- ✅ Extended `id_manager.py` with role mapping and training program tracking
- ✅ All employees_db tables now populated (6/6)
- ✅ All loans_db tables now populated (6/6)
- ✅ Dataset now generates ~60,000 records @ scale 1.0 (was ~19,000)

---
**Last Updated**: 2025-10-26
**Package**: dhub v0.1.0
