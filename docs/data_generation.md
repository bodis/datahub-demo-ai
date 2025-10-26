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

### Phase 1-3 (Implemented - 60% Complete)

| Database | Tables | Records @ Scale 1.0 |
|----------|--------|---------------------|
| **employees_db** | departments, employees, training_programs | ~180 |
| **customer_db** | customer_profiles, interactions, satisfaction_surveys, complaints, campaigns, campaign_responses | ~2,300 |
| **accounts_db** | customers, accounts, account_relationships, transactions | ~16,500 |

**Key Features:**
- ✅ **HR**: 12 departments, employees with roles (Loan Officers, Agents, etc.)
- ✅ **Customers**: Realistic demographics, segments (retail 60%, premium 25%, etc.)
- ✅ **Accounts**: Multiple types (checking 50%, savings 30%, etc.), 20%+5% have relationships
- ✅ **Transactions**: 10-20x accounts, 70% spending / 30% income, chronological
- ✅ **CRM**: 0-5 interactions/customer, 8% complaints, 10-15 campaigns, 5% respond
- ✅ **Satisfaction**: 30% of interactions surveyed, NPS & 1-5 star ratings

### Not Yet Implemented (Phases 4-6)

- **Loans**: Applications, approvals, collateral, payments
- **Insurance**: Policies, claims, beneficiaries, coverage
- **Compliance**: KYC records, AML checks, audit trails

## Scalability

### Scale Factor Parameter

Controls dataset size while maintaining data quality and relationships.

```bash
--scale <factor>    # Multiplier for dataset sizes (default: 1.0)
```

### Scale Examples

| Factor | Employees | Customers | Accounts | Transactions | Interactions | Total Records | Use Case |
|--------|-----------|-----------|----------|--------------|--------------|---------------|----------|
| 0.05 | 7 | 60 | ~55 | ~700 | ~100 | ~1,000 | Quick test |
| **0.1** | **15** | **120** | **~110** | **~1,400** | **~210** | **~2,000** | **Development** |
| 0.5 | 75 | 600 | ~550 | ~7,000 | ~1,000 | ~9,500 | Medium demo |
| 1.0 | 150 | 1,200 | ~1,100 | ~14,000 | ~2,000 | ~19,000 | Base |
| 5.0 | 750 | 6,000 | ~5,500 | ~70,000 | ~10,000 | ~92,000 | Enterprise |

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

## Data Relationships & Details

**Cross-database links maintained:**
- `customer_id`: Syncs accounts_db ↔ customer_db
- `employee_id`: Used in assigned_agent_id, handled_by, processed_by, etc.
- `account_id`: Links to transactions and relationships

### Key Generation Rules

**Accounts (accounts_db)**
- 75% of customers have accounts, 25% have multiple
- Account relationships: 20% have 1 link, 5% have 2 links
- Types: joint_owner, beneficiary, authorized_user, linked_savings

**Transactions (accounts_db)**
- Volume: 10-20x accounts (randomized)
- Spending (70%): withdrawals, payments, fees | Income (30%): deposits, salary, interest
- Amounts: Spending capped at 30% balance, salary $1k-8k
- 30% manual / 70% automated, chronologically sorted

**Interactions (customer_db)**
- Each customer: 0-5 interactions (weighted: 20% none, 25% one, decreasing)
- Channels: phone (30%), email (25%), web (20%), mobile_app (15%), branch (10%)
- 80% handled by employees, duration varies by channel

**Complaints (customer_db)**
- 8% of customers file complaints
- Types: service (35%), fee (25%), product (20%), fraud (10%)
- Status: 60% resolved, 20% investigating, 15% closed, 5% open

**Campaigns (customer_db)**
- Fixed 10-15 campaigns per generation
- Types: email (40%), digital (30%), cross_sell (20%), direct_mail (10%)
- 5% of customers respond (1-2 campaigns each)

**Satisfaction Surveys (customer_db)**
- 30% of interactions get surveyed
- NPS: 0-10 (weighted positive), Satisfaction: 1-5 stars (correlated)
- 50% leave comments

### Quick Verification Queries

```bash
# Transaction distribution
dhub db query "SELECT transaction_type, COUNT(*) FROM transactions GROUP BY transaction_type" -d accounts_db

# Interaction channels
dhub db query "SELECT channel, COUNT(*) FROM interactions GROUP BY channel" -d customer_db

# Satisfaction metrics
dhub db query "SELECT ROUND(AVG(nps_score), 2) as avg_nps, ROUND(AVG(satisfaction_rating), 2) as avg_rating FROM satisfaction_surveys" -d customer_db

# Campaign performance
dhub db query "SELECT response_type, COUNT(*), SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions FROM campaign_responses GROUP BY response_type" -d customer_db
```

## Usage Tips

1. **Start small**: Use `--scale 0.1` for quick tests
2. **Clear before regenerating**: Always run `dhub seed clear --confirm` first
3. **Check status**: Use `dhub seed status` to see record counts
4. **Verify data**: Use `dhub db tables` to see all populated tables

## Performance

| Scale | Total Records | Time | Notes |
|-------|---------------|------|-------|
| 0.1 | ~2,000 | ~12s | Quick dev testing |
| 1.0 | ~19,000 | ~2min | Base requirements |
| 5.0 | ~95,000 | ~10min | Large dataset |

Transactions inserted in batches of 1,000 for efficiency.

## Data Quality Guarantees

- ✅ Realistic distributions & weighted random selections
- ✅ Valid foreign keys across all databases
- ✅ Date/time consistency (no future dates, proper sequences)
- ✅ Appropriate value ranges (balances, salaries, NPS scores)
- ✅ No duplicates on unique constraints
- ✅ Proper hierarchies (managers, relationships)
- ✅ Chronological ordering where applicable

## Roadmap

**Current (Phase 1-3):** ~19,000 records @ scale 1.0 (~60% complete)

**Future (Phases 4-6):**
- Loans: applications, approvals, payments, collateral
- Insurance: policies, claims, beneficiaries
- Compliance: KYC, AML checks, audit trails

**Target:** ~50,000+ records @ scale 1.0 when fully implemented
