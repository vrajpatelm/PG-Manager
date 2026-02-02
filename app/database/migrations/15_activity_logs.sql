CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES owners(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'PAYMENT', 'COMPLAINT', 'TENANT_ADD', 'NOTICE', 'SYSTEM'
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Store extra IDs like tenant_id, payment_id for links
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast sorting by date
CREATE INDEX idx_activity_logs_owner_date ON activity_logs(owner_id, created_at DESC);
