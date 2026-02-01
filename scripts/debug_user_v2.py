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

def list_users():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("--- DATABASE USERS ---")
        cur.execute("SELECT email, role FROM users")
        rows = cur.fetchall()
        
        found = False
        target = "testowner@example.com"
        
        for r in rows:
            email = r[0]
            role = r[1]
            print(f"User: '{email}' | Role: {role}")
            
            if email == target:
                found = True
        
        print("----------------------")
        if found:
            print(f"✅ EXACT MATCH FOUND for '{target}'")
        else:
            print(f"❌ NO EXACT MATCH for '{target}'")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_users()
