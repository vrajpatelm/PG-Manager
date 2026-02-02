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

def verify_email():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        emails_to_check = ['testowner@example.com', 'dhruvharani8@gmail.com']
        
        with open('verification_result.txt', 'w', encoding='utf-8') as f:
            f.write("DATABASE STATE VERIFICATION\n===========================\n\n")
            
            for email in emails_to_check:
                f.write(f"Checking for: {email}\n")
                # Check Users
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if user:
                    f.write(f"  [FOUND] in 'users' table: ID={user[0]}\n")
                else:
                     f.write(f"  [MISSING] in 'users' table\n")
                     
                # Check Owners
                cur.execute("SELECT id FROM owners WHERE email = %s", (email,))
                owner = cur.fetchone()
                if owner:
                    f.write(f"  [FOUND] in 'owners' table: ID={owner[0]}\n")
                else:
                     f.write(f"  [MISSING] in 'owners' table\n")
                f.write("-" * 20 + "\n")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_email()
