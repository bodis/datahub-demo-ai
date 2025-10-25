-- ============================================
-- Core Banking Database (accounts_db)
-- ============================================
CREATE DATABASE accounts_db;

CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    email VARCHAR(150),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_status VARCHAR(20) DEFAULT 'active',
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    opened_date DATE NOT NULL,
    closed_date DATE,
    branch_code VARCHAR(10),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    transaction_amount DECIMAL(15,2) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    balance_after DECIMAL(15,2),
    counterparty_account VARCHAR(20),
    processed_by VARCHAR(50),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE account_relationships (
    relationship_id SERIAL PRIMARY KEY,
    primary_account_id VARCHAR(50) NOT NULL,
    related_account_id VARCHAR(50) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (related_account_id) REFERENCES accounts(account_id)
);

CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

-- Table comments for accounts_db
COMMENT ON TABLE customers IS 'Core customer master data for account holders';
COMMENT ON TABLE accounts IS 'Bank accounts owned by customers';
COMMENT ON TABLE transactions IS 'Financial transactions on accounts';
COMMENT ON TABLE account_relationships IS 'Relationships between accounts such as joint ownership';

-- ============================================
-- accounts_db - Column Comments
-- ============================================

COMMENT ON COLUMN customers.customer_id IS 'Unique identifier for customer across all banking systems';
COMMENT ON COLUMN customers.first_name IS 'Customer first name as per official documents';
COMMENT ON COLUMN customers.last_name IS 'Customer last name as per official documents';
COMMENT ON COLUMN customers.date_of_birth IS 'Customer date of birth for age verification and compliance';
COMMENT ON COLUMN customers.email IS 'Primary email address for customer communication';
COMMENT ON COLUMN customers.phone IS 'Primary phone number for customer contact';
COMMENT ON COLUMN customers.created_at IS 'Timestamp when customer record was created in the system';

COMMENT ON COLUMN accounts.account_id IS 'System-generated unique identifier for the account';
COMMENT ON COLUMN accounts.account_number IS 'Customer-facing account number displayed on statements';
COMMENT ON COLUMN accounts.customer_id IS 'Reference to the customer who owns this account';
COMMENT ON COLUMN accounts.account_type IS 'Type of account: savings, checking, money_market';
COMMENT ON COLUMN accounts.account_status IS 'Current operational status: active, frozen, closed';
COMMENT ON COLUMN accounts.balance IS 'Current account balance in account currency';
COMMENT ON COLUMN accounts.currency IS 'ISO currency code for the account';
COMMENT ON COLUMN accounts.opened_date IS 'Date when the account was officially opened';
COMMENT ON COLUMN accounts.closed_date IS 'Date when the account was closed, NULL if still active';
COMMENT ON COLUMN accounts.branch_code IS 'Code of the branch where account was opened';

COMMENT ON COLUMN transactions.transaction_id IS 'Unique identifier for each transaction';
COMMENT ON COLUMN transactions.account_id IS 'Reference to the account involved in the transaction';
COMMENT ON COLUMN transactions.transaction_type IS 'Type: deposit, withdrawal, transfer, payment, fee';
COMMENT ON COLUMN transactions.transaction_amount IS 'Monetary amount of the transaction, positive for credits';
COMMENT ON COLUMN transactions.transaction_date IS 'Timestamp when transaction was processed';
COMMENT ON COLUMN transactions.description IS 'Human-readable description or memo for the transaction';
COMMENT ON COLUMN transactions.balance_after IS 'Account balance after this transaction was applied';
COMMENT ON COLUMN transactions.counterparty_account IS 'Account number of the other party in transfers';
COMMENT ON COLUMN transactions.processed_by IS 'Employee ID who processed the transaction, NULL for automated';

COMMENT ON COLUMN account_relationships.relationship_id IS 'Auto-incrementing identifier for the relationship';
COMMENT ON COLUMN account_relationships.primary_account_id IS 'The main account in the relationship';
COMMENT ON COLUMN account_relationships.related_account_id IS 'The related or secondary account';
COMMENT ON COLUMN account_relationships.relationship_type IS 'Type: joint_owner, beneficiary, authorized_user';
COMMENT ON COLUMN account_relationships.created_at IS 'When the relationship was established';
