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

### Phase 1-3: Foundation & Banking (Implemented)

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

### Phase 4: Employee Development (Implemented)

| Database | Tables | Records @ Scale 1.0 |
|----------|--------|---------------------|
| **employees_db** | employee_training, performance_reviews, employee_assignments | ~450 |

**Key Features:**
- ✅ **Training Enrollments**: 2-4 programs per employee, 80% completed
- ✅ **Performance Reviews**: 1-3 annual reviews per employee, 5-point rating scale
- ✅ **Employee Assignments**: 60% customers assigned, branch coverage tracking

### Phase 5: Loan Products (Implemented)

| Database | Tables | Records @ Scale 1.0 |
|----------|--------|---------------------|
| **loans_db** | loan_applications, loans, collateral, repayment_schedule, loan_guarantors, risk_assessments | ~40,000+ |

**Key Features:**
- ✅ **Loan Applications**: ~35% of customers apply, 5 loan types (mortgage, personal, auto, business, education)
- ✅ **Loans**: 65% approval rate, realistic amortization schedules
- ✅ **Collateral**: 80% of secured loans (property, vehicles, equipment)
- ✅ **Repayment Schedules**: Complete monthly installment plans for all loans
- ✅ **Guarantors**: 25% of loans have 1-2 guarantors
- ✅ **Risk Assessments**: Credit scores, PD probability, credit grades (AAA-C)

### Not Yet Implemented (Phases 6-7)

- **Insurance**: Policies, claims, beneficiaries, coverage
- **Compliance**: KYC records, AML checks, audit trails

## Scalability

### Scale Factor Parameter

Controls dataset size while maintaining data quality and relationships.

```bash
--scale <factor>    # Multiplier for dataset sizes (default: 1.0)
```

### Scale Examples

| Factor | Employees | Customers | Accounts | Loans | Total Records | Use Case |
|--------|-----------|-----------|----------|-------|---------------|----------|
| 0.05 | 7 | 60 | ~55 | ~15 | ~2,500 | Quick test |
| **0.1** | **15** | **120** | **~110** | **~30** | **~5,000** | **Development** |
| 0.5 | 75 | 600 | ~550 | ~160 | ~30,000 | Medium demo |
| 1.0 | 150 | 1,200 | ~1,100 | ~270 | ~60,000 | Base |
| 5.0 | 750 | 6,000 | ~5,500 | ~1,350 | ~300,000 | Enterprise |

**Notes:**
- Total Records include all tables: employees, customers, accounts, transactions, interactions, loans, repayment schedules, etc.
- Repayment schedules dominate loan record counts (60-360 entries per loan depending on term)

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
- `customer_id`: Syncs accounts_db ↔ customer_db ↔ loans_db
- `employee_id`: Used in assigned_agent_id, handled_by, processed_by, officer_id, approved_by, assessed_by, reviewer_id
- `account_id`: Links to transactions, relationships, and loan disbursements (linked_account_id)
- `application_id`: Links loan applications to loans
- `loan_id`: Links loans to collateral, repayment schedules, guarantors, and risk assessments
- `program_id`: Links training programs to employee training records

### Key Generation Rules

**Employee Training (employees_db)**
- Each employee enrolls in 2-4 training programs
- Status distribution: 80% completed, 15% in_progress, 5% enrolled
- Completed trainings have scores (65-100)
- Enrollment dates within last 2 years

**Performance Reviews (employees_db)**
- Active employees have 1-3 reviews (annual cadence)
- Rating distribution: 1 (2%), 2 (8%), 3 (35%), 4 (40%), 5 (15%)
- Reviewers are other employees (typically managers)
- Goals met: 60-100%

**Employee Assignments (employees_db)**
- 60% of customers assigned to employees (customer_portfolio)
- Customer service reps, loan officers, insurance agents get assignments
- Branch coverage assignments: 10-20 per generation
- 85% ongoing, 15% ended

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

**Loan Applications (loans_db)**
- ~35% of customers apply for loans
- 20% of applicants apply multiple times
- Loan types: mortgage (35%), personal (30%), auto (20%), business (10%), education (5%)
- Status: approved (65%), rejected (20%), pending (10%), withdrawn (5%)
- Assigned to loan officers from employees_db
- Decision made 1-30 days after application

**Loans (loans_db)**
- Generated from approved applications
- Realistic interest rates and terms by loan type:
  - Mortgage: 3.25-6.75%, 15-30 years
  - Personal: 5.99-17.99%, 1-5 years
  - Auto: 3.99-8.99%, 3-6 years
  - Business: 4.99-12.99%, 3-10 years
  - Education: 4.25-8.75%, 5-15 years
- Status: active (75%), paid_off (20%), defaulted (3%), restructured (2%)
- Outstanding balance calculated based on time elapsed
- Linked to customer accounts for disbursement/repayment

**Collateral (loans_db)**
- 80% of secured loans (mortgage, auto, business) have collateral
- Appraised values: 110-150% of loan principal
- LTV (Loan-to-Value) ratios calculated automatically
- Types: property, real_estate, vehicle, equipment, inventory

**Repayment Schedules (loans_db)**
- Complete amortization schedule for each loan
- Monthly installments with principal and interest breakdown
- Payment status based on loan status:
  - Active loans: 95% paid on time
  - Defaulted loans: 50% missed payments
  - Paid-off loans: 100% paid
- Chronological tracking of actual payment dates

**Loan Guarantors (loans_db)**
- 25% of loans have guarantors
- 70% have 1 guarantor, 30% have 2
- Relationships: spouse, parent, sibling, business_partner, etc.
- Guarantee amounts: 50-100% of loan principal

**Risk Assessments (loans_db)**
- All applications assessed before decision
- 40% of active loans reassessed periodically
- Credit scores: 300-850 range (realistic distribution)
- Probability of Default (PD): 0.01-0.95 based on loan status
- Credit grades: AAA to C (correlated with risk scores)
- Assessed by compliance officers or risk analysts

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

# Loan applications by status
dhub db query "SELECT status, COUNT(*) FROM loan_applications GROUP BY status" -d loans_db

# Loan portfolio by type and status
dhub db query "SELECT loan_type, loan_status, COUNT(*), ROUND(AVG(principal_amount), 2) as avg_principal FROM loans GROUP BY loan_type, loan_status ORDER BY loan_type" -d loans_db

# Repayment performance
dhub db query "SELECT payment_status, COUNT(*), ROUND(SUM(total_amount), 2) as total_amount FROM repayment_schedule GROUP BY payment_status" -d loans_db

# Risk assessment summary
dhub db query "SELECT credit_grade, COUNT(*), ROUND(AVG(risk_score), 2) as avg_score, ROUND(AVG(pd_probability), 4) as avg_pd FROM risk_assessments GROUP BY credit_grade ORDER BY credit_grade" -d loans_db

# Employee training completion
dhub db query "SELECT status, COUNT(*), ROUND(AVG(score), 2) as avg_score FROM employee_training GROUP BY status" -d employees_db

# Performance review distribution
dhub db query "SELECT rating, COUNT(*), ROUND(AVG(goals_met), 2) as avg_goals_met FROM performance_reviews GROUP BY rating ORDER BY rating" -d employees_db
```

## Usage Tips

1. **Start small**: Use `--scale 0.1` for quick tests
2. **Clear before regenerating**: Always run `dhub seed clear --confirm` first
3. **Check status**: Use `dhub seed status` to see record counts
4. **Verify data**: Use `dhub db tables` to see all populated tables

## Performance

| Scale | Total Records | Time | Notes |
|-------|---------------|------|-------|
| 0.1 | ~5,000 | ~15s | Quick dev testing |
| 0.5 | ~30,000 | ~45s | Medium demo |
| 1.0 | ~60,000 | ~2min | Base requirements |
| 5.0 | ~300,000 | ~12min | Large dataset |

**Performance optimizations:**
- Transactions and repayment schedules inserted in batches of 1,000 for efficiency
- Unique value generation with retry logic prevents constraint violations
- Phase-based generation with automatic retry on constraint errors

## Data Quality Guarantees

- ✅ Realistic distributions & weighted random selections
- ✅ Valid foreign keys across all databases
- ✅ Date/time consistency (no future dates, proper sequences)
- ✅ Appropriate value ranges (balances, salaries, NPS scores, interest rates)
- ✅ No duplicates on unique constraints (emails, phone numbers)
- ✅ Proper hierarchies (managers, relationships)
- ✅ Chronological ordering where applicable
- ✅ Realistic financial calculations (amortization schedules, LTV ratios)
- ✅ Automatic retry on constraint violations with generator reset

## Architecture

### Generator Classes

```
dhub/data_generators/
├── id_manager.py            # Cross-database ID tracking
├── unique_generator.py      # Unique value generation with deduplication
├── employees.py             # Employee, training, reviews, assignments
├── customers.py             # Customers, accounts, transactions, CRM
├── loans.py                 # Loans, applications, collateral, schedules
└── orchestrator.py          # Main coordinator with phases & retry logic
```

### Key Components

**UniqueValueGenerator** (new):
- Prevents duplicate emails, phone numbers
- Automatic retry with deduplication tracking
- Clears state on orchestrator retry

**EmployeeGenerator**:
- Extended with training, reviews, assignments methods
- Maintains role mapping for cross-references

**LoanGenerator** (new):
- Complete loan lifecycle: application → approval → disbursement → repayment
- Realistic amortization calculations
- Risk assessment integration

**DataOrchestrator**:
- 5-phase generation pipeline
- Retry logic with automatic rollback on constraint errors
- Cross-database relationship management

## Roadmap

**Current (Phases 1-5):** ~60,000 records @ scale 1.0 (~85% complete)

**Implemented:**
- ✅ Phase 1-3: Foundation (employees, customers, accounts, CRM)
- ✅ Phase 4: Employee Development (training, reviews, assignments)
- ✅ Phase 5: Loan Products (applications, loans, collateral, schedules, guarantors, risk)

**Future (Phases 6-7):**
- ⬜ Phase 6: Insurance (policies, claims, beneficiaries, coverage)
- ⬜ Phase 7: Compliance (KYC records, AML checks, audit trails, SARs)

**Target:** ~100,000 records @ scale 1.0 when fully implemented
