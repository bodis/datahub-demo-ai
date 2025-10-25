# DataHub Demonstration Project

A comprehensive demonstration project showcasing DataHub's capabilities for metadata management, data lineage, and data discovery across multiple database sources.

## Project Overview

This project demonstrates a complete DataHub implementation workflow:

1. **Bootstrap DataHub** - Start DataHub locally with all required components
2. **Setup Demo Databases** - Launch PostgreSQL databases with sample data
3. **Data Ingestion** - Ingest metadata from multiple databases into DataHub
4. **CLI Operations** - Use the `dhub` CLI tool for various data operations and demonstrations

## Project Structure

```
datahub/
├── docker-compose.yml                    # DataHub quickstart compose file
├── ingest.yml                            # DataHub ingestion configuration
├── databases/
│   └── postgresql/
│       ├── docker-compose.yaml           # PostgreSQL demo database
│       └── init-scripts/                 # Database initialization scripts
│           ├── 01_init_employees_db.sql  # Employee management database
│           ├── 02_init_customer_db.sql   # Customer database
│           ├── 03_init_accounts_db.sql   # Account database
│           ├── 04_init_insurance_db.sql  # Insurance database
│           ├── 05_init_loans_db.sql      # Loans database
│           └── 06_init_compliance_db.sql # Compliance database
├── dhub/                                 # CLI application package
│   ├── cli.py                           # Main CLI entry point
│   ├── db.py                            # Database utilities
│   └── commands/
│       ├── db.py                        # Database commands
│       └── generate.py                  # Data generation commands
└── pyproject.toml                        # Project configuration
```

## Features

### DataHub Components
- Full DataHub stack (GMS, Frontend, Kafka, OpenSearch, MySQL)
- Web UI available at http://localhost:9002
- REST API available at http://localhost:8080

### Demo Databases
- **6 PostgreSQL schemas** representing different business domains:
  - Employees (HR system)
  - Customers (CRM system)
  - Accounts (Banking system)
  - Insurance (Policy management)
  - Loans (Lending system)
  - Compliance (Regulatory tracking)

### DHub CLI Tool
A beautiful command-line interface for:
- Database operations and health checks
- Fake data generation using Faker
- Query execution and visualization
- Future: Custom demonstrations and use cases

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- uv package manager

### Step 1: Install the Project

```bash
# Install dependencies and CLI tool
uv pip install -e .
```

### Step 2: Start DataHub

```bash
# Start DataHub with quickstart profile
docker compose --profile quickstart up -d

# Wait for all services to be healthy (takes ~2-3 minutes)
docker compose --profile quickstart ps

# Access DataHub UI
open http://localhost:9002
# Default credentials: datahub / datahub
```

### Step 3: Start Demo PostgreSQL Database

```bash
# Start the demo database
cd databases/postgresql
docker compose up -d

# Verify it's running
docker compose ps

# The database will be initialized with all 6 schemas automatically
cd ../..
```

### Step 4: Test the CLI

```bash
# Test database connection
dhub db test

# List all tables in the database
dhub db tables

# Get database information
dhub db info

# Generate fake users
dhub generate users 10
```

### Step 5: Run DataHub Ingestion

```bash
# Ingest PostgreSQL metadata into DataHub
datahub ingest -c ingest.yml

# Browse ingested metadata in DataHub UI
open http://localhost:9002
```

## DHub CLI Usage

### Database Commands

List all available databases:
```bash
dhub db list
```

Test database connections (all demo databases by default):
```bash
# Test all demo databases
dhub db test

# Test specific database
dhub db test --database employees_db
```

List all tables (from all demo databases by default):
```bash
# Show tables from all 6 demo databases
dhub db tables

# Show tables from specific database
dhub db tables --database customer_db

# Show tables from all databases (including system databases)
dhub db tables --all
```

Execute a SQL query:
```bash
# Query default database
dhub db query "SELECT * FROM employees LIMIT 10"

# Query specific database
dhub db query "SELECT * FROM customer_profiles LIMIT 10" --database customer_db
```

Get database information:
```bash
# Get info for default database
dhub db info

# Get info for specific database
dhub db info --database insurance_db
```

### Other Commands

Show version:
```bash
dhub version
```

Get help:
```bash
dhub --help
dhub db --help
dhub seed --help
```

## Environment Configuration

The project uses environment variables for configuration. Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

### Database Configuration

Configure PostgreSQL connection (defaults work with docker-compose setup):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```

**Note**: The CLI automatically connects to all 6 demo databases:
- `employees_db` - Employee management
- `customer_db` - Customer relationship management
- `accounts_db` - Banking accounts
- `insurance_db` - Insurance policies
- `loans_db` - Loan management
- `compliance_db` - Regulatory compliance

### DataHub Configuration

```env
DATAHUB_GMS_HOST=localhost
DATAHUB_GMS_PORT=8080
DATAHUB_TOKEN=your_token_here
```

## Demo Data Generation

Generate realistic data across all 6 databases:

```bash
# Quick demo (120 customers, 15 employees)
dhub seed all --scale 0.1

# Base requirements (1200 customers, 150 employees)
dhub seed all --scale 1.0

# Check generated data
dhub seed status
```

See [docs/data_generation.md](docs/data_generation.md) for details.

## Use Cases & Demonstrations

### Use Case 1: Multi-Database Data Discovery
- Start PostgreSQL with 6 different business domains
- Ingest metadata from all schemas into DataHub
- Explore data lineage and relationships in DataHub UI

### Use Case 2: Data Quality Monitoring
- Generate fake data using the CLI
- Set up data quality rules in DataHub
- Monitor compliance and data quality metrics

### Use Case 3: Schema Evolution Tracking
- Modify database schemas
- Re-ingest metadata
- Track schema changes in DataHub

### Use Case 4: Cross-Domain Data Lineage
- Create views that join multiple schemas
- Ingest lineage information
- Visualize cross-domain dependencies

## Development

### Install Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Format Code

```bash
ruff check --fix .
```

### Adding New CLI Commands

Create a new command in `dhub/commands/`:

```python
# dhub/commands/mycommand.py
import typer
from rich.console import Console

console = Console()
app = typer.Typer()

@app.command("hello")
def hello_world():
    """Say hello."""
    console.print("[bold green]Hello World![/bold green]")
```

Register it in `dhub/cli.py`:

```python
from dhub.commands import db, generate, mycommand

app.add_typer(mycommand.app, name="mycommand", help="My custom commands")
```

## Architecture

### Technology Stack
- **DataHub**: Metadata management and data discovery platform
- **PostgreSQL**: Demo database for various business domains
- **Python 3.11+**: CLI application
- **Typer**: CLI framework with type hints
- **Rich**: Beautiful terminal output
- **Faker**: Fake data generation
- **psycopg3**: PostgreSQL database adapter
- **uv**: Fast Python package manager

### Data Flow
```
PostgreSQL Databases → DataHub Ingestion → DataHub GMS → DataHub UI
                                                ↓
                                         Metadata Storage
                                         (MySQL + OpenSearch)
                                                ↓
                                          DHub CLI ←→ PostgreSQL
```

## Troubleshooting

### DataHub not starting
```bash
# Check service status
docker compose --profile quickstart ps

# View logs
docker compose --profile quickstart logs -f

# Restart services
docker compose --profile quickstart down
docker compose --profile quickstart up -d
```

### PostgreSQL connection issues
```bash
# Check if PostgreSQL is running
cd databases/postgresql
docker compose ps

# Check logs
docker compose logs postgres

# Test connection manually
psql -h localhost -U postgres -d mydb
```

### CLI issues
```bash
# Reinstall the package
uv pip install -e .

# Check if dhub is in PATH
which dhub

# Test with verbose output
dhub db test --help
```

## Contributing

Feel free to extend this project with:
- Additional database sources (MySQL, MongoDB, etc.)
- More CLI commands for specific use cases
- Custom DataHub ingestion recipes
- Data quality checks and validations
- Advanced data lineage demonstrations

## Resources

- [DataHub Documentation](https://datahubproject.io/docs/)
- [DataHub Quickstart Guide](https://datahubproject.io/docs/quickstart)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Faker Documentation](https://faker.readthedocs.io/)

## License

This is a demonstration project for educational purposes.
