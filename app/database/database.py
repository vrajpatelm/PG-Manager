import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Returns a dynamic DB connection based on current environment variables."""
    config = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
    }
    try:
        conn = psycopg2.connect(**config)
        return conn
    except OperationalError as e:
        print(f"DB connection error: {e}")
        return None
