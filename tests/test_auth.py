from app.database.database import get_db_connection

def test_login_page_access(client):
    """Test that login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Sign In" in response.data  # Matches button text

def test_signup_page_access(client):
    """Test that signup page loads successfully."""
    response = client.get('/signup')
    assert response.status_code == 200
    assert b"Sign Up" in response.data

def test_signup_logic(client, init_database):
    """Test creating a new user with OTP flow."""
    email = "testowner@example.com"
    
    # 1. Request OTP
    client.post('/auth/send-otp', json={'email': email})
    
    # 2. Get OTP from Test DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_code FROM otp_verifications WHERE email = %s", (email,))
    otp = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    # 3. Complete Signup
    response = client.post('/signup', data={
        'name': 'Test Owner',
        'email': email,
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'OWNER',
        'otp': otp
    }, follow_redirects=True)
    
    # After successful owner signup, it redirects to dashboard
    assert response.status_code == 200
    assert b"Dashboard" in response.data
