import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

SQL = """
CREATE TABLE IF NOT EXISTS otp_verifications (
    email VARCHAR(255) PRIMARY KEY,
    otp_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Index for cleanup
CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_verifications(expires_at);
"""

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432"))
    )
    cur = conn.cursor()
    cur.execute(SQL)
    conn.commit()
    print("Successfully created otp_verifications table.")
except Exception as e:
    print(f"Error creating table: {e}")
finally:
    if 'conn' in locals() and conn: conn.close()
