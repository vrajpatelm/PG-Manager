-- Database Initialization Script

-- 1. Create Enum Type for User Roles
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('OWNER', 'TENANT', 'ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'TENANT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Owners Table
CREATE TABLE IF NOT EXISTS owners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    business_name VARCHAR(100),
    upi_id VARCHAR(50),
    qr_code_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_owners_user_id UNIQUE (user_id)
);

-- 4. Create Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES owners(id) ON DELETE CASCADE,
    
    -- The Link to the Login Account (Initially NULL)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, 
    
    -- Tenant Details (Added by Owner)
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    room_number VARCHAR(20),
    bed_number VARCHAR(10),
    
    -- Financials
    monthly_rent INTEGER NOT NULL,
    security_deposit INTEGER,
    lease_start DATE,
    lease_end DATE,
    
    -- Status
    onboarding_status VARCHAR(20) DEFAULT 'PENDING',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure an email can only be added once per owner
    CONSTRAINT uq_tenant_email_owner UNIQUE (owner_id, email)
);
