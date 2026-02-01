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

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT email FROM users")
emails = [r[0] for r in cur.fetchall()]
print(emails)
conn.close()
