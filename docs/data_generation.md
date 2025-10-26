# Data Generation Guide

## Overview

Generate realistic demo data across 6 PostgreSQL databases with proper cross-database relationships for DataHub demonstrations.

## Quick Start

```bash
# Generate demo data (default scale 1.0)
dhub seed all

# Small demo (fast)
dhub seed all --scale 0.1

# Large enterprise dataset
dhub seed all --scale 5.0

# Check current data
dhub seed status

# Clear all data
dhub seed clear --confirm
```

## What's Generated

### Phase 1-2 (Implemented)

| Database | Tables | Description |
|----------|--------|-------------|
| **employees_db** | departments, employees, training_programs | HR data with roles & hierarchy |
| **customer_db** | customer_profiles | CRM profiles with segments & KYC status |
| **accounts_db** | customers, accounts, account_relationships, transactions | Customer master + banking accounts + linked accounts + transaction history |

### Current Capabilities

- ✅ 12 Departments (fixed organizational structure)
- ✅ Employees with roles: Loan Officers, Insurance Agents, Compliance Officers, etc.
- ✅ Customers with realistic demographics (age 18-85, bell curve distribution)
- ✅ Customer Profiles with segments (retail 60%, premium 25%, corporate 10%, private 5%)
- ✅ Bank Accounts with types (checking 50%, savings 30%, money market 15%, CD 5%)
- ✅ Account Relationships (20% of accounts have 1 link, 5% have 2 links)
- ✅ Transactions (10-20x account count, 70% spending, 30% income)
- ✅ Cross-database relationships (customer_id, employee_id, account_id) maintained

### Not Yet Implemented

Phases 3-6 are planned but not yet implemented:
- Loan Applications, Loans, Collateral
- Insurance Policies, Claims, Beneficiaries
- Interactions, Campaigns, Complaints
- KYC Records, AML Checks, Audit Trails

## Scalability

### Scale Factor Parameter

Controls dataset size while maintaining data quality and relationships.

```bash
--scale <factor>    # Multiplier for dataset sizes (default: 1.0)
```

### Scale Examples

| Factor | Employees | Customers | Accounts | Relationships | Transactions | Use Case |
|--------|-----------|-----------|----------|---------------|--------------|----------|
| 0.05 | 7 | 60 | ~55 | ~14 | ~700 | Quick test |
| 0.1 | 15 | 120 | ~100 | ~25 | ~1,350 | Development |
| 0.5 | 75 | 600 | ~550 | ~140 | ~7,000 | Medium demo |
| **1.0** | **150** | **1,200** | **~1,100** | **~275** | **~14,000** | **Base (requirements)** |
| 5.0 | 750 | 6,000 | ~5,500 | ~1,400 | ~70,000 | Enterprise |
| 10.0 | 1,500 | 12,000 | ~11,000 | ~2,750 | ~140,000 | Very large |

### Fixed vs Scalable

**Fixed Size** (Don't scale):
- Departments (12)
- Training Programs (16-20)
- Branch Codes (15-20)

**Scalable** (Multiply by scale factor):
- Employees (base: 150)
- Customers (base: 1,200)
- Accounts (proportional to customers)

### Override Options

```bash
# Use scale but override customers
dhub seed all --scale 1.0 --customers 500

# Override both (ignores scale)
dhub seed all --customers 1000 --employees 100
```

## Data Relationships

All cross-database foreign keys are maintained:

1. **customer_id**: Links `accounts_db.customers` ↔ `customer_db.customer_profiles`
2. **employee_id**: Referenced as assigned_agent_id, manager_id, etc.
3. **account_id**: Links customers to their accounts (75% have accounts, 25% multiple)

### Verification

```bash
# Check employee-department relationships
dhub db query "SELECT e.first_name, e.role, d.department_name FROM employees e JOIN departments d ON e.department = d.department_name LIMIT 5" -d employees_db

# Check customer-account relationships
dhub db query "SELECT c.first_name, a.account_type, a.balance FROM customers c JOIN accounts a ON c.customer_id = a.customer_id LIMIT 5" -d accounts_db

# Check assigned agents
dhub db query "SELECT customer_id, full_name, assigned_agent_id FROM customer_profiles WHERE assigned_agent_id IS NOT NULL LIMIT 5" -d customer_db
```

## Usage Tips

1. **Start small**: Use `--scale 0.1` for quick tests
2. **Clear before regenerating**: Always run `dhub seed clear --confirm` first
3. **Check status**: Use `dhub seed status` to see record counts
4. **Verify data**: Use `dhub db tables` to see all populated tables

## Performance

| Scale | Total Records | Generation Time | Memory |
|-------|---------------|-----------------|--------|
| 0.1 | ~250 | ~8 sec | ~100 MB |
| 1.0 | ~2,500 | ~60 sec | ~500 MB |
| 5.0 | ~12,500 | ~5 min | ~2 GB |

## Data Quality

The generator ensures:
- ✅ Realistic distributions (segments, roles, account types)
- ✅ Valid foreign keys across databases
- ✅ Date consistency (hire_date < termination_date, etc.)
- ✅ Appropriate value ranges (balances, salaries)
- ✅ No duplicates on unique constraints
- ✅ Proper manager hierarchy (no circular references)

## Future Enhancements

When Phases 3-6 are implemented, total records at scale 1.0 will be:
- Current: ~2,500 records
- Full implementation: ~35,000+ records (with transactions, loans, insurance, compliance data)
