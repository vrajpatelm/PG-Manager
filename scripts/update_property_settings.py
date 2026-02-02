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

def update_settings():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get Test Owner
        cur.execute("SELECT id FROM users WHERE email = %s", ('testowner@example.com',))
        user_row = cur.fetchone()
        if not user_row:
            print("Test user not found")
            return
            
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_row[0],))
        owner_id = cur.fetchone()[0]
        
        # Update Property
        print(f"Updating settings for Owner: {owner_id}")
        
        cur.execute("""
            UPDATE properties 
            SET wifi_ssid = 'Sunshine_5G_Guest',
                wifi_password = 'securepassword2024',
                gate_closing_time = '22:30:00',
                breakfast_start_time = '07:30:00',
                breakfast_end_time = '10:00:00',
                house_rules = '''1. No loud music after 10 PM.
2. Guests allowed only in lobby.
3. Keep room clean.'''
            WHERE owner_id = %s
        """, (owner_id,))
        
        conn.commit()
        print("✅ Property Settings Updated!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_settings()
