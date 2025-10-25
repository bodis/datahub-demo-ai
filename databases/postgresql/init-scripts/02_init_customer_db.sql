-- ============================================
-- CRM Database (customer_db)
-- ============================================
CREATE DATABASE customer_db;
\c customer_db

CREATE TABLE customer_profiles (
    customer_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    customer_segment VARCHAR(50),
    customer_status VARCHAR(20) DEFAULT 'active',
    onboarding_date DATE NOT NULL,
    assigned_agent_id VARCHAR(50),
    kyc_status VARCHAR(20),
    risk_rating VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interactions (
    interaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50),
    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_minutes INTEGER,
    notes TEXT,
    handled_by VARCHAR(50),
    outcome VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id)
);

CREATE TABLE satisfaction_surveys (
    survey_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    interaction_id VARCHAR(50),
    nps_score INTEGER CHECK (nps_score BETWEEN 0 AND 10),
    satisfaction_rating INTEGER CHECK (satisfaction_rating BETWEEN 1 AND 5),
    survey_date DATE NOT NULL,
    comments TEXT,
    FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id),
    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id)
);

CREATE TABLE complaints (
    complaint_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    complaint_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(20),
    filed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_date TIMESTAMP,
    resolution_time_hours INTEGER,
    assigned_to VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id)
);

CREATE TABLE campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(200) NOT NULL,
    campaign_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    target_segment VARCHAR(50)
);

CREATE TABLE campaign_responses (
    response_id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    response_date DATE,
    response_type VARCHAR(50),
    converted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id)
);

CREATE INDEX idx_interactions_customer ON interactions(customer_id);
CREATE INDEX idx_complaints_customer ON complaints(customer_id);
CREATE INDEX idx_satisfaction_customer ON satisfaction_surveys(customer_id);

-- Table comments for customer_db
COMMENT ON TABLE customer_profiles IS 'Customer relationship management profiles';
COMMENT ON TABLE interactions IS 'Customer interactions across all channels';
COMMENT ON TABLE satisfaction_surveys IS 'Customer satisfaction and NPS survey responses';
COMMENT ON TABLE complaints IS 'Customer complaints and their resolution tracking';
COMMENT ON TABLE campaigns IS 'Marketing campaigns targeting customers';
COMMENT ON TABLE campaign_responses IS 'Customer responses to marketing campaigns';

-- ============================================
-- customer_db - Column Comments
-- ============================================

COMMENT ON COLUMN customer_profiles.customer_id IS 'Unique customer identifier matching across all systems';
COMMENT ON COLUMN customer_profiles.full_name IS 'Complete name of the customer';
COMMENT ON COLUMN customer_profiles.email IS 'Primary email for communications and alerts';
COMMENT ON COLUMN customer_profiles.phone IS 'Primary contact phone number';
COMMENT ON COLUMN customer_profiles.address IS 'Full residential address';
COMMENT ON COLUMN customer_profiles.city IS 'City of residence';
COMMENT ON COLUMN customer_profiles.country IS 'Country of residence';
COMMENT ON COLUMN customer_profiles.customer_segment IS 'Classification: retail, premium, corporate, private_banking';
COMMENT ON COLUMN customer_profiles.customer_status IS 'Lifecycle status: active, dormant, closed';
COMMENT ON COLUMN customer_profiles.onboarding_date IS 'Date when customer relationship was established';
COMMENT ON COLUMN customer_profiles.assigned_agent_id IS 'Employee ID of the assigned relationship manager';
COMMENT ON COLUMN customer_profiles.kyc_status IS 'Know Your Customer verification status';
COMMENT ON COLUMN customer_profiles.risk_rating IS 'Overall customer risk level: low, medium, high';
COMMENT ON COLUMN customer_profiles.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN customer_profiles.updated_at IS 'Last update timestamp';

COMMENT ON COLUMN interactions.interaction_id IS 'Unique identifier for each customer interaction';
COMMENT ON COLUMN interactions.customer_id IS 'Reference to customer who had the interaction';
COMMENT ON COLUMN interactions.interaction_type IS 'Type: call, email, chat, branch_visit, complaint';
COMMENT ON COLUMN interactions.channel IS 'Channel used: phone, email, web, mobile_app, branch';
COMMENT ON COLUMN interactions.interaction_date IS 'When the interaction occurred';
COMMENT ON COLUMN interactions.duration_minutes IS 'Length of interaction in minutes';
COMMENT ON COLUMN interactions.notes IS 'Detailed notes about the interaction';
COMMENT ON COLUMN interactions.handled_by IS 'Employee ID who handled the interaction';
COMMENT ON COLUMN interactions.outcome IS 'Result: resolved, escalated, follow_up_needed';

COMMENT ON COLUMN satisfaction_surveys.survey_id IS 'Auto-incrementing survey identifier';
COMMENT ON COLUMN satisfaction_surveys.customer_id IS 'Customer who completed the survey';
COMMENT ON COLUMN satisfaction_surveys.interaction_id IS 'Related interaction if survey is interaction-specific';
COMMENT ON COLUMN satisfaction_surveys.nps_score IS 'Net Promoter Score: 0-10 scale';
COMMENT ON COLUMN satisfaction_surveys.satisfaction_rating IS 'Overall satisfaction: 1-5 stars';
COMMENT ON COLUMN satisfaction_surveys.survey_date IS 'Date survey was completed';
COMMENT ON COLUMN satisfaction_surveys.comments IS 'Free-text customer feedback';

COMMENT ON COLUMN complaints.complaint_id IS 'Unique complaint identifier';
COMMENT ON COLUMN complaints.customer_id IS 'Customer who filed the complaint';
COMMENT ON COLUMN complaints.complaint_type IS 'Category: service, fee, product, fraud, other';
COMMENT ON COLUMN complaints.description IS 'Detailed description of the complaint';
COMMENT ON COLUMN complaints.status IS 'Current status: open, investigating, resolved, closed';
COMMENT ON COLUMN complaints.priority IS 'Priority level: low, medium, high, critical';
COMMENT ON COLUMN complaints.filed_date IS 'When complaint was filed';
COMMENT ON COLUMN complaints.resolved_date IS 'When complaint was resolved, NULL if still open';
COMMENT ON COLUMN complaints.resolution_time_hours IS 'Time taken to resolve in hours';
COMMENT ON COLUMN complaints.assigned_to IS 'Employee ID responsible for resolution';

COMMENT ON COLUMN campaigns.campaign_id IS 'Unique campaign identifier';
COMMENT ON COLUMN campaigns.campaign_name IS 'Descriptive name of the marketing campaign';
COMMENT ON COLUMN campaigns.campaign_type IS 'Type: email, direct_mail, digital, cross_sell';
COMMENT ON COLUMN campaigns.start_date IS 'Campaign start date';
COMMENT ON COLUMN campaigns.end_date IS 'Campaign end date';
COMMENT ON COLUMN campaigns.target_segment IS 'Customer segment targeted by campaign';

COMMENT ON COLUMN campaign_responses.response_id IS 'Auto-incrementing response identifier';
COMMENT ON COLUMN campaign_responses.campaign_id IS 'Campaign that generated the response';
COMMENT ON COLUMN campaign_responses.customer_id IS 'Customer who responded';
COMMENT ON COLUMN campaign_responses.response_date IS 'When customer responded';
COMMENT ON COLUMN campaign_responses.response_type IS 'Type: clicked, opened, unsubscribed, purchased';
COMMENT ON COLUMN campaign_responses.converted IS 'Whether response resulted in conversion';
