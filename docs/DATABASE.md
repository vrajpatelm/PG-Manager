# Database Documentation 🗃️

## 1. Schema Overview

The application uses **PostgreSQL**. The schema is designed around a central `users` table for authentication, with separate profile tables for `owners` and `tenants`.

### Entity Relationship Diagram (Conceptual)
*   **Users** (1) ---- (1) **Owners**
*   **Users** (1) ---- (1) **Tenants**
*   **Owners** (1) ---- (Many) **Tenants**

## 2. Table Definitions

### `users`
Stores authentication credentials for all system users.
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique User ID |
| `email` | VARCHAR | Unique Login Email |
| `password_hash` | VARCHAR | Hashed Password |
| `role` | ENUM | 'OWNER', 'TENANT', 'ADMIN' |

### `owners`
Profile information for PG Managers.
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique Owner Profile ID |
| `user_id` | UUID (FK) | Link to `users` table |
| `full_name` | VARCHAR | Display Name |
| `business_name` | VARCHAR | Name of the PG |
| `upi_id` | VARCHAR | For payments |

### `tenants`
Stores tenant details. **Critical:** This table acts as a whitelist for tenant signup.
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique Tenant Profile ID |
| `owner_id` | UUID (FK) | Link to the Owner managing them |
| `user_id` | UUID (FK) | Nullable. Links to `users` once signed up. |
| `full_name` | VARCHAR | Tenant Name |
| `email` | VARCHAR | Used for invitation verification |
| `phone_number` | VARCHAR | Contact Number |
| `room_number` | VARCHAR | Assigned Room |
| `bed_number` | VARCHAR | Assigned Bed (Optional) |
| `monthly_rent` | INTEGER | Monthly Rent Amount (Required) |
| `security_deposit`| INTEGER | Security Deposit Amount |
| `lease_start` | DATE | Lease Start Date |
| `lease_end` | DATE | Lease End Date |
| `onboarding_status`| VARCHAR | 'PENDING' vs 'ACTIVE' |

## 3. Key Workflows

### Tenant Invitation Logic
1.  Owner adds a tenant in dashboard.
    *   `INSERT INTO tenants (owner_id, email, status) VALUES (..., 'PENDING')`
    *   `user_id` is currently `NULL`.
2.  Tenant signs up with that email.
3.  System verifies email exists in `tenants`.
4.  System creates `users` record.
5.  System updates `tenants` record:
    *   `UPDATE tenants SET user_id = new_user_id, status = 'ACTIVE' ...`

## 4. Resetting the Database
If you need to wipe everything and start fresh, run these SQL commands:

```sql
DROP TABLE IF EXISTS tenants;
DROP TABLE IF EXISTS owners;
DROP TABLE IF EXISTS users;
DROP TYPE IF EXISTS user_role;
```
Then run `python app/database/init_db.py` again.
