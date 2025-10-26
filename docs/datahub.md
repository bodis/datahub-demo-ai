# DataHub Metadata Import & Management

The `dhub datahub` command group provides tools to import and manage DataHub metadata (domains and glossaries) from CSV files.

## Overview

This functionality allows you to:
- **Import domains** - Create hierarchical domain structures in DataHub
- **Import glossaries** - Create business glossary terms with parent-child relationships
- **Associate glossaries with domains** - Link glossary terms to specific domains
- **Clear metadata** - Remove domains and glossaries from DataHub

All metadata is defined in CSV files located in `databases/imports/<subdirectory>/`.

## Commands

### Import All Metadata

Import both domains and glossaries in the correct order:

```bash
# Import from all subdirectories
dhub datahub import-all

# Import from specific subdirectory
dhub datahub import-all --subdirectory bank
```

This command:
1. Imports domains first (parents before children)
2. Imports glossaries second (can reference domains)

### Import Domains Only

```bash
# Import from all subdirectories
dhub datahub import-domains

# Import from specific subdirectory
dhub datahub import-domains --subdirectory bank
```

**Features:**
- Hierarchical domain support (nested domains)
- Topological sorting (parents created before children)
- Upsert behavior (safe to re-run)

### Import Glossaries Only

```bash
# Import from all subdirectories
dhub datahub import-glossaries

# Import from specific subdirectory
dhub datahub import-glossaries --subdirectory bank
```

**Features:**
- Parent-child term relationships
- Domain associations
- Hierarchical glossary support

### Clear Metadata

Delete domains and glossaries from DataHub:

```bash
# Clear from specific subdirectory (requires confirmation)
dhub datahub clear --subdirectory bank --confirm

# Clear from all subdirectories
dhub datahub clear --confirm
```

**Safety:**
- Requires `--confirm` flag to prevent accidental deletions
- Deletes glossaries first, then domains (reverse dependency order)
- Only deletes entities defined in CSV files

## CSV File Format

### domains.csv

Defines domain hierarchy with parent-child relationships.

**Columns:**
- `domain_id` - Unique identifier for the domain
- `parent_domain_id` - ID of parent domain (empty for root domains)
- `name` - Display name
- `description` - Domain description

**Example:**

```csv
domain_id,parent_domain_id,name,description
banking_operations,,Banking Operations,Core banking operations and services
customer_management,banking_operations,Customer Management,Management of customer relationships
customer_data,customer_management,Customer Data,Core customer identification and profile information
```

This creates a hierarchy:
```
banking_operations
└── customer_management
    └── customer_data
```

### glossaries.csv

Defines business glossary terms with optional domain associations.

**Columns:**
- `glossary_id` - Unique identifier for the term
- `glossary_parent_id` - ID of parent term (empty for root terms)
- `name` - Display name
- `definition` - Term definition
- `domain_id` - Associated domain ID (optional)

**Example:**

```csv
glossary_id,glossary_parent_id,name,definition,domain_id
customer_domain_terms,,Customer Domain Terms,Terms related to customer identification,customer_management
customer_id,customer_domain_terms,Customer ID,Unique identifier for a customer,customer_data
kyc_status,customer_domain_terms,KYC Status,Know Your Customer verification status,customer_data
```

This creates:
- Root term: `customer_domain_terms` → associated with `customer_management` domain
- Child terms: `customer_id`, `kyc_status` → associated with `customer_data` domain

## Directory Structure

```
databases/imports/
├── bank/                    # Banking domain metadata
│   ├── domains.csv
│   └── glossaries.csv
├── retail/                  # Retail domain metadata (example)
│   ├── domains.csv
│   └── glossaries.csv
└── manufacturing/           # Manufacturing domain (example)
    ├── domains.csv
    └── glossaries.csv
```

## Configuration

The imports root directory is configured in `.env`:

```env
# DataHub Imports Configuration
DATAHUB_IMPORTS_ROOT=databases/imports
```

DataHub connection settings:

```env
DATAHUB_GMS_HOST=localhost
DATAHUB_GMS_PORT=8080
DATAHUB_GMS_PROTOCOL=http
DATAHUB_FRONTEND_URL=http://localhost:9002
DATAHUB_TOKEN=your_jwt_token_here
```

## Workflow Example

### 1. Prepare CSV Files

Create `databases/imports/bank/domains.csv` and `glossaries.csv` with your metadata.

### 2. Import to DataHub

```bash
# Import all metadata
dhub datahub import-all --subdirectory bank
```

**Output:**
```
Step 1: Importing Domains
Found 15 domain(s)
✓ Completed

Step 2: Importing Glossaries
Found 49 glossary term(s)
✓ Completed

Total imported: 64
```

### 3. Verify in DataHub UI

- Domains: http://localhost:9002/domains
- Glossary: http://localhost:9002/glossary

### 4. Update and Re-import

Modify CSV files and re-run import (upsert behavior):

```bash
dhub datahub import-all --subdirectory bank
```

### 5. Clear When Needed

```bash
# Remove all imported metadata
dhub datahub clear --subdirectory bank --confirm
```

## Features & Capabilities

### Hierarchical Support

Both domains and glossaries support arbitrary nesting levels:

**Domains:**
```
banking_operations
├── customer_management
│   ├── customer_data
│   └── customer_experience
├── financial_products
│   ├── deposit_services
│   └── lending_services
└── risk_compliance
```

**Glossaries:**
```
customer_domain_terms
├── customer_identification
│   ├── customer_id
│   ├── kyc_status
│   └── customer_segment
└── customer_lifecycle
    ├── onboarding_date
    └── customer_status
```

### Domain-Glossary Associations

Glossary terms can be associated with domains via the `domain_id` column:

```csv
glossary_id,glossary_parent_id,name,definition,domain_id
customer_id,customer_identification,Customer ID,Unique identifier,customer_data
```

This creates a relationship: `customer_id` term → `customer_data` domain

### Upsert Behavior

All import commands use upsert (update or insert):
- Existing entities are updated
- New entities are created
- Safe to re-run imports

### Batch Processing

The CLI searches for CSV files in all subdirectories by default:

```bash
# Imports from all subdirectories under databases/imports/
dhub datahub import-all
```

Use `--subdirectory` to target specific imports:

```bash
# Only import from databases/imports/bank/
dhub datahub import-all --subdirectory bank
```

## Best Practices

1. **Start with domains** - Define domain hierarchy first
2. **Group glossaries by domain** - Use `domain_id` to associate terms
3. **Use clear IDs** - Use descriptive, lowercase IDs with underscores
4. **Document relationships** - Use parent columns to show hierarchy
5. **Version control CSVs** - Keep CSV files in git for change tracking
6. **Test incrementally** - Import and verify before adding more entries

## Troubleshooting

### Import fails with "Connection refused"

DataHub is not running. Start it:

```bash
docker compose --profile quickstart up -d
```

### Parent domain warnings

```
Warning: Parent domain relationship not set (ParentDomainsClass not available)
```

This is a known limitation in some DataHub versions. Domains are still created successfully, but parent-child relationships may not display in the UI.

### Clear fails to delete entities

Ensure you're using the `--confirm` flag:

```bash
dhub datahub clear --subdirectory bank --confirm
```

### CSV parsing errors

Check CSV format:
- Use UTF-8 encoding
- Include header row
- Use comma as delimiter
- Quote fields containing commas

## Example Dataset

A complete banking domain example is included at `databases/imports/bank/`:

- **15 domains** - Hierarchical banking operations structure
- **49 glossary terms** - Business terms across customer, products, risk, and operations
- **Full relationships** - Parent-child and domain associations

Explore these files to understand the format and capabilities.

---

**View imported metadata:**
- Domains: http://localhost:9002/domains
- Glossary: http://localhost:9002/glossary
