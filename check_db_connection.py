import psycopg2
import os
from dotenv import load_dotenv

def check_connection():
    print("--- Testing Database Connection ---")
    # Reload .env to get the new Supabase values you just pasted
    load_dotenv(override=True) 
    
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    dbname = os.getenv("DB_NAME")
    
    print(f"Target: {user}@{host}/{dbname}")
    
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=os.getenv("DB_PASSWORD"),
            host=host,
            port=int(os.getenv("DB_PORT", "5432")),
            connect_timeout=10
        )
        print("✅ SUCCESS! Connected to Supabase successfully.")
        conn.close()
        return True
    except Exception as e:
        print("❌ FAILED. Could not connect.")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_connection()
