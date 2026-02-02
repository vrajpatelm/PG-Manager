-- Create complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES owners(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'IN_PROGRESS', 'RESOLVED'
    priority VARCHAR(10) DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX idx_complaints_owner ON complaints(owner_id);
CREATE INDEX idx_complaints_status ON complaints(status);
