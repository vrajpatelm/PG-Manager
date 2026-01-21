from app.database.database import get_db_connection
from datetime import datetime
import uuid

def debug_insert():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get a tenant
        cur.execute("SELECT id, full_name FROM tenants LIMIT 1")
        tenant = cur.fetchone()
        if not tenant:
            print("No tenants found")
            return
            
        tenant_id = tenant[0]
        print(f"Attempting insert for tenant: {tenant[1]} ({tenant_id})")
        
        # Data
        amount = 5000
        payment_date = datetime.now()
        payment_month = payment_date.strftime('%Y-%m')
        mode = 'CASH'
        remarks = 'Debug Insert'
        
        # INSERT
        print("Executing INSERT...")
        cur.execute("""
            INSERT INTO payments (tenant_id, amount, payment_date, payment_month, status, payment_mode, remarks)
            VALUES (%s, %s, %s, %s, 'COMPLETED', %s, %s)
        """, (tenant_id, amount, payment_date, payment_month, mode, remarks))
        
        print("Insert Successful (Rolling back)")
        conn.rollback()
        
    except Exception as e:
        print("\n!!! INSERT FAILED !!!")
        print(f"Error Type: {type(e)}")
        print(f"Error Details: {e}")
        # Identify constraint if possible
        if hasattr(e, 'pgcode'):
            print(f"PG Code: {e.pgcode}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    debug_insert()
