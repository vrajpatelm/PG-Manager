
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
    if session.get('role') != 'OWNER':
        return redirect(url_for('main.login'))
    return render_template('owner/dashboard.html', name=session.get('name', 'Owner'))


@bp.route('/owner/tenants')
def owner_tenants():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    return render_template('owner/tenants.html')

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
