
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

def init_db():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Connected to database. Creating tables...")

        # 1. Create Enum Type for User Roles
        try:
            cur.execute("CREATE TYPE user_role AS ENUM ('OWNER', 'TENANT', 'ADMIN');")
        except psycopg2.errors.DuplicateObject:
            print("Enum type 'user_role' already exists, skipping.")
            conn.rollback() # Rollback the failed Create Type transaction but continue
        
        # 2. Create Users Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role user_role NOT NULL DEFAULT 'TENANT',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. Create Owners Table
        cur.execute("""
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
        """)

        # 4. Create Tenants Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                owner_id UUID REFERENCES owners(id) ON DELETE CASCADE,
                
                -- The Link to the Login Account (Initially NULL until signup)
                user_id UUID REFERENCES users(id) ON DELETE SET NULL, 
                
                -- Tenant Details (Added by Owner)
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone_number VARCHAR(20),
                room_number VARCHAR(20),
                
                -- Status
                onboarding_status VARCHAR(20) DEFAULT 'PENDING',
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure an email can only be added once per owner
                CONSTRAINT uq_tenant_email_owner UNIQUE (owner_id, email)
            );
        """)

        conn.commit()
        print("All tables created successfully!")
        
        # Verify tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Tables in DB:", [t[0] for t in tables])

        cur.close()

    except Exception as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
