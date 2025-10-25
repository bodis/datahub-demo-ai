-- ============================================
-- Loan Management Database (loans_db)
-- ============================================
CREATE DATABASE loans_db;

CREATE TABLE loan_applications (
    application_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    loan_type VARCHAR(50) NOT NULL,
    requested_amount DECIMAL(15,2) NOT NULL,
    application_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    officer_id VARCHAR(50),
    decision_date DATE,
    approved_amount DECIMAL(15,2),
    rejection_reason TEXT
);

CREATE TABLE loans (
    loan_id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50),
    loan_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    linked_account_id VARCHAR(50),
    loan_type VARCHAR(50) NOT NULL,
    principal_amount DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,4) NOT NULL,
    term_months INTEGER NOT NULL,
    disbursement_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    loan_status VARCHAR(50) DEFAULT 'active',
    outstanding_balance DECIMAL(15,2),
    default_status BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(50),
    FOREIGN KEY (application_id) REFERENCES loan_applications(application_id)
);

CREATE TABLE collateral (
    collateral_id VARCHAR(50) PRIMARY KEY,
    loan_id VARCHAR(50) NOT NULL,
    collateral_type VARCHAR(100) NOT NULL,
    description TEXT,
    appraised_value DECIMAL(15,2) NOT NULL,
    appraisal_date DATE,
    ltv_ratio DECIMAL(5,4),
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE repayment_schedule (
    schedule_id SERIAL PRIMARY KEY,
    loan_id VARCHAR(50) NOT NULL,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    principal_amount DECIMAL(15,2) NOT NULL,
    interest_amount DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    payment_date DATE,
    payment_status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE loan_guarantors (
    guarantor_id SERIAL PRIMARY KEY,
    loan_id VARCHAR(50) NOT NULL,
    guarantor_name VARCHAR(200) NOT NULL,
    relationship VARCHAR(50),
    contact_info TEXT,
    guarantee_amount DECIMAL(15,2),
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE risk_assessments (
    assessment_id SERIAL PRIMARY KEY,
    loan_id VARCHAR(50),
    application_id VARCHAR(50),
    assessment_date DATE NOT NULL,
    risk_score INTEGER CHECK (risk_score BETWEEN 0 AND 1000),
    pd_probability DECIMAL(5,4),
    credit_grade VARCHAR(10),
    assessed_by VARCHAR(50)
);

CREATE INDEX idx_loans_customer ON loans(customer_id);
CREATE INDEX idx_applications_customer ON loan_applications(customer_id);
CREATE INDEX idx_schedule_loan ON repayment_schedule(loan_id);

-- Table comments for loans_db
COMMENT ON TABLE loan_applications IS 'Loan applications submitted by customers';
COMMENT ON TABLE loans IS 'Active and historical loan accounts';
COMMENT ON TABLE collateral IS 'Assets pledged as security for loans';
COMMENT ON TABLE repayment_schedule IS 'Scheduled loan repayment installments';
COMMENT ON TABLE loan_guarantors IS 'Third-party guarantors for loans';
COMMENT ON TABLE risk_assessments IS 'Credit risk assessments for loans and applications';

-- ============================================
-- loans_db - Column Comments
-- ============================================

COMMENT ON COLUMN loan_applications.application_id IS 'Unique loan application identifier';
COMMENT ON COLUMN loan_applications.customer_id IS 'Customer applying for the loan';
COMMENT ON COLUMN loan_applications.loan_type IS 'Type: mortgage, personal, auto, business, education';
COMMENT ON COLUMN loan_applications.requested_amount IS 'Amount customer requested to borrow';
COMMENT ON COLUMN loan_applications.application_date IS 'Date application was submitted';
COMMENT ON COLUMN loan_applications.status IS 'Status: pending, approved, rejected, withdrawn';
COMMENT ON COLUMN loan_applications.officer_id IS 'Loan officer handling the application';
COMMENT ON COLUMN loan_applications.decision_date IS 'Date final decision was made';
COMMENT ON COLUMN loan_applications.approved_amount IS 'Amount approved, may differ from requested';
COMMENT ON COLUMN loan_applications.rejection_reason IS 'Reason for rejection if applicable';

COMMENT ON COLUMN loans.loan_id IS 'System-generated unique loan identifier';
COMMENT ON COLUMN loans.application_id IS 'Original application that led to this loan';
COMMENT ON COLUMN loans.loan_number IS 'Customer-facing loan account number';
COMMENT ON COLUMN loans.customer_id IS 'Customer who received the loan';
COMMENT ON COLUMN loans.linked_account_id IS 'Bank account for disbursement and repayment';
COMMENT ON COLUMN loans.loan_type IS 'Type of loan product';
COMMENT ON COLUMN loans.principal_amount IS 'Original loan amount disbursed';
COMMENT ON COLUMN loans.interest_rate IS 'Annual interest rate as decimal (e.g., 0.0525 for 5.25%)';
COMMENT ON COLUMN loans.term_months IS 'Loan term length in months';
COMMENT ON COLUMN loans.disbursement_date IS 'Date loan funds were disbursed';
COMMENT ON COLUMN loans.maturity_date IS 'Final payment due date';
COMMENT ON COLUMN loans.loan_status IS 'Status: active, paid_off, defaulted, restructured';
COMMENT ON COLUMN loans.outstanding_balance IS 'Current remaining balance to be paid';
COMMENT ON COLUMN loans.default_status IS 'Whether loan is currently in default';
COMMENT ON COLUMN loans.approved_by IS 'Employee who approved the loan';

COMMENT ON COLUMN collateral.collateral_id IS 'Unique collateral identifier';
COMMENT ON COLUMN collateral.loan_id IS 'Loan secured by this collateral';
COMMENT ON COLUMN collateral.collateral_type IS 'Type: property, vehicle, equipment, securities';
COMMENT ON COLUMN collateral.description IS 'Detailed description of the collateral';
COMMENT ON COLUMN collateral.appraised_value IS 'Professional appraisal value';
COMMENT ON COLUMN collateral.appraisal_date IS 'Date of last appraisal';
COMMENT ON COLUMN collateral.ltv_ratio IS 'Loan-to-Value ratio as decimal';

COMMENT ON COLUMN repayment_schedule.schedule_id IS 'Auto-incrementing schedule entry identifier';
COMMENT ON COLUMN repayment_schedule.loan_id IS 'Loan this schedule belongs to';
COMMENT ON COLUMN repayment_schedule.installment_number IS 'Sequential installment number';
COMMENT ON COLUMN repayment_schedule.due_date IS 'Payment due date';
COMMENT ON COLUMN repayment_schedule.principal_amount IS 'Principal portion of payment';
COMMENT ON COLUMN repayment_schedule.interest_amount IS 'Interest portion of payment';
COMMENT ON COLUMN repayment_schedule.total_amount IS 'Total payment amount due';
COMMENT ON COLUMN repayment_schedule.payment_date IS 'Actual date payment was received';
COMMENT ON COLUMN repayment_schedule.payment_status IS 'Status: pending, paid, late, missed';

COMMENT ON COLUMN loan_guarantors.guarantor_id IS 'Auto-incrementing guarantor identifier';
COMMENT ON COLUMN loan_guarantors.loan_id IS 'Loan being guaranteed';
COMMENT ON COLUMN loan_guarantors.guarantor_name IS 'Full name of guarantor';
COMMENT ON COLUMN loan_guarantors.relationship IS 'Relationship to borrower';
COMMENT ON COLUMN loan_guarantors.contact_info IS 'Guarantor contact information';
COMMENT ON COLUMN loan_guarantors.guarantee_amount IS 'Amount guaranteed by this guarantor';

COMMENT ON COLUMN risk_assessments.assessment_id IS 'Auto-incrementing assessment identifier';
COMMENT ON COLUMN risk_assessments.loan_id IS 'Loan being assessed, NULL for applications';
COMMENT ON COLUMN risk_assessments.application_id IS 'Application being assessed, NULL for existing loans';
COMMENT ON COLUMN risk_assessments.assessment_date IS 'Date assessment was performed';
COMMENT ON COLUMN risk_assessments.risk_score IS 'Credit risk score: 0-1000 scale';
COMMENT ON COLUMN risk_assessments.pd_probability IS 'Probability of Default as decimal';
COMMENT ON COLUMN risk_assessments.credit_grade IS 'Letter grade: AAA, AA, A, BBB, BB, B, CCC, etc.';
COMMENT ON COLUMN risk_assessments.assessed_by IS 'Employee or system that performed assessment';
