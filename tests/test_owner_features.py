import pytest
from app.database.database import get_db_connection

def test_owner_dashboard_access(auth_owner):
    """Verify owner can access dashboard."""
    response = auth_owner.get('/owner/dashboard')
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Income" in response.data

def test_add_room(auth_owner):
    """Test adding a room to property."""
    response = auth_owner.post('/owner/properties/add-room', data={
        'room_number': '101',
        'floor': '1',
        'capacity': '2',
        'rent_amount': '5000'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Room added successfully" in response.data
    
    # Verify in DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM rooms WHERE room_number = '101'")
    assert cur.fetchone() is not None
    cur.close()
    conn.close()

def test_add_tenant(auth_owner):
    """Test adding a tenant (Draft mode)."""
    # Note: Room must exist first
    auth_owner.post('/owner/properties/add-room', data={
        'room_number': '102',
        'floor': '1',
        'capacity': '2',
        'rent_amount': '6000'
    })

    response = auth_owner.post('/owner/add-tenant', data={
        'full_name': 'John Doe',
        'email': 'john@example.com',
        'phone': '1234567890',
        'room_no': '102',
        'rent': '6000',
        'bed_no': '1',
        'move_in_date': '2026-02-01',
        'action': 'draft'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Tenant details saved as Draft" in response.data
    
    # Verify in DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tenants WHERE email = 'john@example.com' AND onboarding_status = 'DRAFT'")
    assert cur.fetchone() is not None
    cur.close()
    conn.close()

def test_add_expense(auth_owner):
    """Test adding an expense."""
    response = auth_owner.post('/owner/add-expense', data={
        'category': 'Maintenance',
        'amount': '1500',
        'expense_date': '2026-02-02',
        'description': 'Broken tap repair'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Expense added" in response.data
    
    # Verify in DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM expenses WHERE amount = 1500")
    assert cur.fetchone() is not None
    cur.close()
    conn.close()

def test_tenant_details_access(auth_owner):
    """Test accessing individual tenant details page."""
    # 1. Setup Tenant
    auth_owner.post('/owner/properties/add-room', data={'room_number': '103', 'floor': '1', 'capacity': '1', 'rent_amount': '7000'})
    auth_owner.post('/owner/add-tenant', data={
        'full_name': 'Jane Smit', 'email': 'jane@example.com', 'phone': '9876543210',
        'room_no': '103', 'rent': '7000', 'bed_no': '1', 'action': 'pending'
    })
    
    # 2. Get ID
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tenants WHERE email = 'jane@example.com'")
    tenant_id = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    # 3. Access Page
    response = auth_owner.get(f'/owner/tenants/{tenant_id}')
    assert response.status_code == 200
    # Note: Currently owner_tenant_details just renders tenant_details.html with tenant_id
    # We should verify it contains the ID or some tenant info if the template renders it.
