import psycopg2
import os

# Database connection parameters
DB_HOST = "localhost"
DB_NAME = "pg_manager"
DB_USER = "postgres"
DB_PASS = "1234"

def debug_tenant_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()

        print("\n--- Debugging Tenant Data ---")
        
        # 1. List all tenants with relevant columns
        print("\nAll Tenants:")
        cur.execute("""
            SELECT id, full_name, email, bed_number, lease_start, room_number, created_at 
            FROM tenants
        """)
        tenants = cur.fetchall()
        
        for t in tenants:
            print(f"ID: {t[0]}")
            print(f"Name: {t[1]}")
            print(f"Email: {t[2]}")
            print(f"Bed Number: '{t[3]}'")  # Quotes to see empty strings
            print(f"Lease Start: {t[4]}")
            print(f"Room Number: {t[5]}")
            print(f"Created At: {t[6]}")
            print("-" * 30)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_tenant_data()
