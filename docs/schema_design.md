# Database Schema & Authentication Design

## 1. Authentication Strategy (Role-Based with Pre-Verification) 🔐

We will use a **Pre-Verification Flow** for tenants to ensure security and valid tenancy.

### The Logic:
1.  **Owners**: Can sign up freely (Business logic).
2.  **Tenants**: Can **ONLY** sign up if their email has already been added to the system by an Owner.

---

## 2. Table Scripts (PostgreSQL) 🗄️

### A. Users Table (Auth Credentials)
Stores login info for everyone.
```sql
CREATE TYPE user_role AS ENUM ('OWNER', 'TENANT', 'ADMIN');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'TENANT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### B. Owners Table (Profiles)
Detailed profile for the PG Owner.
```sql
CREATE TABLE owners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    business_name VARCHAR(100),
    upi_id VARCHAR(50),
    qr_code_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### C. Tenants Table (The Verification Core) 🛡️
This table does double duty: it stores tenant data for the Owner **AND** acts as the whitelist for Signup.

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES owners(id) ON DELETE CASCADE, -- Belongs to this Owner
    
    -- The Link to the Login Account (Initially NULL)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, 
    
    -- Tenant Details (Added by Owner)
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,    -- Used for verification
    phone_number VARCHAR(20),
    room_number VARCHAR(20),
    
    -- Status
    onboarding_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING -> ACTIVE (after signup)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure an email can only be added once per owner (or globally if strict)
    CONSTRAINT uq_tenant_email_owner UNIQUE (owner_id, email)
);
```

---

## 3. The Signup Workflows 🔄

### Scenario A: Owner Signup (standard)
1.  User fills Signup Form.
2.  Backend creates `users` entry (Role='OWNER').
3.  Backend creates `owners` entry.
4.  **Result**: Owner Dashboard.

### Scenario B: Tenant Signup (The "Invite" Check)
**Pre-condition**: Owner has successfully added a tenant with email `tenant@example.com` via their dashboard. (Table `tenants` has a row with this email, but `user_id` is NULL).

1.  **Tenant visits Signup Page**.
2.  Tenant enters Email: `tenant@example.com` and Password.
3.  **Backend Verification Step**:
    *   Query: `SELECT * FROM tenants WHERE email = 'tenant@example.com'`
    *   **IF NO MATCH**: 
        *   ❌ **Stop Signup**.
        *   Return Message: *"No active invitation found. Please ask your PG Owner to add your email first."*
    *   **IF MATCH FOUND**:
        *   ✅ **Proceed**.
        *   Create `users` entry (Role='TENANT', Email, Password).
        *   **Link Accounts**: Update the existing row in `tenants` table set `user_id` = `new_users_id`.
        *   **Result**: Tenant Dashboard (Pre-filled with the room info the owner already added!).

## 4. Why this is better?
-   **No Fake Accounts**: Random people cannot create tenant accounts.
-   **Seamless Onboarding**: When a tenant logs in for the first time, they *automatically* see their specific PG details, Room Number, and Due Rent because the system already linked them to the Owner who added them.
