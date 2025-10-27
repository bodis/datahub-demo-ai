# YAML Schema Export - Developer Guide

Complete guide for generating and using YAML schema exports from DataHub.

## Table of Contents
- [Generating Exports](#generating-exports)
- [Export Formats](#export-formats)
- [Minified Format Details](#minified-format-details)
- [Best Practices for AI Text-to-SQL](#best-practices-for-ai-text-to-sql)
- [Complete Examples](#complete-examples)

## Generating Exports

### Basic Commands

```bash
# Export all databases (full format)
dhub datahub list-tables --with-columns --yaml > schema.yaml

# Export all databases (minified for AI)
dhub datahub list-tables --yaml --minified > schema_for_ai.yaml

# Export specific database (minified)
dhub datahub list-tables --database employees_db --yaml --minified > employees_schema.yaml

# Export without column details (table list only)
dhub datahub list-tables --yaml > tables_only.yaml
```

### Command Options

- `--database <name>`: Filter by specific database
- `--with-columns`: Include column details, relationships, and statistics
- `--yaml`: Output in YAML format (vs. table display)
- `--minified`: Use AI-optimized format (requires `--yaml`, auto-enables `--with-columns`)

## Export Formats

### Full Format

Includes all metadata from DataHub:

```yaml
databases:
  accounts_db:
    schemas:
      public:
        tables:
          accounts:
            platform: postgres
            environment: PROD
            urn: urn:li:dataset:(urn:li:dataPlatform:postgres,accounts_db.public.accounts,PROD)
            description: "Bank accounts owned by customers"
            row_count: 1129
            column_count: 10
            columns:
              - name: account_id
                type: VARCHAR(50)
                nullable: false
                description: "System-generated unique identifier"
                stats:
                  unique_count: 1129
                  unique_proportion: 1.0
                  null_count: 0
                  null_proportion: 0.0
                  sample_values:
                    - ACC-536BF5BDB958
                    - ACC-162378CC0F49
```

**Use for**: Complete metadata analysis, documentation, DataHub debugging

### Minified Format

Optimized for AI text-to-SQL generation:

```yaml
databases:
  accounts_db:
    schemas:
      public:
        tables:
          accounts:
            description: "Bank accounts owned by customers"
            columns:
              - name: account_id
                type: VARCHAR(50)
                nullable: false
                description: "System-generated unique identifier"
              - name: account_type
                type: VARCHAR(50)
                nullable: false
                description: "Type of account"
                sample_values:
                  - savings
                  - checking
                  - money_market
                  - cd
```

**Use for**: AI/LLM text-to-SQL generation, token-limited contexts

## Minified Format Details

### What's Included

✅ **Always Included**:
- Database, schema, and table names
- Table descriptions
- Column names, types, nullable flags
- Column descriptions
- Foreign key relationships
- Cross-database references

✅ **Conditionally Included**:
- Sample values (only for columns with ≤10 unique values)

### What's Excluded

❌ **Removed for Token Efficiency**:
- URNs (DataHub internal identifiers)
- Platform and environment metadata
- Row counts and column counts
- Tags and properties
- Detailed statistics (min, max, mean, median, stdev)
- Unique counts and null proportions
- Sample values for high-cardinality columns (>10 unique values)

### Cross-Database Reference Transformation

The minified format transforms structured properties into a cleaner format:

**Source (DataHub structured properties)**:
```yaml
structured_properties:
  fk_target_table: "loans_db.public.loans"
  fk_target_column: "customer_id"
  fk_cross_database: "true"
  fk_relationship_description: "Links customer to their loan records"
```

**Output (minified format)**:
```yaml
cross_db_reference:
  table: "loans_db.public.loans"
  column: "customer_id"
  description: "Links customer to their loan records"
```

## Best Practices for AI Text-to-SQL

### 1. Understanding Table Relationships

**Schema**:
```yaml
tables:
  accounts:
    columns:
      - name: customer_id
        type: VARCHAR(50)
        foreign_key:
          table: "accounts_db.public.customers"
          column: "customer_id"
```

**Natural Language**: "Show me all accounts for customer John Doe"

**SQL Generation Logic**:
1. Identify tables: `customers` (has name) and `accounts` (has account data)
2. Use foreign key to JOIN: `accounts.customer_id = customers.customer_id`
3. Filter: `WHERE customers.first_name = 'John' AND customers.last_name = 'Doe'`

**Generated SQL**:
```sql
SELECT a.*
FROM accounts_db.public.accounts a
JOIN accounts_db.public.customers c ON a.customer_id = c.customer_id
WHERE c.first_name = 'John' AND c.last_name = 'Doe'
```

### 2. Using Sample Values for Filtering

**Schema**:
```yaml
columns:
  - name: account_status
    type: VARCHAR(20)
    nullable: true
    description: "Current operational status: active, frozen, closed"
    sample_values:
      - active
      - frozen
      - closed
```

**Natural Language**: "Show me all active accounts"

**Correct SQL**:
```sql
WHERE account_status = 'active'
```

**Incorrect** (don't invent values):
```sql
WHERE account_status = 'open'  -- ❌ Not in sample_values
```

### 3. Handling NULL Values

**Schema**:
```yaml
columns:
  - name: closed_date
    type: DATE
    nullable: true
    description: "Date when the account was closed, NULL if still active"
```

**Natural Language**: "Show me all open accounts"

**SQL Generation**: Recognize NULL as "not closed":
```sql
WHERE closed_date IS NULL
```

### 4. Cross-Database Queries

**Schema**:
```yaml
columns:
  - name: customer_id
    type: VARCHAR(50)
    description: "Reference to customer who owns this loan"
    cross_db_reference:
      table: "accounts_db.public.customers"
      column: "customer_id"
      description: "Links loan to customer account holder in accounts database"
```

**Natural Language**: "Show me all loans for customers in California"

**SQL Generation**: Use fully qualified table names:
```sql
SELECT
    l.loan_id,
    l.amount,
    c.state
FROM loans_db.public.loans l
JOIN accounts_db.public.customers c
  ON l.customer_id = c.customer_id
WHERE c.state = 'CA'
```

### 5. Leveraging Column Descriptions

**Schema**:
```yaml
columns:
  - name: balance
    type: NUMERIC(15, 2)
    description: "Current account balance in account currency"
```

**Natural Language**: "Find customers with over $10,000"

**SQL Generation**: Map "$10,000" to `balance` column:
```sql
SELECT *
FROM accounts_db.public.accounts
WHERE balance > 10000
```

## Complete Examples

### Example 1: Simple Same-Database Query

**Schema**:
```yaml
databases:
  accounts_db:
    schemas:
      public:
        tables:
          accounts:
            description: "Bank accounts owned by customers"
            columns:
              - name: account_id
                type: VARCHAR(50)
                nullable: false
              - name: customer_id
                type: VARCHAR(50)
                nullable: false
                foreign_key:
                  table: "accounts_db.public.customers"
                  column: "customer_id"
              - name: account_type
                type: VARCHAR(50)
                description: "Type of account"
                sample_values:
                  - savings
                  - checking
                  - money_market
                  - cd
              - name: balance
                type: NUMERIC(15, 2)
                description: "Current account balance"
          customers:
            description: "Customer master data"
            columns:
              - name: customer_id
                type: VARCHAR(50)
                nullable: false
              - name: first_name
                type: VARCHAR(100)
              - name: last_name
                type: VARCHAR(100)
```

**Natural Language**: "Show me all savings accounts with balance over $5000 for customers named Smith"

**AI Reasoning**:
1. **Tables**: `accounts` (has account_type and balance), `customers` (has last_name)
2. **Join**: `accounts.customer_id` → `customers.customer_id` (foreign key)
3. **Filters**:
   - "savings accounts" → `account_type = 'savings'` (from sample_values)
   - "balance over $5000" → `balance > 5000`
   - "named Smith" → `last_name = 'Smith'`

**Generated SQL**:
```sql
SELECT
    c.first_name,
    c.last_name,
    a.account_id,
    a.account_type,
    a.balance
FROM accounts_db.public.accounts a
JOIN accounts_db.public.customers c ON a.customer_id = c.customer_id
WHERE a.account_type = 'savings'
  AND a.balance > 5000
  AND c.last_name = 'Smith'
```

### Example 2: Cross-Database Query

**Schema**:
```yaml
databases:
  loans_db:
    schemas:
      public:
        tables:
          loans:
            description: "Customer loans"
            columns:
              - name: loan_id
                type: VARCHAR(50)
                nullable: false
              - name: customer_id
                type: VARCHAR(50)
                nullable: false
                cross_db_reference:
                  table: "accounts_db.public.customers"
                  column: "customer_id"
                  description: "Links loan to customer in accounts database"
              - name: amount
                type: NUMERIC(15, 2)
                description: "Loan amount"
              - name: status
                type: VARCHAR(20)
                sample_values:
                  - active
                  - paid_off
                  - defaulted
  accounts_db:
    schemas:
      public:
        tables:
          customers:
            description: "Customer master data"
            columns:
              - name: customer_id
                type: VARCHAR(50)
              - name: first_name
                type: VARCHAR(100)
              - name: last_name
                type: VARCHAR(100)
              - name: state
                type: VARCHAR(2)
```

**Natural Language**: "Find all active loans for customers in California"

**AI Reasoning**:
1. **Tables**: `loans` (has status), `customers` (has state)
2. **Join**: `loans.customer_id` → `customers.customer_id` (cross_db_reference)
3. **Filters**:
   - "active loans" → `status = 'active'` (from sample_values)
   - "in California" → `state = 'CA'`

**Generated SQL**:
```sql
SELECT
    l.loan_id,
    l.amount,
    c.first_name,
    c.last_name,
    c.state
FROM loans_db.public.loans l
JOIN accounts_db.public.customers c
  ON l.customer_id = c.customer_id
WHERE l.status = 'active'
  AND c.state = 'CA'
```

## Token Efficiency

**Standard export**: ~35,000 tokens for a moderate database
**Minified export**: ~15,000 tokens (57% reduction)

This allows larger schemas to fit within AI context windows while preserving all information necessary for accurate SQL generation.

## Related Documentation

- **AI_SCHEMA_DESCRIPTOR.md**: Concise guide for LLMs (use alongside YAML export)
- **DataHub structured properties**: `databases/datahub/structured-properties.yaml`
