-- ============================================
-- HR Database (employees_db)
-- ============================================
CREATE DATABASE employees_db;
\c employees_db

CREATE TABLE employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    employee_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(20),
    role VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    branch_code VARCHAR(10),
    manager_id VARCHAR(50),
    hire_date DATE NOT NULL,
    termination_date DATE,
    employment_status VARCHAR(20) DEFAULT 'active',
    salary DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

CREATE TABLE departments (
    department_id VARCHAR(50) PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL,
    department_head_id VARCHAR(50),
    budget DECIMAL(15,2),
    FOREIGN KEY (department_head_id) REFERENCES employees(employee_id)
);

CREATE TABLE performance_reviews (
    review_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    review_date DATE NOT NULL,
    reviewer_id VARCHAR(50) NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    goals_met INTEGER,
    comments TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (reviewer_id) REFERENCES employees(employee_id)
);

CREATE TABLE training_programs (
    program_id VARCHAR(50) PRIMARY KEY,
    program_name VARCHAR(200) NOT NULL,
    description TEXT,
    duration_hours INTEGER,
    certification BOOLEAN DEFAULT FALSE
);

CREATE TABLE employee_training (
    training_record_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    program_id VARCHAR(50) NOT NULL,
    enrollment_date DATE,
    completion_date DATE,
    status VARCHAR(50) DEFAULT 'enrolled',
    score INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (program_id) REFERENCES training_programs(program_id)
);

CREATE TABLE employee_assignments (
    assignment_id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    assignment_type VARCHAR(50) NOT NULL,
    related_entity_id VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE INDEX idx_employees_department ON employees(department);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_reviews_employee ON performance_reviews(employee_id);

-- Table comments for employees_db
COMMENT ON TABLE employees IS 'Bank employee records and employment details';
COMMENT ON TABLE departments IS 'Organizational departments within the bank';
COMMENT ON TABLE performance_reviews IS 'Employee performance evaluation records';
COMMENT ON TABLE training_programs IS 'Available training and certification programs';
COMMENT ON TABLE employee_training IS 'Employee enrollment and completion in training programs';
COMMENT ON TABLE employee_assignments IS 'Employee assignments to customers, projects, or branches';

-- ============================================
-- employees_db - Column Comments
-- ============================================

COMMENT ON COLUMN employees.employee_id IS 'System-generated unique employee identifier';
COMMENT ON COLUMN employees.employee_number IS 'Human-readable employee number';
COMMENT ON COLUMN employees.first_name IS 'Employee first name';
COMMENT ON COLUMN employees.last_name IS 'Employee last name';
COMMENT ON COLUMN employees.email IS 'Corporate email address';
COMMENT ON COLUMN employees.phone IS 'Work phone number';
COMMENT ON COLUMN employees.role IS 'Job title or position';
COMMENT ON COLUMN employees.department IS 'Department name: lending, operations, risk, customer_service';
COMMENT ON COLUMN employees.branch_code IS 'Branch location code where employee works';
COMMENT ON COLUMN employees.manager_id IS 'Employee ID of direct manager';
COMMENT ON COLUMN employees.hire_date IS 'Date employee was hired';
COMMENT ON COLUMN employees.termination_date IS 'Date employment ended, NULL if currently employed';
COMMENT ON COLUMN employees.employment_status IS 'Status: active, on_leave, terminated';
COMMENT ON COLUMN employees.salary IS 'Annual salary amount';
COMMENT ON COLUMN employees.created_at IS 'Record creation timestamp';

COMMENT ON COLUMN departments.department_id IS 'Unique department identifier';
COMMENT ON COLUMN departments.department_name IS 'Official department name';
COMMENT ON COLUMN departments.department_head_id IS 'Employee ID of department head';
COMMENT ON COLUMN departments.budget IS 'Annual department budget';

COMMENT ON COLUMN performance_reviews.review_id IS 'Auto-incrementing review identifier';
COMMENT ON COLUMN performance_reviews.employee_id IS 'Employee being reviewed';
COMMENT ON COLUMN performance_reviews.review_date IS 'Date of the performance review';
COMMENT ON COLUMN performance_reviews.reviewer_id IS 'Employee ID of the reviewer, typically manager';
COMMENT ON COLUMN performance_reviews.rating IS 'Overall performance rating: 1-5 scale';
COMMENT ON COLUMN performance_reviews.goals_met IS 'Number or percentage of goals achieved';
COMMENT ON COLUMN performance_reviews.comments IS 'Detailed review comments';

COMMENT ON COLUMN training_programs.program_id IS 'Unique training program identifier';
COMMENT ON COLUMN training_programs.program_name IS 'Name of the training program';
COMMENT ON COLUMN training_programs.description IS 'Detailed description of program content';
COMMENT ON COLUMN training_programs.duration_hours IS 'Total program duration in hours';
COMMENT ON COLUMN training_programs.certification IS 'Whether program awards certification upon completion';

COMMENT ON COLUMN employee_training.training_record_id IS 'Auto-incrementing training record identifier';
COMMENT ON COLUMN employee_training.employee_id IS 'Employee enrolled in training';
COMMENT ON COLUMN employee_training.program_id IS 'Training program enrolled in';
COMMENT ON COLUMN employee_training.enrollment_date IS 'Date employee enrolled';
COMMENT ON COLUMN employee_training.completion_date IS 'Date employee completed training';
COMMENT ON COLUMN employee_training.status IS 'Status: enrolled, in_progress, completed, dropped';
COMMENT ON COLUMN employee_training.score IS 'Final score or grade if applicable';

COMMENT ON COLUMN employee_assignments.assignment_id IS 'Auto-incrementing assignment identifier';
COMMENT ON COLUMN employee_assignments.employee_id IS 'Employee assigned';
COMMENT ON COLUMN employee_assignments.assignment_type IS 'Type: customer_portfolio, project, branch_coverage';
COMMENT ON COLUMN employee_assignments.related_entity_id IS 'ID of related entity (customer, project, branch)';
COMMENT ON COLUMN employee_assignments.start_date IS 'Assignment start date';
COMMENT ON COLUMN employee_assignments.end_date IS 'Assignment end date, NULL if ongoing';
