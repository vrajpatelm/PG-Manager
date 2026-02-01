import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

def verify_login():
    email_input = "testowner@example.com"
    password_input = "password123"
    
    print(f"Testing Login for: '{email_input}' with password '{password_input}'")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Exact Query used in auth.py
        cur.execute("SELECT id, password_hash, role, email FROM users WHERE email = %s", (email_input,))
        user = cur.fetchone()
        
        if not user:
            print("❌ Query failed to find user.")
            
            # Debug: Check rough match
            cur.execute("SELECT email FROM users WHERE email ILIKE %s", (email_input,))
            fuzzy = cur.fetchone()
            if fuzzy:
                print(f"   But found fuzzy match: '{fuzzy[0]}'")
            else:
                print("   No fuzzy match either.")
                
        else:
            print(f"✅ User Found in DB. ID: {user[0]}")
            print(f"   Stored Email: '{user[3]}'")
            print(f"   Stored Hash: {user[1]}")
            
            # 2. Check Password
            is_valid = check_password_hash(user[1], password_input)
            if is_valid:
                print("✅ Password Check PASSED.")
            else:
                print("❌ Password Check FAILED.")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_login()
