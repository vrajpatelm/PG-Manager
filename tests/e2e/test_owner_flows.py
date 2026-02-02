import pytest
from playwright.sync_api import expect
from app.database.database import get_db_connection

def test_owner_login_and_dashboard(page, live_server, init_database):
    """E2E Test: Owner Login and Dashboard navigation."""
    
    # 1. Setup User (Backend)
    # We can't skip UI signup if we want true E2E, but for speed we can insert user
    # Actually, let's do the UI signup flow! It tests everything.
    
    email = "e2e_owner@example.com"
    name = "E2E Owner"
    
    # Go to Signup
    page.goto(f"{live_server}/signup")
    
    # Select Role
    page.click('h3:has-text("PG Owner")')
    
    # Fill details
    page.fill('#name', name)
    page.fill('#email', email)
    page.fill('#password', "password123")
    page.fill('#confirm_password', "password123")
    
    # Request OTP
    page.click('button:has-text("Get Verification Code")')
    
    # Get OTP from DB
    import time
    time.sleep(1) # Wait for processing
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_code FROM otp_verifications WHERE email = %s", (email,))
    otp = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    # Fill OTP and Submit
    page.fill('#otp', otp)
    page.click('button:has-text("Verify & Create Account")')
    
    # Should be redirected to Dashboard
    expect(page).to_have_url(f"{live_server}/owner/dashboard")
    expect(page.locator('h1')).to_contain_text("Dashboard")
    
    # Verify Sidebar links
    expect(page.locator('aside')).to_contain_text("Properties")
    expect(page.locator('aside')).to_contain_text("Tenants")
    
    # Navigate to Properties
    page.click('a:has-text("Properties")')
    expect(page).to_have_url(f"{live_server}/owner/properties")
    expect(page.locator('h1')).to_contain_text("My Properties")

def test_add_room_ui(auth_owner_e2e, live_server):
    """E2E Test: Adding a room via UI."""
    page = auth_owner_e2e
    
    # 1. Go to Properties
    page.click('a:has-text("Properties")')
    expect(page).to_have_url(f"{live_server}/owner/properties")
    
    # 2. Open Add Room Modal
    page.click('button:has-text("Add Room")')
    
    # 3. Fill Modal
    page.fill('#room_number', '303')
    page.fill('#floor', '3')
    page.fill('#capacity', '2')
    page.fill('#rent_amount', '5500')
    
    # 4. Submit
    page.click('#save-room-btn')
    
    # 5. Verify Flash message and UI update
    expect(page.locator('body')).to_contain_text("Room added successfully")
    expect(page.locator('table')).to_contain_text("303")

@pytest.fixture
def auth_owner_e2e(page, live_server, init_database):
    """Reusable fixture to login for E2E tests."""
    email = "e2e_auth@example.com"
    name = "Auth E2E"
    
    # 1. Signup flow
    page.goto(f"{live_server}/signup")
    
    # Select Role
    page.click('h3:has-text("PG Owner")')
    
    # Fill details
    page.fill('#name', name)
    page.fill('#email', email)
    page.fill('#password', "pass123")
    page.fill('#confirm_password', "pass123")
    
    # Request OTP
    page.click('button:has-text("Get Verification Code")')
    
    # Get OTP from DB
    import time
    time.sleep(1)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_code FROM otp_verifications WHERE email = %s", (email,))
    otp = cur.fetchone()[0]
    cur.close(); conn.close()
    
    # Fill OTP and Submit
    page.fill('#otp', otp)
    page.click('button:has-text("Verify & Create Account")')
    
    return page
