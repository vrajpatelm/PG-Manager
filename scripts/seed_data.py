import os
import psycopg2
import uuid
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load env variables including DB credentials
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

# constants
TEST_EMAIL = "testowner@example.com"
TEST_PASSWORD = "password123"
PROPERTY_NAME = "Sunshine Residency"

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def seed_data():
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    print("🌱 Starting Database Seeding...")

    try:
        # 1. Create/Get User
        print(f"Creating User: {TEST_EMAIL}...")
        cur.execute("SELECT id FROM users WHERE email = %s", (TEST_EMAIL,))
        user_row = cur.fetchone()
        
        if not user_row:
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(TEST_PASSWORD)
            cur.execute("""
                INSERT INTO users (id, email, password_hash, role)
                VALUES (%s, %s, %s, 'OWNER')
            """, (user_id, TEST_EMAIL, password_hash))
            print(" [OK] User created.")
        else:
            user_id = user_row[0]
            print(" [SKIP] User already exists.")

        # 2. Create/Get Owner Profile
        print("Creating Owner Profile...")
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_id,))
        owner_row = cur.fetchone()
        
        if not owner_row:
            owner_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO owners (id, user_id, full_name, business_name, phone_number, upi_id)
                VALUES (%s, %s, 'Test Owner', %s, '9876543210', 'testowner@upi')
            """, (owner_id, user_id, PROPERTY_NAME))
            print(" [OK] Owner profile created.")
        else:
            owner_id = owner_row[0]
            print(" [SKIP] Owner profile exists.")

        # 3. Create Property
        print("Creating Property...")
        cur.execute("SELECT id FROM properties WHERE owner_id = %s AND name = %s", (owner_id, PROPERTY_NAME))
        prop_row = cur.fetchone()
        
        if not prop_row:
            prop_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO properties (id, owner_id, name, address)
                VALUES (%s, %s, %s, '123 Baker Street, Tech City')
            """, (prop_id, owner_id, PROPERTY_NAME))
            print(" [OK] Property created.")
        else:
            prop_id = prop_row[0]
            print(" [SKIP] Property exists.")

        # 4. Create Rooms (101-110)
        print("Creating Rooms...")
        room_ids = []
        for i in range(1, 11):
            room_num = f"10{i}" if i < 10 else f"1{i}" # 101 to 109, then 110? No wait. 101...110.
            if i == 10: room_num = "110"
            else: room_num = f"10{i}"

            cur.execute("SELECT id FROM rooms WHERE property_id = %s AND room_number = %s", (prop_id, room_num))
            r_row = cur.fetchone()
            
            if not r_row:
                r_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO rooms (id, property_id, room_number, floor_number, capacity, rent_amount)
                    VALUES (%s, %s, %s, 1, 2, 8000)
                """, (r_id, prop_id, room_num))
                room_ids.append(r_id)
            else:
                room_ids.append(r_row[0])
        print(f" [OK] {len(room_ids)} rooms ready.")

        # 5. Create Tenants
        print("Creating Tenants & Payments...")
        names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan"]
        surnames = ["Patel", "Sharma", "Singh", "Kumar", "Gupta", "Rao", "Reddy", "Nair", "Iyer", "Verma"]
        
        # We'll create tenants for first 8 rooms (16 beds capacity, but lets fill some single, some double)
        # 5 Active Paid, 3 Active Pending, 2 Draft
        
        tenant_configs = [
            ("ACTIVE", "PAID"), ("ACTIVE", "PAID"), ("ACTIVE", "PAID"), ("ACTIVE", "PAID"), ("ACTIVE", "PAID"),
            ("ACTIVE", "PENDING"), ("ACTIVE", "PENDING"), ("ACTIVE", "PENDING"),
            ("DRAFT", "NONE"), ("DRAFT", "NONE")
        ]
        
        for idx, (status, payment_status) in enumerate(tenant_configs):
            full_name = f"{names[idx]} {surnames[idx]}"
            email = f"{names[idx].lower()}.{surnames[idx].lower()}@test.com"
            room_id = room_ids[idx] # Use 1 room per tenant for simplicity
            
            cur.execute("SELECT id FROM tenants WHERE owner_id = %s AND email = %s", (owner_id, email))
            t_row = cur.fetchone()
            
            if not t_row:
                t_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tenants (id, owner_id, full_name, email, phone_number, room_id, room_number, monthly_rent, onboarding_status, lease_start)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 8000, %s, CURRENT_DATE)
                """, (t_id, owner_id, full_name, email, f"900000000{idx}", room_id, f"10{idx+1}" if idx < 9 else "110", status))
                
                # Add Payment if needed
                if status == "ACTIVE":
                    if payment_status == "PAID":
                        cur.execute("""
                            INSERT INTO payments (tenant_id, amount, payment_date, payment_month, status, payment_mode)
                            VALUES (%s, 8000, CURRENT_DATE, TO_CHAR(CURRENT_DATE, 'YYYY-MM'), 'APPROVED', 'UPI')
                        """, (t_id,))
                    # For Pending, we assume no record exists for this month, usually. Or a PENDING record.
                    # Let's verify logic: remind all checks for *no approved payment*.
                
                # Add a random complaint for some
                if idx % 3 == 0:
                    cur.execute("""
                        INSERT INTO complaints (tenant_id, owner_id, title, description, status, priority)
                        VALUES (%s, %s, 'Fan not working', 'Ceiling fan making noise', 'PENDING', 'MEDIUM')
                    """, (t_id, owner_id))

            print(f"   Processed {full_name} ({status})")

        # 6. Notices
        print("Creating Notices...")
        cur.execute("SELECT COUNT(*) FROM notices WHERE owner_id = %s", (owner_id,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO notices (owner_id, title, description, priority)
                VALUES 
                (%s, 'Welcome to Sunshine Residency', 'We are happy to have you here. Please follow house rules.', 'LOW'),
                (%s, 'Maintenance Work', 'Plumbing work scheduled for Sunday.', 'MEDIUM')
            """, (owner_id, owner_id))
            print(" [OK] Notices added.")
        
        # 7. Expenses
        print("Creating Expenses...")
        cur.execute("SELECT COUNT(*) FROM expenses WHERE owner_id = %s", (owner_id,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO expenses (owner_id, amount, category, description, expense_date, expense_month)
                VALUES 
                (%s, 1500, 'UTILITIES', 'Electricity Bill', CURRENT_DATE, TO_CHAR(CURRENT_DATE, 'YYYY-MM')),
                (%s, 500, 'MAINTENANCE', 'Cleaning supplies', CURRENT_DATE, TO_CHAR(CURRENT_DATE, 'YYYY-MM'))
            """, (owner_id, owner_id))
            print(" [OK] Expenses added.")

        conn.commit()
        print("\n✅ Database Seeded Successfully!")
        print(f"👉 Login with: {TEST_EMAIL} / {TEST_PASSWORD}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error seeding data: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_data()
