-- ============================================
-- Insurance Database (insurance_db)
-- ============================================
CREATE DATABASE insurance_db;

CREATE TABLE policies (
    policy_id VARCHAR(50) PRIMARY KEY,
    policy_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    policy_type VARCHAR(50) NOT NULL,
    policy_status VARCHAR(20) DEFAULT 'active',
    coverage_amount DECIMAL(15,2) NOT NULL,
    premium_amount DECIMAL(10,2) NOT NULL,
    premium_frequency VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE,
    linked_account_id VARCHAR(50),
    agent_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE beneficiaries (
    beneficiary_id SERIAL PRIMARY KEY,
    policy_id VARCHAR(50) NOT NULL,
    beneficiary_name VARCHAR(200) NOT NULL,
    relationship VARCHAR(50),
    percentage INTEGER CHECK (percentage BETWEEN 0 AND 100),
    contact_info TEXT,
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE TABLE claims (
    claim_id VARCHAR(50) PRIMARY KEY,
    policy_id VARCHAR(50) NOT NULL,
    claim_number VARCHAR(30) UNIQUE NOT NULL,
    claim_type VARCHAR(100) NOT NULL,
    claim_amount DECIMAL(15,2) NOT NULL,
    claim_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'submitted',
    approved_amount DECIMAL(15,2),
    settlement_date DATE,
    description TEXT,
    processed_by VARCHAR(50),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE TABLE premium_payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    policy_id VARCHAR(50) NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    from_account_id VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'completed',
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE TABLE policy_events (
    event_id SERIAL PRIMARY KEY,
    policy_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    performed_by VARCHAR(50),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

CREATE INDEX idx_policies_customer ON policies(customer_id);
CREATE INDEX idx_claims_policy ON claims(policy_id);
CREATE INDEX idx_payments_policy ON premium_payments(policy_id);

-- Table comments for insurance_db
COMMENT ON TABLE policies IS 'Insurance policies sold to customers';
COMMENT ON TABLE beneficiaries IS 'Policy beneficiaries who receive benefits';
COMMENT ON TABLE claims IS 'Insurance claims filed by policyholders';
COMMENT ON TABLE premium_payments IS 'Premium payment transactions for policies';
COMMENT ON TABLE policy_events IS 'Lifecycle events for insurance policies';

-- ============================================
-- insurance_db - Column Comments
-- ============================================

COMMENT ON COLUMN policies.policy_id IS 'System-generated unique policy identifier';
COMMENT ON COLUMN policies.policy_number IS 'Customer-facing policy number';
COMMENT ON COLUMN policies.customer_id IS 'Customer who owns the policy';
COMMENT ON COLUMN policies.policy_type IS 'Type: life, property, vehicle, health, travel';
COMMENT ON COLUMN policies.policy_status IS 'Status: active, lapsed, cancelled, matured';
COMMENT ON COLUMN policies.coverage_amount IS 'Maximum benefit payable under policy';
COMMENT ON COLUMN policies.premium_amount IS 'Regular premium payment amount';
COMMENT ON COLUMN policies.premium_frequency IS 'Payment frequency: monthly, quarterly, annual';
COMMENT ON COLUMN policies.start_date IS 'Policy coverage start date';
COMMENT ON COLUMN policies.end_date IS 'Policy expiration or maturity date';
COMMENT ON COLUMN policies.linked_account_id IS 'Bank account used for premium payments';
COMMENT ON COLUMN policies.agent_id IS 'Employee who sold the policy';
COMMENT ON COLUMN policies.created_at IS 'Record creation timestamp';

COMMENT ON COLUMN beneficiaries.beneficiary_id IS 'Auto-incrementing beneficiary identifier';
COMMENT ON COLUMN beneficiaries.policy_id IS 'Policy to which beneficiary is linked';
COMMENT ON COLUMN beneficiaries.beneficiary_name IS 'Full name of the beneficiary';
COMMENT ON COLUMN beneficiaries.relationship IS 'Relationship to policyholder: spouse, child, parent';
COMMENT ON COLUMN beneficiaries.percentage IS 'Percentage of benefit allocated to this beneficiary';
COMMENT ON COLUMN beneficiaries.contact_info IS 'Contact information for the beneficiary';

COMMENT ON COLUMN claims.claim_id IS 'Unique claim identifier';
COMMENT ON COLUMN claims.policy_id IS 'Policy under which claim is filed';
COMMENT ON COLUMN claims.claim_number IS 'Customer-facing claim reference number';
COMMENT ON COLUMN claims.claim_type IS 'Type: death, accident, property_damage, medical';
COMMENT ON COLUMN claims.claim_amount IS 'Total amount claimed';
COMMENT ON COLUMN claims.claim_date IS 'Date when claim was filed';
COMMENT ON COLUMN claims.status IS 'Status: submitted, under_review, approved, rejected, paid';
COMMENT ON COLUMN claims.approved_amount IS 'Amount approved for payment, may differ from claim_amount';
COMMENT ON COLUMN claims.settlement_date IS 'Date when claim was paid';
COMMENT ON COLUMN claims.description IS 'Detailed description of the claim';
COMMENT ON COLUMN claims.processed_by IS 'Employee who processed the claim';

COMMENT ON COLUMN premium_payments.payment_id IS 'Unique payment identifier';
COMMENT ON COLUMN premium_payments.policy_id IS 'Policy for which premium was paid';
COMMENT ON COLUMN premium_payments.payment_date IS 'Date premium was received';
COMMENT ON COLUMN premium_payments.amount IS 'Premium amount paid';
COMMENT ON COLUMN premium_payments.payment_method IS 'Method: auto_debit, check, wire_transfer, online';
COMMENT ON COLUMN premium_payments.from_account_id IS 'Bank account from which payment was made';
COMMENT ON COLUMN premium_payments.payment_status IS 'Status: completed, pending, failed, reversed';

COMMENT ON COLUMN policy_events.event_id IS 'Auto-incrementing event identifier';
COMMENT ON COLUMN policy_events.policy_id IS 'Policy associated with the event';
COMMENT ON COLUMN policy_events.event_type IS 'Type: renewal, modification, cancellation, reinstatement';
COMMENT ON COLUMN policy_events.event_date IS 'Date the event occurred';
COMMENT ON COLUMN policy_events.description IS 'Details about the event';
COMMENT ON COLUMN policy_events.performed_by IS 'Employee who performed the action';
