import pytest
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import glob
from app import create_app
from app.database.database import get_db_connection

# Use a separate test database
TEST_DB_NAME = "pg_manager_test"

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    os.environ['DB_NAME'] = TEST_DB_NAME
    os.environ['FLASK_ENV'] = 'testing'
    
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    return app

@pytest.fixture(scope='session')
def client(app):
    """A test client for the app session."""
    return app.test_client()

@pytest.fixture(scope='session')
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture(scope='session')
def live_server(app):
    """Run the Flask app in a background thread."""
    import threading
    from werkzeug.serving import make_server
    
    # Use a random port or fixed port
    port = 5001
    server = make_server('127.0.0.1', port, app)
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    yield f"http://127.0.0.1:{port}"
    
    server.shutdown()
    thread.join()

@pytest.fixture(scope='session', autouse=True)
def init_database(app):
    """Setup the test database and run all migrations once per session."""
    
    # 1. Create Database
    default_db = "postgres"
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    
    try:
        conn = psycopg2.connect(dbname=default_db, user=user, password=password, host=host)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Always Drop and Recreate for a clean session migration run
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME};")
        cur.execute(f"CREATE DATABASE {TEST_DB_NAME};")
        
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Primary Test DB Setup Failed: {e}")

    # 2. Run Migrations
    conn = get_db_connection()
    cur = conn.cursor()
    
    migrations_dir = os.path.join(app.root_path, 'database', 'migrations')
    sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    
    for sql_file in sql_files:
        with open(sql_file, 'r') as f:
            try:
                cur.execute(f.read())
            except Exception as e:
                print(f"Error in migration {os.path.basename(sql_file)}: {e}")
                conn.rollback()
                pytest.fail(f"Migration Failed: {os.path.basename(sql_file)}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    yield

@pytest.fixture(autouse=True)
def clean_database():
    """Truncate tables after each test to ensure isolation."""
    yield
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # List of tables to truncate in order (respecting FKs if possible, or use CASCADE)
    tables = [
        "activity_logs", "notices", "complaints", "expenses", 
        "payments", "tenants", "rooms", "properties", 
        "owners", "users", "otp_verifications"
    ]
    
    try:
        cur.execute(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;")
        conn.commit()
    except Exception as e:
        print(f"Cleanup Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

@pytest.fixture
def auth_owner(client):
    """Fixture to create and log in an owner."""
    email = "testowner@example.com"
    name = "Test Owner"
    
    # 1. Request OTP
    client.post('/auth/send-otp', json={'email': email})
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_code FROM otp_verifications WHERE email = %s", (email,))
    otp = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    client.post('/signup', data={
        'name': name,
        'email': email,
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'OWNER',
        'otp': otp
    }, follow_redirects=True)
    
    return client
