from app.database.database import get_db_connection

def check_tables():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect")
        return

    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print("Tables found:", [t[0] for t in tables])
    
    # Check payments columns if table exists
    if 'payments' in [t[0] for t in tables]:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'payments'")
        columns = cur.fetchall()
        print("Payments Columns:", columns)
    else:
        print("Payments table MISSING")

    conn.close()

if __name__ == "__main__":
    check_tables()
