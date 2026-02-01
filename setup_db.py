import os
import psycopg2
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

SCHEMA_DIR = "database_schemas"

def setup_db():
    print(" Starting Database Setup...")
    
    # 1. Connect to Database
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print(f" Connected to database: {DB_CONFIG['dbname']}")
    except Exception as e:
        print(f" Failed to connect to database. Check your .env file.\nError: {e}")
        return

    # 2. Get all SQL files sorted
    sql_files = sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.sql")))
    
    if not sql_files:
        print(f" No schema files found in {SCHEMA_DIR}")
        return

    print(f" Found {len(sql_files)} schema files. Executing...")

    # 3. Execute each file
    success_count = 0
    try:
        for sql_file in sql_files:
            filename = os.path.basename(sql_file)
            print(f"   Executing {filename}...", end=" ", flush=True)
            
            with open(sql_file, 'r') as f:
                sql_script = f.read()
                
            try:
                cur.execute(sql_script)
                conn.commit()
                print(" Done.")
                success_count += 1
            except psycopg2.errors.DuplicateObject:
                conn.rollback()
                print(" Skipped (Already exists).")
            except Exception as e:
                conn.rollback()
                print(f" Failed!\n      Error: {e}")
                # Optional: Stop on error or continue? Usually stop is safer for schema.
                print("      Aborting setup.")
                break
                
        print("-" * 30)
        if success_count == len(sql_files):
            print(f" Database setup completed successfully! ({success_count}/{len(sql_files)} files applied)")
        else:
            print(f" Database setup finished with warnings or errors. ({success_count}/{len(sql_files)} files applied)")

    except Exception as e:
        print(f"\n Critical Error during setup: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    setup_db()
