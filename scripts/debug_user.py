import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

def check_user():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        email = "TestOwner@example.com"
        print(f"Checking for user: {email} (Mixed Case)")
        
        cur.execute("SELECT id, email, role, password_hash FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user:
            print(f"✅ User FOUND: ID={user[0]}, Role={user[2]}")
            print(f"   Hash starts with: {user[3][:10]}...")
        else:
            print("❌ User NOT FOUND in 'users' table.")
            
            # List all users
            print("Listing all users:")
            cur.execute("SELECT email FROM users")
            rows = cur.fetchall()
            for r in rows:
                print(f" - {r[0]}")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_user()
