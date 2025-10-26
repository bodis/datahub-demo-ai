# Structured Properties Guide

This guide explains how to use structured properties in DataHub to document cross-database foreign key relationships and other column-level metadata.

## Overview

Structured properties allow you to attach custom metadata to schema fields (columns) in DataHub. This is particularly useful for:

- Documenting cross-database foreign key relationships
- Adding business metadata to columns
- Tracking data lineage across databases
- Enriching column documentation

## Available Structured Properties

The following structured properties are defined in `databases/datahub/structured-properties.yaml`:

### Foreign Key Properties

1. **fk_target_table** (string)
   - Fully qualified name of the table this column references (database.schema.table)
   - Example: `accounts_db.public.customers`

2. **fk_target_column** (string)
   - Column name in the target table that this column references
   - Example: `customer_id`

3. **fk_cross_database** (string: "true" or "false")
   - Whether this FK references a table in a different database
   - Allowed values: "true", "false"

4. **fk_relationship_description** (string)
   - Human-readable description of this foreign key relationship
   - Example: "Links loan to customer master record in accounts database"

## Quick Start

### Step 1: Register Structured Properties

First, register the structured property definitions in DataHub:

```bash
dhub datahub register-structured-properties
```

This reads the definitions from `databases/datahub/structured-properties.yaml` and creates them in DataHub.

**Note:** You only need to do this once, unless you add new property definitions.

### Step 2: Create a Metadata YAML File

Create a YAML file defining the column metadata you want to add:

```yaml
tables:
  - database: loans_db
    schema: public
    table: loans
    columns:
      - name: customer_id
        description: "Customer who received the loan - references accounts_db.public.customers"
        structured_properties:
          fk_target_table: "accounts_db.public.customers"
          fk_target_column: "customer_id"
          fk_cross_database: "true"
          fk_relationship_description: "Links loan to customer master record"
```

See `examples/column_metadata_example.yaml` for a complete example.

### Step 3: Preview Changes (Optional)

Preview what will be updated without actually making changes:

```bash
dhub datahub update-column-metadata examples/column_metadata_example.yaml --dry-run
```

### Step 4: Apply the Metadata

Apply the metadata updates to DataHub:

```bash
dhub datahub update-column-metadata examples/column_metadata_example.yaml
```

### Step 5: View the Results

List tables with column details to see the structured properties:

```bash
# View in terminal
dhub datahub list-tables --database loans_db --with-columns

# Export to YAML
dhub datahub list-tables --database loans_db --with-columns --yaml > loans_metadata.yaml
```

## CLI Commands Reference

### Register Structured Properties

```bash
# Register from default file (databases/datahub/structured-properties.yaml)
dhub datahub register-structured-properties

# Register from custom file
dhub datahub register-structured-properties --file my-properties.yaml
```

### Update Column Metadata

```bash
# Update from YAML file
dhub datahub update-column-metadata metadata.yaml

# Preview changes without applying
dhub datahub update-column-metadata metadata.yaml --dry-run
```

### List Tables with Structured Properties

```bash
# List all tables
dhub datahub list-tables

# List tables from specific database with column details
dhub datahub list-tables --database loans_db --with-columns

# Export to YAML format
dhub datahub list-tables --database loans_db --with-columns --yaml
```

## YAML File Format

### Basic Structure

```yaml
tables:
  - database: <database_name>
    schema: <schema_name>      # Optional, defaults to "public"
    table: <table_name>
    columns:
      - name: <column_name>
        description: <description>              # Optional
        structured_properties:                   # Optional
          <property_name>: <property_value>
          ...
```

### Example: Cross-Database Foreign Key

```yaml
tables:
  - database: loans_db
    schema: public
    table: loans
    columns:
      - name: customer_id
        description: "Customer who received the loan"
        structured_properties:
          fk_target_table: "accounts_db.public.customers"
          fk_target_column: "customer_id"
          fk_cross_database: "true"
          fk_relationship_description: "Links to customer master record"

      - name: linked_account_id
        description: "Bank account for loan disbursement"
        structured_properties:
          fk_target_table: "accounts_db.public.accounts"
          fk_target_column: "account_id"
          fk_cross_database: "true"
          fk_relationship_description: "Links to disbursement account"
```

### Example: Update Only Description

```yaml
tables:
  - database: accounts_db
    schema: public
    table: customers
    columns:
      - name: customer_id
        description: "Unique customer identifier - master record"
```

### Example: Multiple Tables

```yaml
tables:
  - database: loans_db
    schema: public
    table: loans
    columns:
      - name: customer_id
        structured_properties:
          fk_target_table: "accounts_db.public.customers"
          fk_target_column: "customer_id"

  - database: customer_db
    schema: public
    table: customer_profiles
    columns:
      - name: customer_id
        structured_properties:
          fk_target_table: "accounts_db.public.customers"
          fk_target_column: "customer_id"
```

## Complete Workflow Example

Here's a complete workflow for documenting cross-database relationships:

```bash
# 1. Ensure DataHub is running
docker compose --profile quickstart up -d

# 2. Ingest database metadata
dhub datahub ingest-run --database loans_db --database accounts_db

# 3. Register structured property definitions
dhub datahub register-structured-properties

# 4. Preview metadata updates
dhub datahub update-column-metadata examples/column_metadata_example.yaml --dry-run

# 5. Apply metadata updates
dhub datahub update-column-metadata examples/column_metadata_example.yaml

# 6. View results in terminal
dhub datahub list-tables --database loans_db --with-columns

# 7. Export to YAML
dhub datahub list-tables --database loans_db --with-columns --yaml > loans_with_metadata.yaml

# 8. View in DataHub UI
open http://localhost:9002
```

## Tips and Best Practices

### 1. Use Dry Run First

Always preview changes with `--dry-run` before applying:

```bash
dhub datahub update-column-metadata metadata.yaml --dry-run
```

### 2. Document Cross-Database Relationships

Use the full qualified name for cross-database FKs:

```yaml
structured_properties:
  fk_target_table: "database_name.schema_name.table_name"
  fk_target_column: "column_name"
  fk_cross_database: "true"
```

### 3. Add Meaningful Descriptions

Combine descriptions with structured properties:

```yaml
- name: customer_id
  description: "References the master customer record in accounts_db"
  structured_properties:
    fk_target_table: "accounts_db.public.customers"
```

### 4. Organize by Domain

Create separate YAML files for different business domains:

```
metadata/
  ├── loans_metadata.yaml
  ├── accounts_metadata.yaml
  ├── customer_metadata.yaml
  └── compliance_metadata.yaml
```

### 5. Version Control

Keep your metadata YAML files in version control to track changes over time.

## Troubleshooting

### Error: "Structured property not found"

**Problem:** The structured property hasn't been registered in DataHub.

**Solution:** Run `dhub datahub register-structured-properties` first.

### Error: "Dataset not found"

**Problem:** The table hasn't been ingested into DataHub yet.

**Solution:** Run `dhub datahub ingest-run --database <database_name>` first.

### Error: "Invalid property value"

**Problem:** The property value doesn't match the allowed values (e.g., "true" vs "false" for fk_cross_database).

**Solution:** Check the allowed values in `databases/datahub/structured-properties.yaml`.

## Advanced: Creating Custom Structured Properties

To add your own structured properties:

1. Edit `databases/datahub/structured-properties.yaml`:

```yaml
- id: data_classification
  qualified_name: data_classification
  type: string
  cardinality: SINGLE
  display_name: Data Classification
  description: "Sensitivity classification (public, internal, confidential, restricted)"
  allowed_values:
    - value: "public"
      description: "Publicly available data"
    - value: "internal"
      description: "Internal use only"
    - value: "confidential"
      description: "Confidential data"
    - value: "restricted"
      description: "Highly restricted data"
  entity_types:
    - urn:li:entityType:datahub.schemaField
```

2. Register the new property:

```bash
dhub datahub register-structured-properties
```

3. Use it in your metadata YAML:

```yaml
columns:
  - name: ssn
    description: "Social Security Number"
    structured_properties:
      data_classification: "restricted"
```

## Next Steps

- View metadata in DataHub UI: http://localhost:9002
- Explore lineage visualization
- Set up data governance policies based on structured properties
- Create dashboards showing cross-database relationships

---

**Last Updated:** 2025-10-26
