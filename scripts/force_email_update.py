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

def force_update():
    log_file = 'email_update_log.txt'
    with open(log_file, 'w', encoding='utf-8') as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            old_email = 'testowner@example.com'
            new_email = 'dhruvharani8@gmail.com'
            
            log(f"Starting Email Update Diagnostics...")
            log(f"Target: {old_email} -> {new_email}")
            
            # 1. Check existing records
            cur.execute("SELECT id FROM users WHERE email = %s", (old_email,))
            old_user = cur.fetchone()
            log(f"Old User Exists: {bool(old_user)} (ID: {old_user[0] if old_user else 'N/A'})")
            
            cur.execute("SELECT id FROM users WHERE email = %s", (new_email,))
            new_user = cur.fetchone()
            log(f"New User Already Exists: {bool(new_user)} (ID: {new_user[0] if new_user else 'N/A'})")
            
            if new_user:
                log("⚠️ CONFLICT DETECTED: Target email already in use.")
                # Strategy: If the new user has no rigorous data, maybe delete it?
                # For safety, let's just reporting this for now unless instructed otherwise.
                # Actually, user want to CHANGE the email. If the email exists, they might have created a dup account.
                log("ABORTING update to avoid data corruption. Please delete the existing account for 'dhruvharani8@gmail.com' first if it is empty.")
            
            elif old_user:
                log("✅ No conflict. Proceeding with UPDATE.")
                
                # Update Users
                cur.execute("UPDATE users SET email = %s WHERE email = %s", (new_email, old_email))
                log(f"Updated 'users' table. Rows affected: {cur.rowcount}")
                
                # Update Tenants (if applicable)
                cur.execute("UPDATE tenants SET email = %s WHERE email = %s", (new_email, old_email))
                log(f"Updated 'tenants' table. Rows affected: {cur.rowcount}")
                
                conn.commit()
                log("✅ Update COMMITTED successfully.")
            else:
                log("❌ Source user 'testowner@example.com' NOT FOUND. Nothing to update.")

            cur.close()
            conn.close()
        except Exception as e:
            log(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    force_update()
