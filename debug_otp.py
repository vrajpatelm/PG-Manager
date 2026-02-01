import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Check Table
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432"))
    )
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM otp_verifications")
    print(f"Table otp_verifications exists. Count: {cur.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"Database Error: {e}")

# 2. Test Endpoint
try:
    resp = requests.post(
        "http://127.0.0.1:5000/auth/send-otp", 
        json={"email": "debug_test@example.com"}
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Request Error: {e}")
