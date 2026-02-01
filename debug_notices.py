from app.database.database import get_db_connection

def debug():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return
    
    cur = conn.cursor()
    
    print("\n--- USERS ---")
    cur.execute("SELECT id, email, role FROM users")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- OWNERS ---")
    cur.execute("SELECT id, user_id, full_name FROM owners")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- TENANTS ---")
    cur.execute("SELECT id, user_id, owner_id, full_name FROM tenants")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- NOTICES ---")
    cur.execute("SELECT id, owner_id, title FROM notices")
    for row in cur.fetchall():
        print(row)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug()
