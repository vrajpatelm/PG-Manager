import os
from dotenv import load_dotenv
import psycopg2
from werkzeug.security import generate_password_hash
import traceback

# Load env from app/.env if it exists, or local .env
load_dotenv(os.path.join("app", ".env"))
load_dotenv() # Fallback

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

def reproduce():
    print("Connecting to DB...")
    print(f"Config: {DB_CONFIG}")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("Connected.")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    email = "debug_user_123@example.com"
    password = "password123"
    name = "Debug User"
    role = "OWNER" # Testing flow
    hashed_pw = generate_password_hash(password)

    try:
        # Check email
        print(f"Checking email {email}...")
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            print("Email already exists. Deleting for reproduction...")
            # Delete from owners first due to FK
            cur.execute("DELETE FROM owners WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (email,))
            cur.execute("DELETE FROM users WHERE email = %s", (email,))
            conn.commit()
            print("Deleted.")
        
        print("Attempting INSERT into users...")
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'OWNER') RETURNING id",
            (email, hashed_pw)
        )
        user_id = cur.fetchone()[0]
        print(f"User inserted with ID: {user_id}")

        print("Attempting INSERT into owners...")
        cur.execute("INSERT INTO owners (user_id, full_name) VALUES (%s, %s)", (user_id, name))
        print("Owner inserted.")
        
        conn.commit() 
        print("Transaction Committed. Signup seems successful logic-wise.")
        
        # Cleanup
        print("Cleaning up...")
        cur.execute("DELETE FROM owners WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit() 
        print("Cleaned up.")

    except Exception as e:
        print("\n!!! CAUGHT EXCEPTION !!!")
        print(e)
        traceback.print_exc()
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    reproduce()
