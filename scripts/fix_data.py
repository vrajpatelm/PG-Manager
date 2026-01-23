import psycopg2
import os

# Database connection parameters (Using default local settings which usually work for dev)
DB_HOST = "localhost"
DB_NAME = "pg_manager"
DB_USER = "postgres"
DB_PASS = "1234"

def fix_tenant_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        
        # Update the specific tenant (Assuming it's the most recent one or doing a broad update for NULLs)
        # Setting Bed Number to 'D' and Lease Start to Today for tenants where it is NULL
        
        print("Updating missing Bed Number and Lease Start...")
        
        cur.execute("""
            UPDATE tenants 
            SET bed_number = 'D', lease_start = CURRENT_DATE
            WHERE bed_number IS NULL OR lease_start IS NULL
        """)
        
        updated_rows = cur.rowcount
        conn.commit()
        print(f"Updated {updated_rows} tenant records.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_tenant_data()
