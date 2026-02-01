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

def fix_activity_feed():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🛠️ Creating 'activity_logs' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                owner_id UUID REFERENCES owners(id) ON DELETE CASCADE,
                event_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_activity_logs_owner_date ON activity_logs(owner_id, created_at DESC);
        """)
        conn.commit()
        print("✅ Table created.")
        
        print("🌱 Seeding Activity Logs...")
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
        
        # Clear existing logs
        cur.execute("DELETE FROM activity_logs WHERE owner_id = %s", (owner_id,))
        
        logs = [
            ('PAYMENT', 'Verified payment of ₹8500 from Aarav Patel', {'amount': 8500, 'metadata': 'green'}, 2),
            ('TENANT_ADD', 'Added new tenant Sneha Gupta to Room 104', {'room': '104', 'metadata': 'blue'}, 5),
            ('NOTICE', 'Posted notice: Gym Maintenance Shut Down', {'priority': 'HIGH', 'metadata': 'purple'}, 24),
            ('COMPLAINT', 'Complaint Update: Leaky Tap resolved', {'status': 'RESOLVED', 'metadata': 'red'}, 48),
            ('PAYMENT', 'Verified payment of ₹6000 from Rahul Kumar', {'amount': 6000, 'metadata': 'green'}, 50)
        ]
        
        for event_type, desc, meta, hours_ago in logs:
            created_at = datetime.now() - timedelta(hours=hours_ago)
            cur.execute("""
                INSERT INTO activity_logs (owner_id, event_type, description, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (owner_id, event_type, desc, json.dumps(meta), created_at))
            
        conn.commit()
        print("✅ Seeded 5 logs successfully.")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_activity_feed()
