import json
from app.database.database import get_db_connection

def log_activity(owner_id, event_type, description, metadata=None):
    """
    Logs an event to the activity_logs table.
    
    Args:
        owner_id (str): UUID of the owner
        event_type (str): Category (PAYMENT, COMPLAINT, NEW_TENANT, NOTICE, SYSTEM)
        description (str): Human readable text
        metadata (dict, optional): Extra data like ids for linking. Defaults to {}.
    """
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB for logging activity")
        return

    try:
        cur = conn.cursor()
        if metadata is None:
            metadata = {}
            
        cur.execute("""
            INSERT INTO activity_logs (owner_id, event_type, description, metadata)
            VALUES (%s, %s, %s, %s)
        """, (owner_id, event_type, description, json.dumps(metadata)))
        
        conn.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
    finally:
        if conn: conn.close()
