Data Generation Requirements for Banking Database Demo
Overview
Create Python script to generate realistic fake data for 6 PostgreSQL databases with cross-database relationships. Target: 1000+ customers with varying product penetration rates.
Technical Stack

Library: Faker (primary), random, datetime
DB Driver: psycopg2
Python: 3.9+

Database Connection Configuration
accounts_db: localhost:5432
customer_db: localhost:5432
insurance_db: localhost:5432
employees_db: localhost:5432
loans_db: localhost:5432
compliance_db: localhost:5432

Credentials: configurable via env vars or config file
```

## Generation Order & Dependencies

### Phase 1: Foundation Data (No Dependencies)

#### 1.1 Employees (employees_db)
**Target**: 150 employees

**Requirements**:
- Generate departments first (10-12 departments: retail_banking, lending, insurance, compliance, operations, customer_service, risk, IT, HR, finance, audit, marketing)
- Create department heads (1 per department)
- Generate employees with realistic role distribution:
  - 40% customer_service representatives
  - 20% loan officers
  - 15% insurance agents
  - 10% compliance officers
  - 15% managers/specialists
- Manager hierarchy: 70% have managers, 30% are senior/independent
- Branch codes: 15-20 different branches
- Hire dates: distributed over last 10 years
- 5% terminated employees (with termination_date)
- Salary ranges by role (realistic USD amounts)

**Deliverables**: 
- List of employee_ids saved in memory for later reference
- Separate lists for: loan_officers, insurance_agents, compliance_officers

#### 1.2 Training Programs (employees_db)
**Target**: 20-30 programs

**Requirements**:
- Mix of: compliance, product, customer_service, technical, leadership
- Duration: 2-40 hours
- 30% offer certification

#### 1.3 Customers Master (accounts_db)
**Target**: 1200 customers

**Requirements**:
- Realistic names, emails, phones (use Faker)
- Age distribution: 18-85 years (bell curve centered at 35-50)
- Created_at: distributed over last 7 years
- Store customer_ids in memory for Phase 2

### Phase 2: Core Banking Products

#### 2.1 Customer Profiles (customer_db)
**Target**: All 1200 customers

**Requirements**:
- Mirror customer_id from accounts_db
- Segments distribution:
  - 60% retail
  - 25% premium
  - 10% corporate
  - 5% private_banking
- Customer status: 90% active, 7% dormant, 3% closed
- KYC status: 85% verified, 10% pending, 5% expired
- Risk rating: 70% low, 25% medium, 5% high
- Assigned agent: 80% have one (from employees)
- Onboarding dates match customers.created_at

#### 2.2 Accounts (accounts_db)
**Target**: 1500-1800 accounts

**Requirements**:
- 75% of customers have accounts (some customers in CRM but no accounts yet)
- 25% of account holders have multiple accounts
- Account types distribution:
  - 50% checking
  - 30% savings
  - 15% money_market
  - 5% other
- Account status: 92% active, 5% frozen, 3% closed
- Balance ranges:
  - checking: $50 - $25,000
  - savings: $100 - $100,000
  - money_market: $10,000 - $500,000
- Opened dates: align with customer created_at +/- random days
- Currency: 95% USD, 5% EUR/GBP/other
- Store account_ids and map to customer_ids

#### 2.3 Transactions (accounts_db)
**Target**: 15,000-20,000 transactions

**Requirements**:
- Per account: 5-50 transactions (vary by account age and type)
- Transaction types distribution:
  - 40% deposit
  - 30% withdrawal
  - 20% transfer
  - 10% payment/fee
- Transaction amounts:
  - deposit: $20 - $10,000
  - withdrawal: $20 - $5,000
  - transfer: $50 - $50,000
  - payment: $10 - $2,000
- Dates: distributed from account opened_date to present
- 15% have processed_by (employee_id)
- Calculate balance_after sequentially per account
- Transfers: 30% should have counterparty_account (another account_number)

#### 2.4 Account Relationships (accounts_db)
**Target**: 100-150 relationships

**Requirements**:
- Relationship types:
  - 60% joint_owner
  - 30% beneficiary
  - 10% authorized_user
- Only for accounts that exist
- No duplicate relationships

### Phase 3: Customer Engagement

#### 3.1 Interactions (customer_db)
**Target**: 3000-4000 interactions

**Requirements**:
- 60% of customers have interactions
- Per customer: 1-10 interactions
- Types distribution:
  - 35% call
  - 25% email
  - 20% branch_visit
  - 15% chat
  - 5% complaint
- Channels: phone, email, web, mobile_app, branch
- Duration: 2-60 minutes (NULL for email)
- 80% handled_by employee_id
- Outcomes: 70% resolved, 20% escalated, 10% follow_up_needed
- Dates: within customer lifetime

#### 3.2 Satisfaction Surveys (customer_db)
**Target**: 800-1000 surveys

**Requirements**:
- 40% of interactions get surveys
- NPS: bell curve 0-10 (mean ~7)
- Satisfaction: 1-5 (mean ~4)
- 30% have comments (generate short feedback text)
- Survey date = interaction date + 1-3 days

#### 3.3 Complaints (customer_db)
**Target**: 150-200 complaints

**Requirements**:
- 10-15% of customers file complaints
- Types: service (40%), fee (25%), product (20%), fraud (10%), other (5%)
- Status: 60% resolved, 25% investigating, 10% closed, 5% open
- Priority: 10% critical, 20% high, 50% medium, 20% low
- Resolution time: 1-240 hours (NULL if not resolved)
- 70% assigned_to employee

#### 3.4 Campaigns (customer_db)
**Target**: 15-20 campaigns

**Requirements**:
- Types: email, direct_mail, digital, cross_sell, retention
- Date ranges: last 2 years
- Target segments match customer segments

#### 3.5 Campaign Responses (customer_db)
**Target**: 2000-3000 responses

**Requirements**:
- 40-50% of customers respond to at least one campaign
- Response types: clicked (50%), opened (30%), unsubscribed (5%), purchased (15%)
- Converted: 20% of responses
- Response dates within campaign period

### Phase 4: Financial Products

#### 4.1 Loan Applications (loans_db)
**Target**: 400-500 applications

**Requirements**:
- 35% of customers apply for loans
- Types distribution:
  - 30% mortgage
  - 25% personal
  - 20% auto
  - 15% business
  - 10% education
- Requested amounts by type:
  - mortgage: $100K - $800K
  - personal: $5K - $50K
  - auto: $10K - $80K
  - business: $20K - $500K
  - education: $5K - $100K
- Status: 65% approved, 25% rejected, 7% pending, 3% withdrawn
- Officer_id from loan officers list
- Application dates: last 3 years
- Store approved application_ids for loan creation

#### 4.2 Loans (loans_db)
**Target**: 260-325 loans (approved applications)

**Requirements**:
- Create only for approved applications
- Approved amount: 80-100% of requested
- Interest rates by type and risk:
  - mortgage: 3.5-7.5%
  - personal: 6-18%
  - auto: 4-12%
  - business: 5-15%
  - education: 4-10%
- Terms by type:
  - mortgage: 180-360 months
  - personal: 12-60 months
  - auto: 24-72 months
  - business: 12-120 months
  - education: 60-180 months
- Disbursement dates: application decision_date + 5-30 days
- Status: 85% active, 10% paid_off, 5% defaulted
- Outstanding balance: 20-95% of principal (for active)
- Default status: 3-5% of active loans
- Link to customer accounts where possible (70%)

#### 4.3 Collateral (loans_db)
**Target**: 200-250 records

**Requirements**:
- 60% of mortgages have property collateral
- 80% of auto loans have vehicle collateral
- 40% of business loans have equipment/property
- Appraised value: 110-150% of loan principal
- LTV ratio: calculate from loan amount / appraised value
- Appraisal dates: near disbursement date

#### 4.4 Repayment Schedule (loans_db)
**Target**: Auto-generate for each loan

**Requirements**:
- Create installments = term_months per loan
- Calculate amortization schedule (principal + interest)
- Due dates: monthly from disbursement
- Payment status for past due dates:
  - 90% paid
  - 5% late
  - 3% pending
  - 2% missed
- Fill payment_date for paid/late status

#### 4.5 Loan Guarantors (loans_db)
**Target**: 80-120 records

**Requirements**:
- 25-30% of personal/business loans have guarantors
- Guarantor names: use Faker
- Relationships: family (60%), business_partner (30%), friend (10%)
- Guarantee amount: 50-100% of loan principal

#### 4.6 Risk Assessments (loans_db)
**Target**: All applications + 30% of active loans

**Requirements**:
- One per application (before decision)
- Periodic assessments for 30% of active loans
- Risk score: 300-850 (FICO-like)
- PD probability: 0.01-0.25 (higher for rejected/defaulted)
- Credit grades: AAA(5%), AA(10%), A(25%), BBB(30%), BB(20%), B(8%), CCC(2%)
- Assessed_by: mix of employee_ids and 'SYSTEM'

### Phase 5: Insurance Products

#### 5.1 Policies (insurance_db)
**Target**: 300-400 policies

**Requirements**:
- 25-30% of customers have insurance
- 15% of policy holders have multiple policies
- Types distribution:
  - 35% life
  - 25% property
  - 20% vehicle
  - 15% health
  - 5% travel
- Coverage amounts by type:
  - life: $50K - $2M
  - property: $100K - $5M
  - vehicle: $10K - $150K
  - health: $50K - $1M
  - travel: $10K - $100K
- Premium amounts: 0.5-3% of coverage (annual equivalent)
- Frequency: 50% annual, 30% quarterly, 20% monthly
- Status: 88% active, 7% lapsed, 5% cancelled
- 70% linked to customer accounts
- Agent_id from insurance agents list
- Start dates: last 5 years

#### 5.2 Beneficiaries (insurance_db)
**Target**: 400-600 records

**Requirements**:
- Life insurance: 1-3 beneficiaries per policy
- Other types: 20% have beneficiaries
- Relationships: spouse (50%), child (30%), parent (10%), other (10%)
- Percentages sum to 100 per policy

#### 5.3 Claims (insurance_db)
**Target**: 200-300 claims

**Requirements**:
- 40-50% of policies have claims
- Claim types match policy types
- Claim amounts: 10-100% of coverage (weighted toward lower)
- Status: 50% paid, 25% approved, 15% under_review, 10% rejected
- Settlement dates for paid claims
- Processed_by from employees

#### 5.4 Premium Payments (insurance_db)
**Target**: 2000-3000 payments

**Requirements**:
- Generate payment history based on frequency and start_date
- Payment methods: 60% auto_debit, 20% online, 15% check, 5% wire
- 70% from linked accounts
- Status: 95% completed, 3% pending, 2% failed

#### 5.5 Policy Events (insurance_db)
**Target**: 300-500 events

**Requirements**:
- Types: renewal (40%), modification (30%), cancellation (20%), reinstatement (10%)
- 50% have performed_by employee

### Phase 6: Compliance & Risk

#### 6.1 KYC Records (compliance_db)
**Target**: All 1200 customers

**Requirements**:
- One record per customer
- Status matches customer_profiles.kyc_status
- Document types: passport (50%), drivers_license (35%), national_id (15%)
- Generate realistic document numbers
- Expiry dates: 1-10 years from verification
- Next review: 1-3 years after verification
- Verified_by from compliance officers
- Verification dates align with onboarding

#### 6.2 AML Checks (compliance_db)
**Target**: 3000-4000 checks

**Requirements**:
- All customers: initial check
- 50% of customers: periodic checks
- All high-value transactions (>$10K): transaction monitoring
- Types: watchlist (40%), sanctions (30%), pep_screening (20%), transaction_monitoring (10%)
- AML flag: 5% flagged
- Risk levels for flagged: 60% medium, 35% low, 5% high
- Reviewed_by for flagged checks

#### 6.3 Suspicious Activity Reports (compliance_db)
**Target**: 30-50 SARs

**Requirements**:
- Triggered by flagged AML checks or unusual transactions
- Activity types: structuring (40%), unusual_pattern (35%), high_risk_country (25%)
- Status: 40% filed, 30% under_review, 20% closed, 10% draft
- Amount involved: $5K - $500K
- Regulatory tier: tier1 (60%), tier2 (30%), tier3 (10%)
- Filed_by from compliance officers

#### 6.4 Regulatory Reports (compliance_db)
**Target**: 20-30 reports

**Requirements**:
- Types: capital_adequacy, liquidity, stress_test, quarterly_filing
- Quarterly reports for last 2 years
- Status: 80% submitted, 15% accepted, 5% pending
- Prepared_by and approved_by from senior employees

#### 6.5 Audit Trails (compliance_db)
**Target**: 5000-8000 records

**Requirements**:
- Sample critical actions across all databases
- Entity types: account, customer, loan, transaction, policy
- Actions: 50% update, 30% create, 15% view, 5% delete
- Random employee_ids as performed_by
- Timestamps distributed across all operational dates
- 30% have old_value/new_value (JSON format)
- Random IP addresses

#### 6.6 Compliance Rules (compliance_db)
**Target**: 15-20 rules

**Requirements**:
- Types: transaction_limit, velocity_check, geographic_restriction, amount_threshold
- Realistic thresholds (e.g., $10K for CTR, 5 transactions/day)
- 90% active, 10% inactive

#### 6.7 Rule Violations (compliance_db)
**Target**: 200-300 violations

**Requirements**:
- Reference existing rules
- Entity types: transaction (60%), account (25%), customer (15%)
- Severity: 10% critical, 25% high, 45% medium, 20% low
- Status: 60% resolved, 20% investigating, 15% false_positive, 5% open
- Resolution time: resolved violations only
- Resolved_by from compliance officers

## Cross-Database Relationship Requirements

**Critical**: Maintain referential integrity via shared IDs:

1. **customer_id**: Must match across accounts_db.customers, customer_db.customer_profiles, loans_db, insurance_db, compliance_db
2. **employee_id**: Appears in multiple DBs as agent_id, officer_id, processed_by, handled_by, etc.
3. **account_id**: Referenced in loans, insurance (linked_account_id), transactions
4. **transaction_id**: Referenced in compliance_db.aml_checks

## Implementation Requirements

### Script Structure
```
data_generator/
├── config.py          # DB connections, constants
├── generators/
│   ├── employees.py
│   ├── customers.py
│   ├── accounts.py
│   ├── crm.py
│   ├── loans.py
│   ├── insurance.py
│   └── compliance.py
├── utils.py           # Shared utilities, ID management
└── main.py           # Orchestrator
Key Features

ID Management: Store generated IDs in dictionaries for FK references
Bulk Inserts: Use executemany() with batches of 500-1000 records
Progress Tracking: Print progress for each phase
Data Consistency: Ensure dates, amounts, statuses are logically consistent
Configurability: Easy to adjust quantities via constants
Error Handling: Graceful handling of constraint violations
Idempotency: Can re-run (consider truncate option)

Performance Targets

Complete generation in < 5 minutes
Memory usage < 1GB

Validation Requirements
After generation, script should output:

Record counts per table
Sample FK validation queries
Data quality checks (e.g., no future dates, valid balances)

Output

Populated databases ready for DataHub ingestion
Generation log file with statistics
Optional: CSV exports of generated data for backup