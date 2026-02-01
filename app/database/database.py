import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "sslmode": "require" if os.getenv("DB_HOST") != "localhost" else "prefer"
}

from psycopg2 import pool

# Create a global connection pool
# Min=1, Max=10. In serverless, this pool usually persists for the warm instance.
try:
    connection_pool = pool.SimpleConnectionPool(
        1,  # minconn
        10, # maxconn
        **DB_CONFIG
    )
    print("Database connection pool created.")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

class PooledConnection:
    """
    Wraps a psycopg2 connection to return it to the pool on close()
    instead of actually closing it.
    """
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn

    def close(self):
        if self._conn:
            self._pool.putconn(self._conn)
            self._conn = None

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)

def get_db_connection():
    try:
        if connection_pool:
            # Get a connection from the pool
            conn = connection_pool.getconn()
            if conn:
                return PooledConnection(connection_pool, conn)
        
        # Fallback if pool failed
        return psycopg2.connect(**DB_CONFIG)
        
    except OperationalError as e:
        print(f"❌ DB CONNECTION ERROR: {e}")
        return None
    except Exception as e:
        print(f"❌ GENERAL DB ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
