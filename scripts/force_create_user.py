import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

def force_reset_user():
    email = "testowner@example.com"
    password = "password123"
    
    print(f"🔄 Resetting user: {email}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Delete if exists
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        print(f"   Deleted existing user (if any).")
        
        # 2. Insert new
        pw_hash = generate_password_hash(password)
        cur.execute("""
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, 'OWNER')
            RETURNING id
        """, (email, pw_hash))
        
        user_id = cur.fetchone()[0]
        print(f"✅ User Created with ID: {user_id}")
        
        conn.commit()
        print("   Transaction Committed.")
        
        # 3. Verify immediately
        cur.execute("SELECT email, password_hash FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            print(f"🔍 Verification: User found: {row[0]}")
        else:
            print("❌ Verification FAILED: User not found after commit!")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_reset_user()
