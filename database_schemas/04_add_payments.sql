-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    amount INTEGER NOT NULL,
    payment_date DATE DEFAULT CURRENT_DATE,
    payment_month VARCHAR(7), -- Format: 'YYYY-MM'
    status VARCHAR(20) DEFAULT 'COMPLETED', -- 'COMPLETED', 'PENDING', 'FAILED'
    payment_mode VARCHAR(50),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster dashboard queries
CREATE INDEX idx_payments_month ON payments(payment_month);
CREATE INDEX idx_payments_tenant ON payments(tenant_id);
