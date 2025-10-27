# Database Schema for AI Text-to-SQL Generation

This YAML export provides database schema metadata optimized for AI-powered SQL query generation.

## YAML Structure

```yaml
databases:
  <database_name>:
    schemas:
      <schema_name>:
        tables:
          <table_name>:
            description: "Human-readable table purpose"
            columns:
              - name: column_name
                type: COLUMN_TYPE
                nullable: true/false
                description: "What this column represents"
                foreign_key:          # Same-database foreign key
                  table: "database.schema.table"
                  column: "referenced_column"
                cross_db_reference:   # Cross-database reference
                  table: "other_database.schema.table"
                  column: "referenced_column"
                  description: "Why these tables are related"
                sample_values:        # Only for enums/categories (≤10 unique values)
                  - value1
                  - value2
```

## Key Fields

### Table Level
- **table name**: Use in FROM and JOIN clauses
- **description**: Explains what data the table contains and when to query it

### Column Level
- **name**: Exact column name for SQL
- **type**: Data type (VARCHAR, INTEGER, TIMESTAMP, etc.) for type casting and operators
- **nullable**: Whether NULL values are allowed (use `IS NULL` / `IS NOT NULL` when needed)
- **description**: Semantic meaning - **critical for mapping natural language to columns**

### Relationships

**foreign_key**: Standard SQL foreign key within the same database
```yaml
foreign_key:
  table: "database.schema.table"
  column: "column_name"
```
Use for: Same-database JOINs

**cross_db_reference**: Reference spanning multiple databases
```yaml
cross_db_reference:
  table: "other_database.schema.table"
  column: "column_name"
  description: "Semantic meaning of this relationship"
```
Use for: Cross-database JOINs (must use fully qualified table names)

**When both exist**: Prefer `cross_db_reference` for richer context

### Sample Values

Only present for low-cardinality columns (≤10 unique values):
- Status fields (`active`, `closed`, `pending`)
- Type fields (`savings`, `checking`, `money_market`)
- Category/enum fields

**Usage**: Use exact values from sample_values list in WHERE clauses. Don't invent values.

## SQL Generation Guidelines

1. **JOINs**: Use `foreign_key` and `cross_db_reference` to determine JOIN conditions
2. **Cross-database JOINs**: Always use fully qualified names (database.schema.table)
3. **Filtering**: Match sample_values exactly (case-sensitive)
4. **NULLs**: Check nullable flag, use `IS NULL` / `IS NOT NULL` appropriately
5. **Column selection**: Use descriptions to map natural language to columns
6. **Table selection**: Use table descriptions to identify relevant tables
