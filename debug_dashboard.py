import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path='p:/PG-Manager/.env')

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

print(f"Connecting to DB: {DB_CONFIG['dbname']} as {DB_CONFIG['user']}")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("Connection successful.")

    # Test Queries from routes.py
    
    # 1. Total Income
    # Need a valid owner_id. Let's pick one users.
    cur.execute("SELECT id FROM owners LIMIT 1")
    owner_row = cur.fetchone()
    if not owner_row:
        print("No owners found.")
        exit()
    owner_id = owner_row[0]
    print(f"Testing for Owner ID: {owner_id}")

    # Query 1
    cur.execute("SELECT COALESCE(SUM(monthly_rent), 0) FROM tenants WHERE owner_id = %s", (owner_id,))
    print(f"Total Income Query Result: {cur.fetchone()}")

    # Query 2 (Rent Collection - New Code)
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    print(f"Current Month: {current_month}")

    sql = """
            SELECT COUNT(DISTINCT tenant_id), COALESCE(SUM(amount), 0)
            FROM payments
            JOIN tenants ON payments.tenant_id = tenants.id
            WHERE tenants.owner_id = %s AND payment_month = %s
        """
    print("Executing Payment Query...")
    cur.execute(sql, (owner_id, current_month))
    print(f"Payment Query Result: {cur.fetchone()}")
    
    conn.close()
    print("All queries successful.")

except Exception as e:
    print(f"CAUGHT EXCEPTION: {e}")
