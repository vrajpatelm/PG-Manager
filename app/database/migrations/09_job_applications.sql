DROP TABLE IF EXISTS job_applications;

CREATE TABLE job_applications (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role_applied VARCHAR(100) NOT NULL,
    -- Resume Storage (Binary)
    resume_filename VARCHAR(255) NOT NULL,
    resume_data BYTEA NOT NULL,
    resume_mimetype VARCHAR(100) NOT NULL,
    
    cover_letter TEXT,
    
    -- Professional Details
    linkedin_url VARCHAR(255),
    portfolio_url VARCHAR(255),
    experience_years VARCHAR(50), -- e.g., "3.5 Years"
    current_ctc VARCHAR(50),
    expected_ctc VARCHAR(50),
    notice_period VARCHAR(50),    -- e.g., "30 Days"

    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, CONTACTED, REJECTED
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookup by role or status
CREATE INDEX IF NOT EXISTS idx_apps_role ON job_applications(role_applied);
CREATE INDEX IF NOT EXISTS idx_apps_status ON job_applications(status);
