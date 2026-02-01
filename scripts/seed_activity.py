import os
import psycopg2
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

def seed_activity():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get Test Owner
        cur.execute("SELECT id FROM users WHERE email = 'testowner@example.com'")
        row = cur.fetchone()
        if not row:
            print("Test owner not found.")
            return
            
        # Get Owner ID from owner table
        user_id = row[0]
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_id,))
        owner_id = cur.fetchone()[0]
        
        print(f"Seeding activity for Owner ID: {owner_id}")
        
        # Clear existing logs
        cur.execute("DELETE FROM activity_logs WHERE owner_id = %s", (owner_id,))
        
        logs = [
            ('PAYMENT', 'Verified payment of ₹8500 from Aarav Patel', {'amount': 8500}, 2), # 2 hours ago
            ('TENANT_ADD', 'Added new tenant Sneha Gupta to Room 104', {'room': '104'}, 5),
            ('NOTICE', 'Posted notice: Gym Maintenance Shut Down', {'priority': 'HIGH'}, 24),
            ('COMPLAINT', 'Complaint Update: Leaky Tap resolved', {'status': 'RESOLVED'}, 48),
            ('PAYMENT', 'Verified payment of ₹6000 from Rahul Kumar', {'amount': 6000}, 50)
        ]
        
        for event_type, desc, meta, hours_ago in logs:
            created_at = datetime.now() - timedelta(hours=hours_ago)
            cur.execute("""
                INSERT INTO activity_logs (owner_id, event_type, description, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (owner_id, event_type, desc, json.dumps(meta), created_at))
            
        conn.commit()
        print("✅ seeded 5 activity logs.")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    seed_activity()
