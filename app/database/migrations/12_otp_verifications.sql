CREATE TABLE IF NOT EXISTS otp_verifications (
    email VARCHAR(255) PRIMARY KEY,
    otp_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Index for cleanup
CREATE INDEX idx_otp_expires ON otp_verifications(expires_at);
