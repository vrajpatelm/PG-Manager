-- Create expenses table
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES owners(id),
    category VARCHAR(50) NOT NULL, -- 'UTILITIES', 'MAINTENANCE', 'SALARY', 'MARKETING', 'OTHER'
    amount INTEGER NOT NULL,
    description TEXT,
    expense_date DATE DEFAULT CURRENT_DATE,
    expense_month VARCHAR(7), -- Format: 'YYYY-MM'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for analytics
CREATE INDEX idx_expenses_month ON expenses(expense_month);
CREATE INDEX idx_expenses_owner ON expenses(owner_id);
