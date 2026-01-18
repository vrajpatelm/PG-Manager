
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
            flash('Database connection error')
            return render_template('login.html')
            
        cur = conn.cursor()
        try:
            # Check User
            cur.execute("SELECT id, password_hash, role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['role'] = user[2]
                
                # Get Name for Session (Optional but nice)
                if user[2] == 'OWNER':
                     cur.execute("SELECT full_name FROM owners WHERE user_id = %s", (user[0],))
                     owner = cur.fetchone()
                     if owner: session['name'] = owner[0]
                     return redirect(url_for('main.owner_dashboard'))
                elif user[2] == 'TENANT':
                     # Placeholder logic for tenant
                     return redirect(url_for('main.index')) 
            else:
                flash('Invalid email or password', 'error')
                
        except Exception as e:
            print(e)
            flash('An error occurred during login')
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
            flash("Please select a role", "error")
            return redirect(url_for('main.signup'))

        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash("Database Error")
            return redirect(url_for('main.signup'))
            
        cur = conn.cursor()
        try:
            # Check if email already taken
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("Email already registered", "error")
                return redirect(url_for('main.signup'))

            if role == 'OWNER':
                # 1. Create User
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'OWNER') RETURNING id",
                    (email, hashed_pw)
                )
                user_id = cur.fetchone()[0]
                
                # 2. Create Owner Profile
                cur.execute(
                    "INSERT INTO owners (user_id, full_name) VALUES (%s, %s)",
                    (user_id, name)
                )
                
                conn.commit()
                
                # Auto Login
                session['user_id'] = user_id
                session['role'] = 'OWNER'
                session['name'] = name
                return redirect(url_for('main.owner_dashboard'))

            elif role == 'TENANT':
                # 1. Verify Invitation
                cur.execute("SELECT id, owner_id FROM tenants WHERE email = %s", (email,))
                tenant_record = cur.fetchone()
                
                if not tenant_record:
                    flash("No invitation found for this email. Please ask your PG owner to add you first.", "error")
                    return redirect(url_for('main.signup'))
                    
                tenant_id = tenant_record[0]
                
                # 2. Create User
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'TENANT') RETURNING id",
                    (email, hashed_pw)
                )
                user_id = cur.fetchone()[0]
                
                # 3. Link User to Tenant Record
                cur.execute(
                    "UPDATE tenants SET user_id = %s, onboarding_status = 'ACTIVE' WHERE id = %s",
                    (user_id, tenant_id)
                )
                
                conn.commit()
                
                 # Auto Login
                session['user_id'] = user_id
                session['role'] = 'TENANT'
                session['name'] = name
                return redirect(url_for('main.index')) # Tenant Dashboard Placeholder

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

@bp.route('/owner/add-tenant')
def owner_add_tenant():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
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
