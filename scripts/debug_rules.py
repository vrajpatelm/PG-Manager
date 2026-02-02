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

def debug_rules():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT house_rules FROM properties WHERE owner_id = (SELECT id FROM owners LIMIT 1)")
        row = cur.fetchone()
        
        if row:
            raw_rules = row[0]
            print(f"RAW RULES: {repr(raw_rules)}")
        else:
            print("No rules found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_rules()
