-- ============================================
-- Compliance & Audit Database (compliance_db)
-- ============================================
CREATE DATABASE compliance_db;
\c compliance_db

CREATE TABLE kyc_records (
    kyc_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    verification_date DATE NOT NULL,
    kyc_status VARCHAR(20) NOT NULL,
    document_type VARCHAR(100),
    document_number VARCHAR(100),
    expiry_date DATE,
    verified_by VARCHAR(50),
    next_review_date DATE,
    risk_rating VARCHAR(20)
);

CREATE TABLE aml_checks (
    check_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    transaction_id VARCHAR(50),
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_type VARCHAR(50) NOT NULL,
    aml_flag BOOLEAN DEFAULT FALSE,
    risk_level VARCHAR(20),
    screening_result TEXT,
    reviewed_by VARCHAR(50)
);

CREATE TABLE suspicious_activity_reports (
    sar_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    account_id VARCHAR(50),
    report_date DATE NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    sar_status VARCHAR(50) DEFAULT 'draft',
    filed_date DATE,
    regulatory_tier VARCHAR(20),
    filed_by VARCHAR(50),
    amount_involved DECIMAL(15,2)
);

CREATE TABLE regulatory_reports (
    report_id VARCHAR(50) PRIMARY KEY,
    report_type VARCHAR(100) NOT NULL,
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    submission_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    prepared_by VARCHAR(50),
    approved_by VARCHAR(50)
);

CREATE TABLE audit_trails (
    audit_id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(50) NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45)
);

CREATE TABLE compliance_rules (
    rule_id VARCHAR(50) PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    description TEXT,
    threshold_value DECIMAL(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATE NOT NULL
);

CREATE TABLE rule_violations (
    violation_id VARCHAR(50) PRIMARY KEY,
    rule_id VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    violation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20),
    status VARCHAR(50) DEFAULT 'open',
    resolution_notes TEXT,
    resolved_by VARCHAR(50),
    resolved_date DATE,
    FOREIGN KEY (rule_id) REFERENCES compliance_rules(rule_id)
);

CREATE INDEX idx_kyc_customer ON kyc_records(customer_id);
CREATE INDEX idx_aml_customer ON aml_checks(customer_id);
CREATE INDEX idx_sar_customer ON suspicious_activity_reports(customer_id);
CREATE INDEX idx_audit_entity ON audit_trails(entity_type, entity_id);

-- Table comments for compliance_db
COMMENT ON TABLE kyc_records IS 'Know Your Customer verification records';
COMMENT ON TABLE aml_checks IS 'Anti-Money Laundering screening checks';
COMMENT ON TABLE suspicious_activity_reports IS 'Suspicious Activity Reports filed with regulators';
COMMENT ON TABLE regulatory_reports IS 'Regulatory compliance reports submitted to authorities';
COMMENT ON TABLE audit_trails IS 'System audit log for all critical actions';
COMMENT ON TABLE compliance_rules IS 'Automated compliance rules and thresholds';
COMMENT ON TABLE rule_violations IS 'Compliance rule violations and their resolution';

-- ============================================
-- compliance_db - Column Comments
-- ============================================

COMMENT ON COLUMN kyc_records.kyc_id IS 'Unique KYC record identifier';
COMMENT ON COLUMN kyc_records.customer_id IS 'Customer being verified';
COMMENT ON COLUMN kyc_records.verification_date IS 'Date verification was completed';
COMMENT ON COLUMN kyc_records.kyc_status IS 'Status: verified, pending, expired, rejected';
COMMENT ON COLUMN kyc_records.document_type IS 'Type of ID document: passport, drivers_license, national_id';
COMMENT ON COLUMN kyc_records.document_number IS 'Identification document number';
COMMENT ON COLUMN kyc_records.expiry_date IS 'Document expiration date';
COMMENT ON COLUMN kyc_records.verified_by IS 'Employee who verified the documents';
COMMENT ON COLUMN kyc_records.next_review_date IS 'Date when KYC needs to be refreshed';
COMMENT ON COLUMN kyc_records.risk_rating IS 'Customer risk level: low, medium, high';

COMMENT ON COLUMN aml_checks.check_id IS 'Unique AML check identifier';
COMMENT ON COLUMN aml_checks.customer_id IS 'Customer being screened';
COMMENT ON COLUMN aml_checks.transaction_id IS 'Transaction being screened if applicable';
COMMENT ON COLUMN aml_checks.check_date IS 'When check was performed';
COMMENT ON COLUMN aml_checks.check_type IS 'Type: watchlist, sanctions, pep_screening, transaction_monitoring';
COMMENT ON COLUMN aml_checks.aml_flag IS 'Whether check raised a concern';
COMMENT ON COLUMN aml_checks.risk_level IS 'Risk level identified: low, medium, high';
COMMENT ON COLUMN aml_checks.screening_result IS 'Detailed results of the screening';
COMMENT ON COLUMN aml_checks.reviewed_by IS 'Compliance officer who reviewed results';

COMMENT ON COLUMN suspicious_activity_reports.sar_id IS 'Unique SAR identifier';
COMMENT ON COLUMN suspicious_activity_reports.customer_id IS 'Customer involved in suspicious activity';
COMMENT ON COLUMN suspicious_activity_reports.account_id IS 'Account involved if applicable';
COMMENT ON COLUMN suspicious_activity_reports.report_date IS 'Date SAR was created';
COMMENT ON COLUMN suspicious_activity_reports.activity_type IS 'Type: structuring, unusual_pattern, high_risk_country';
COMMENT ON COLUMN suspicious_activity_reports.description IS 'Detailed description of suspicious activity';
COMMENT ON COLUMN suspicious_activity_reports.sar_status IS 'Status: draft, filed, under_review, closed';
COMMENT ON COLUMN suspicious_activity_reports.filed_date IS 'Date filed with regulator';
COMMENT ON COLUMN suspicious_activity_reports.regulatory_tier IS 'Classification tier for regulatory purposes';
COMMENT ON COLUMN suspicious_activity_reports.filed_by IS 'Compliance officer who filed the SAR';
COMMENT ON COLUMN suspicious_activity_reports.amount_involved IS 'Total monetary amount involved';

COMMENT ON COLUMN regulatory_reports.report_id IS 'Unique regulatory report identifier';
COMMENT ON COLUMN regulatory_reports.report_type IS 'Type: capital_adequacy, liquidity, stress_test, quarterly_filing';
COMMENT ON COLUMN regulatory_reports.reporting_period_start IS 'Start of reporting period';
COMMENT ON COLUMN regulatory_reports.reporting_period_end IS 'End of reporting period';
COMMENT ON COLUMN regulatory_reports.submission_date IS 'Date submitted to regulator';
COMMENT ON COLUMN regulatory_reports.status IS 'Status: pending, submitted, accepted, rejected';
COMMENT ON COLUMN regulatory_reports.prepared_by IS 'Employee who prepared the report';
COMMENT ON COLUMN regulatory_reports.approved_by IS 'Senior officer who approved submission';

COMMENT ON COLUMN audit_trails.audit_id IS 'Auto-incrementing audit record identifier';
COMMENT ON COLUMN audit_trails.entity_type IS 'Type of entity: account, customer, loan, transaction';
COMMENT ON COLUMN audit_trails.entity_id IS 'ID of the entity being audited';
COMMENT ON COLUMN audit_trails.action IS 'Action performed: create, update, delete, view';
COMMENT ON COLUMN audit_trails.performed_by IS 'Employee who performed the action';
COMMENT ON COLUMN audit_trails.performed_at IS 'Timestamp of the action';
COMMENT ON COLUMN audit_trails.old_value IS 'Previous value before change';
COMMENT ON COLUMN audit_trails.new_value IS 'New value after change';
COMMENT ON COLUMN audit_trails.ip_address IS 'IP address from which action was performed';

COMMENT ON COLUMN compliance_rules.rule_id IS 'Unique compliance rule identifier';
COMMENT ON COLUMN compliance_rules.rule_name IS 'Descriptive name of the rule';
COMMENT ON COLUMN compliance_rules.rule_type IS 'Type: transaction_limit, velocity_check, geographic_restriction';
COMMENT ON COLUMN compliance_rules.description IS 'Detailed description of the rule';
COMMENT ON COLUMN compliance_rules.threshold_value IS 'Numeric threshold that triggers the rule';
COMMENT ON COLUMN compliance_rules.is_active IS 'Whether rule is currently enforced';
COMMENT ON COLUMN compliance_rules.created_date IS 'Date rule was created';

COMMENT ON COLUMN rule_violations.violation_id IS 'Unique violation identifier';
COMMENT ON COLUMN rule_violations.rule_id IS 'Rule that was violated';
COMMENT ON COLUMN rule_violations.entity_type IS 'Type of entity that violated: transaction, account, customer';
COMMENT ON COLUMN rule_violations.entity_id IS 'ID of the entity that violated';
COMMENT ON COLUMN rule_violations.violation_date IS 'When violation occurred';
COMMENT ON COLUMN rule_violations.severity IS 'Severity: low, medium, high, critical';
COMMENT ON COLUMN rule_violations.status IS 'Status: open, investigating, resolved, false_positive';
COMMENT ON COLUMN rule_violations.resolution_notes IS 'Notes about how violation was resolved';
COMMENT ON COLUMN rule_violations.resolved_by IS 'Employee who resolved the violation';
COMMENT ON COLUMN rule_violations.resolved_date IS 'Date violation was resolved';