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

def debug_rules_targeted():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get Test Owner ID first
        cur.execute("SELECT id FROM users WHERE email = 'testowner@example.com'")
        user_row = cur.fetchone()
        if not user_row:
            print("User testowner not found")
            return

        cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_row[0],))
        owner_row = cur.fetchone()
        if not owner_row:
             print("Owner profile not found")
             return
        
        owner_id = owner_row[0]
        print(f"Checking rules for Owner ID: {owner_id}")

        cur.execute("SELECT house_rules FROM properties WHERE owner_id = %s", (owner_id,))
        row = cur.fetchone()
        
        if row:
            raw_rules = row[0]
            print(f"RAW RULES: {repr(raw_rules)}")
        else:
            print("No property found for this owner.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_rules_targeted()
