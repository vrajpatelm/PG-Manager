
import os
from flask import Blueprint, jsonify, redirect, render_template, request, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.database import get_db_connection

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    if 'user_id' in session:
        if session.get('role') == 'OWNER':
            return redirect(url_for('main.owner_dashboard'))
        else:
             # Placeholder for Tenant Dashboard
            return render_template("index.html") # Temp
            
    return render_template("index.html")


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('login.html')
            
        cur = conn.cursor()
        try:
            # Check User
            cur.execute("SELECT id, password_hash, role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if not user:
                flash('User does not exist. Please Sign Up first.', 'error')
                return render_template('login.html')
            
            if not check_password_hash(user[1], password):
                flash('Incorrect password. Please try again.', 'error')
                return render_template('login.html')

            # Login Success
            session['user_id'] = user[0]
            session['role'] = user[2]
            
            # Get Name
            if user[2] == 'OWNER':
                    cur.execute("SELECT full_name FROM owners WHERE user_id = %s", (user[0],))
                    owner = cur.fetchone()
                    if owner: session['name'] = owner[0]
                    return redirect(url_for('main.owner_dashboard'))
            elif user[2] == 'TENANT':
                    # Placeholder logic
                    return redirect(url_for('main.index')) 
                
        except Exception as e:
            print(e)
            flash('An error occurred during login', 'error')
        finally:
            cur.close()
            conn.close()
            
    return render_template('login.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') # 'OWNER' or 'TENANT'
        
        if not role:
            flash("Please form role", "error") # Should be hidden input, but safety check
            return redirect(url_for('main.signup'))

        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash("Database Error", "error")
            return redirect(url_for('main.signup'))
            
        cur = conn.cursor()
        try:
            # Check if email already taken
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("Email already registered. Please Login instead.", "error")
                return redirect(url_for('main.signup'))

            if role == 'OWNER':
                # ... (Owner creation logic remains same) ...
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'OWNER') RETURNING id",
                    (email, hashed_pw)
                )
                user_id = cur.fetchone()[0]
                cur.execute("INSERT INTO owners (user_id, full_name) VALUES (%s, %s)", (user_id, name))
                conn.commit()
                
                session['user_id'] = user_id
                session['role'] = 'OWNER'
                session['name'] = name
                return redirect(url_for('main.owner_dashboard'))

            elif role == 'TENANT':
                # 1. Verify Invitation
                cur.execute("SELECT id, owner_id FROM tenants WHERE email = %s", (email,))
                tenant_record = cur.fetchone()
                
                if not tenant_record:
                    # Specific Error as requested
                    flash("You are not associated with any PG. Please verify your email or contact your PG Owner.", "error")
                    return redirect(url_for('main.signup'))
                    
                tenant_id = tenant_record[0]
                
                # ... (Tenant creation logic remains same) ...
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'TENANT') RETURNING id",
                    (email, hashed_pw)
                )
                user_id = cur.fetchone()[0]
                cur.execute("UPDATE tenants SET user_id = %s, onboarding_status = 'ACTIVE' WHERE id = %s", (user_id, tenant_id))
                conn.commit()
                
                session['user_id'] = user_id
                session['role'] = 'TENANT'
                session['name'] = name
                return redirect(url_for('main.index'))

        except Exception as e:
            conn.rollback()
            print(f"Signup Error: {e}")
            flash("Registration failed. Please try again.", "error")
        finally:
            cur.close()
            conn.close()

    return render_template('signup.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


# --- Owner Routes ---

@bp.route('/owner/dashboard')
def owner_dashboard():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    if not conn: return render_template('owner/dashboard.html', name=session.get('name', 'Owner'), total_income=0)
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_row = cur.fetchone()
        if not owner_row:
             return render_template('owner/dashboard.html', name=session.get('name', 'Owner'), total_income=0)
        
        owner_id = owner_row[0]
        
        # Calculate Total Monthly Potential Income (Sum of rents of all tenants)
        cur.execute("SELECT SUM(monthly_rent) FROM tenants WHERE owner_id = %s", (owner_id,))
        total_income = cur.fetchone()[0] or 0
        
        # Placeholder for Expenses (Not implemented yet)
        total_spent = 0
        
        net_profit = total_income - total_spent
        
        # Calculate Occupancy
        # 1. Total Capacity (Sum of all beds in all rooms of this owner)
        cur.execute("""
            SELECT SUM(capacity) 
            FROM rooms 
            WHERE property_id IN (SELECT id FROM properties WHERE owner_id = %s)
        """, (owner_id,))
        capacity_row = cur.fetchone()
        total_capacity = capacity_row[0] or 0
        
        # 2. Total Tenants (Occupied Beds)
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s", (owner_id,))
        total_tenants = cur.fetchone()[0] or 0
        
        # 3. Calculate Stats
        if total_capacity > 0:
            occupancy_rate = int((total_tenants / total_capacity) * 100)
        else:
            occupancy_rate = 0
            
        available_beds = max(0, total_capacity - total_tenants)
        occupancy_rotation = int((occupancy_rate / 100) * 360)
        occupancy_rotation_style = f"transform: rotate({occupancy_rotation}deg);"
        
        # 4. Rent Collection Stats (Current Month)
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        
        # Total Expected Rent (Sum of monthly_reny from Active Tenants)
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(monthly_rent), 0) 
            FROM tenants 
            WHERE owner_id = %s AND onboarding_status = 'ACTIVE'
        """, (owner_id,))
        stats_row = cur.fetchone()
        
        total_active_tenants = stats_row[0] or 0
        total_expected_rent = stats_row[1] or 0
        
        # Total Collected (Payments this month)
        cur.execute("""
            SELECT COUNT(DISTINCT tenant_id), COALESCE(SUM(amount), 0)
            FROM payments
            JOIN tenants ON payments.tenant_id = tenants.id
            WHERE tenants.owner_id = %s AND payment_month = %s
        """, (owner_id, current_month))
        payment_row = cur.fetchone()
        
        tenants_paid = payment_row[0] or 0
        total_collected = payment_row[1] or 0
        
        tenants_pending = max(0, total_active_tenants - tenants_paid)
        
        # Progress Calculation
        if total_active_tenants > 0:
            collection_percentage = int((tenants_paid / total_active_tenants) * 100)
        else:
            collection_percentage = 0
            
        rent_collection_style = f"width: {collection_percentage}%;"
        
        return render_template('owner/dashboard.html', 
                             name=session.get('name', 'Owner'),
                             total_income=total_income,
                             total_spent=total_spent,
                             net_profit=net_profit,
                             occupancy_rate=occupancy_rate,
                             occupancy_rotation=occupancy_rotation,
                             occupancy_rotation_style=occupancy_rotation_style,
                             available_beds=available_beds,
                             total_occupied=total_tenants,
                             # Rent Collection Data
                             tenants_paid=tenants_paid,
                             tenants_pending=tenants_pending,
                             collection_percentage=collection_percentage,
                             rent_collection_style=rent_collection_style)
                             
    except Exception as e:
        print(f"Error dashboard stats: {e}")
        return render_template('owner/dashboard.html', name=session.get('name', 'Owner'), total_income=0)
    finally:
        cur.close()
        conn.close()


@bp.route('/owner/tenants')
def owner_tenants():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database Error", "error")
        return render_template('owner/tenants.html', tenants=[])
        
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # Fetch Tenants
        cur.execute("""
            SELECT id, full_name, email, phone_number, room_number, 
                   onboarding_status, monthly_rent, created_at 
            FROM tenants 
            WHERE owner_id = %s 
            ORDER BY created_at DESC
        """, (owner_id,))
        
        # Convert to list of dicts for template
        rows = cur.fetchall()
        tenants = []
        for row in rows:
            tenants.append({
                'id': row[0],
                'full_name': row[1],
                'email': row[2],
                'phone': row[3],
                'room_no': row[4],
                'status': row[5],
                'rent': row[6],
                'joined': row[7].strftime('%d %b %Y') if row[7] else 'N/A'
            })
            
        return render_template('owner/tenants.html', tenants=tenants)
        
    except Exception as e:
        print(f"Error fetching tenants: {e}")
        flash("Could not load tenants", "error")
        return render_template('owner/tenants.html', tenants=[])
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/add-tenant', methods=['GET', 'POST'])
def owner_add_tenant():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        room_no = request.form.get('room_no')
        rent = request.form.get('rent')
        
        # Simple Validation
        if not full_name or not email:
            flash("Name and Email are required", "error")
            return redirect(url_for('main.owner_add_tenant'))
            
        if not rent:
            flash("Monthly Rent is mandatory", "error")
            return redirect(url_for('main.owner_add_tenant'))

        user_id = session.get('user_id')
        
        conn = get_db_connection()
        if not conn:
            flash("Database Connection Error", "error")
            return redirect(url_for('main.owner_add_tenant'))
            
        cur = conn.cursor()
        try:
             # Get Owner ID
            cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_id,))
            owner_row = cur.fetchone()
            if not owner_row:
                 flash("Owner profile not found", "error")
                 return redirect(url_for('main.login'))
            
            owner_id = owner_row[0]
            
            # 1. Check if email already invited (Global or Owner specific? Unique Constraint is per Owner)
            cur.execute("SELECT id FROM tenants WHERE email = %s AND owner_id = %s", (email, owner_id))
            if cur.fetchone():
                flash(f"Tenant with email '{email}' already exists.", "error")
                return redirect(url_for('main.owner_add_tenant'))

            # 2. Check if Phone Number already exists
            if phone:
                cur.execute("SELECT id FROM tenants WHERE phone_number = %s AND owner_id = %s", (phone, owner_id))
                if cur.fetchone():
                    flash(f"Tenant with phone number '{phone}' is already added.", "error")
                    return redirect(url_for('main.owner_add_tenant'))
                
            # Insert Tenant
            cur.execute("""
                INSERT INTO tenants (owner_id, full_name, email, phone_number, room_number, monthly_rent, onboarding_status)
                VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
            """, (owner_id, full_name, email, phone, room_no, rent))
            
            conn.commit()
            flash("Tenant added successfully! They can now sign up.", "success")
            return redirect(url_for('main.owner_tenants'))

        except Exception as e:
            conn.rollback()
            print(f"Error adding tenant: {e}")
            # Try to give a hint if it's a database constraint issue that wasn't caught
            if "unique constraint" in str(e).lower():
                 flash("A record with this email or ID already exists.", "error")
            else:
                 flash("System Error: Could not add tenant. Please check connection.", "error")
        finally:
             cur.close()
             conn.close()

    return render_template('owner/add_tenant.html')


@bp.route('/owner/settings')
def owner_settings():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    return render_template('owner/settings.html')


@bp.route('/owner/export/tenants')
def export_tenants():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    # Mock CSV for now
    csv_content = "Name,Email,Room,Status\nMock Data,mock@test.com,101,Active"
    from flask import Response
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=tenants.csv"}
    )


@bp.route('/owner/tenants/<int:tenant_id>')
def owner_tenant_details(tenant_id):
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    return render_template('owner/tenant_details.html', tenant_id=tenant_id)

@bp.route('/owner/properties')
def owner_properties():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database Error", "error")
        return render_template('owner/properties.html', properties=[])
        
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # 1. Fetch Properties
        cur.execute("SELECT id, name, address FROM properties WHERE owner_id = %s", (owner_id,))
        prop_rows = cur.fetchall()
        
        properties = []
        for prop_row in prop_rows:
            prop_id = prop_row[0]
            
            # 2. Fetch Rooms for this property
            cur.execute("""
                SELECT id, room_number, floor_number, capacity, rent_amount 
                FROM rooms WHERE property_id = %s ORDER BY room_number
            """, (prop_id,))
            room_rows = cur.fetchall()
            
            rooms = []
            for room in room_rows:
                r_id = room[0]
                # Count current tenants in this room
                cur.execute("SELECT COUNT(*) FROM tenants WHERE room_id = %s", (r_id,))
                occupancy = cur.fetchone()[0]
                
                capacity = room[3]
                occupancy_pct = int((occupancy / capacity) * 100) if capacity > 0 else 0
                
                rooms.append({
                    'id': r_id,
                    'room_number': room[1],
                    'floor': room[2],
                    'capacity': capacity,
                    'rent': room[4],
                    'occupancy': occupancy,
                    'occupancy_pct': occupancy_pct,
                    'occupancy_style': f"width: {occupancy_pct}%"
                })
                
            properties.append({
                'id': prop_id,
                'name': prop_row[1],
                'address': prop_row[2],
                'rooms': rooms
            })
            
        return render_template('owner/properties.html', properties=properties)

    except Exception as e:
        print(f"Error fetching properties: {e}")
        flash("System Error", "error")
        return render_template('owner/properties.html', properties=[])
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/properties/add-room', methods=['POST'])
def add_room():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    room_number = request.form.get('room_number')
    floor = request.form.get('floor')
    capacity = request.form.get('capacity')
    rent = request.form.get('rent_amount')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # Get default property (assume single property for now)
        cur.execute("SELECT id FROM properties WHERE owner_id = %s", (owner_id,))
        prop_row = cur.fetchone()
        if not prop_row:
             # Create one if missing safety net
             cur.execute("INSERT INTO properties (owner_id) VALUES (%s) RETURNING id", (owner_id,))
             property_id = cur.fetchone()[0]
        else:
             property_id = prop_row[0]

        cur.execute("""
            INSERT INTO rooms (property_id, room_number, floor_number, capacity, rent_amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (property_id, room_number, floor, capacity, rent))
        
        conn.commit()
        flash("Room added successfully!", "success")
        
    except Exception as e:
        conn.rollback()
        print(f"Error adding room: {e}")
        if "unique constraint" in str(e).lower():
            flash("Room number already exists!", "error")
        else:
            flash("Failed to add room", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_properties'))
