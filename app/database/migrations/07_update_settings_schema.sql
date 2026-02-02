-- 1. Update Owners Table (Banking & Preferences)
ALTER TABLE owners 
ADD COLUMN IF NOT EXISTS account_holder_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS account_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS ifsc_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{"email_alerts": true, "sms_alerts": true, "dark_mode": false}';

-- 2. Update Properties Table (Rules & Info)
-- We are adding these to the properties table to allow per-property rules in the future
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS wifi_ssid VARCHAR(100),
ADD COLUMN IF NOT EXISTS wifi_password VARCHAR(100),
ADD COLUMN IF NOT EXISTS gate_closing_time TIME,
ADD COLUMN IF NOT EXISTS breakfast_start_time TIME,
ADD COLUMN IF NOT EXISTS breakfast_end_time TIME,
ADD COLUMN IF NOT EXISTS house_rules TEXT,
ADD COLUMN IF NOT EXISTS late_fee_daily INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS rent_grace_period_days INTEGER DEFAULT 5;
