import os
import psycopg2
import uuid
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load env variables
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

# Constants
TEST_EMAIL = "testowner@example.com"
PROPERTY_NAME = "Sunshine Residency (Mass)"

NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", 
         "Shaurya", "Atharv", "Neel", "Siddharth", "Shivansh", "Dhruv", "Rohan", "Kabir", "Ansh", "Ravi",
         "Sneha", "Ananya", "Diya", "Priya", "Riya", "Isha", "Nisha", "Kavya", "Meera", "Saanvi",
         "Pooja", "Maya", "Tanvi", "Aditi", "Roshni", "Anjali", "Sima", "Tina", "Zara", "Kiran"]

SURNAMES = ["Patel", "Sharma", "Singh", "Kumar", "Gupta", "Rao", "Reddy", "Nair", "Iyer", "Verma", 
            "Mehta", "Joshi", "Chopra", "Malhotra", "Kapoor", "Khan", "Das", "Bhat", "Saxena", "Yadav",
            "Jain", "Agarwal", "Mishra", "Pandey", "Sinha", "Roy", "Banerjee", "Ghosh", "Dutta", "Nandi",
            "Chatterjee", "Sen", "Bose", "Biswas", "Sarkar", "Chakraborty", "Mukherjee", "Paul", "Ray", "Mandal"]

ACTIVITY_TYPES = ['PAYMENT', 'COMPLAINT', 'TENANT_ADD', 'NOTICE']

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def heavy_seed():
    conn = get_db_connection()
    if not conn: return
    cur = conn.cursor()
    print("🚀 Starting HEAVY Database Seeding...")

    try:
        # 1. Get Owner
        cur.execute("SELECT id FROM users WHERE email = %s", (TEST_EMAIL,))
        user_row = cur.fetchone()
        if not user_row:
            print("❌ User not found. Run seed_data.py first to create the base owner.")
            return
        user_id = user_row[0]
        
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_id,))
        owner_id = cur.fetchone()[0]
        
        # 2. Get Property (or use existing)
        cur.execute("SELECT id FROM properties WHERE owner_id = %s LIMIT 1", (owner_id,))
        prop_id = cur.fetchone()[0]

        # 3. Create 50 Rooms (Floors 1-5, 10 rooms per floor)
        print("🏗️  Building 50 Rooms...")
        room_ids = []
        
        # Cleanup dependencies
        cur.execute("DELETE FROM payments WHERE tenant_id IN (SELECT id FROM tenants WHERE owner_id = %s)", (owner_id,))
        cur.execute("DELETE FROM complaints WHERE owner_id = %s", (owner_id,))
        cur.execute("DELETE FROM notices WHERE owner_id = %s", (owner_id,))
        cur.execute("DELETE FROM activity_logs WHERE owner_id = %s", (owner_id,))
        cur.execute("DELETE FROM tenants WHERE owner_id = %s", (owner_id,)) 
        cur.execute("DELETE FROM rooms WHERE property_id = %s", (prop_id,)) 
        
        for floor in range(1, 6):
            for r in range(1, 11):
                room_num = f"{floor}{r:02d}" # 101, 102... 510
                r_id = str(uuid.uuid4())
                rent = random.choice([6000, 8000, 10000, 12000])
                capacity = random.choice([1, 2, 3])
                
                cur.execute("""
                    INSERT INTO rooms (id, property_id, room_number, floor_number, capacity, rent_amount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (r_id, prop_id, room_num, floor, capacity, rent))
                room_ids.append({'id': r_id, 'num': room_num, 'rent': rent})
        
        # 4. Create 40 Tenants (Mixed Status)
        print("👥  Moving in 40 Tenants...")
        # Status distribution: 30 Active, 5 Notice, 5 Draft
        statuses = ["ACTIVE"] * 30 + ["NOTICE"] * 5 + ["DRAFT"] * 5
        random.shuffle(statuses)
        
        tenant_ids = []
        
        for i, status in enumerate(statuses):
            fname = random.choice(NAMES)
            lname = random.choice(SURNAMES)
            full_name = f"{fname} {lname}"
            email = f"{fname.lower()}.{lname.lower()}{i}@example.com"
            
            # Pick a room
            room = room_ids[i % len(room_ids)]
            
            t_id = str(uuid.uuid4())
            lease_start = datetime.now() - timedelta(days=random.randint(30, 300))
            
            cur.execute("""
                INSERT INTO tenants (id, owner_id, full_name, email, phone_number, room_id, room_number, monthly_rent, onboarding_status, lease_start)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (t_id, owner_id, full_name, email, f"98765{i:05d}", room['id'], room['num'], room['rent'], status, lease_start))
            
            tenant_ids.append({'id': t_id, 'name': full_name, 'rent': room['rent'], 'start': lease_start})
            
            # Log Creation
            log_date = lease_start
            meta = {'room': room['num'], 'metadata': 'blue'}
            cur.execute("""
                INSERT INTO activity_logs (owner_id, event_type, description, metadata, created_at)
                VALUES (%s, 'TENANT_ADD', %s, %s, %s)
            """, (owner_id, f"Added {full_name} to Room {room['num']}", json.dumps(meta), log_date))

        # 5. Generate Payments (Last 6 Months)
        print("💰  Generating Payment History...")
        payment_modes = ['UPI', 'CASH', 'BANK_TRANSFER']
        
        for t in tenant_ids:
            # Generate payments from lease start until now
            current = t['start']
            now = datetime.now()
            
            while current < now:
                # 90% chance of payment on time
                if random.random() > 0.1:
                    pay_date = current + timedelta(days=random.randint(1, 10))
                    if pay_date > now: break
                    
                    amount = t['rent']
                    mode = random.choice(payment_modes)
                    
                    cur.execute("""
                        INSERT INTO payments (tenant_id, amount, payment_date, payment_month, status, payment_mode)
                        VALUES (%s, %s, %s, %s, 'APPROVED', %s)
                    """, (t['id'], amount, pay_date, pay_date.strftime('%Y-%m'), mode))
                    
                    # Log Payment
                    meta = {'amount': amount, 'metadata': 'green'}
                    cur.execute("""
                        INSERT INTO activity_logs (owner_id, event_type, description, metadata, created_at)
                        VALUES (%s, 'PAYMENT', %s, %s, %s)
                    """, (owner_id, f"Received rent from {t['name']}", json.dumps(meta), pay_date))
                
                # Move to next month safely
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)

        # 6. Generate Complaints
        print("⚠️  Generating Complaints...")
        issues = ["Leaky tap", "Internet slow", "Power cut", "Broken chair", "Window jammed", "No water", "AC not cooling"]
        
        for _ in range(20):
            t = random.choice(tenant_ids)
            issue = random.choice(issues)
            status = random.choice(['PENDING', 'RESOLVED', 'IN_PROGRESS'])
            prio = random.choice(['LOW', 'MEDIUM', 'HIGH'])
            c_date = datetime.now() - timedelta(days=random.randint(1, 60))
            
            cur.execute("""
                INSERT INTO complaints (tenant_id, owner_id, title, description, status, priority, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (t['id'], owner_id, issue, f"{issue} issue in room.", status, prio, c_date))
            
            # Log Complaint
            meta = {'status': status, 'metadata': 'red'}
            cur.execute("""
                INSERT INTO activity_logs (owner_id, event_type, description, metadata, created_at)
                VALUES (%s, 'COMPLAINT', %s, %s, %s)
            """, (owner_id, f"Complaint: {issue} ({t['name']})", json.dumps(meta), c_date))

        conn.commit()
        print("\n✅ MASSIVE DATA SEED COMPLETE!")
        print(f"Created 50 Rooms, 40 Tenants, ~{len(tenant_ids)*5} Payments.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    heavy_seed()
