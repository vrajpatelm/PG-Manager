import traceback
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.database import get_db_connection
from . import bp

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
                    return redirect(url_for('main.tenant_dashboard')) 
                
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
                cur.execute("SELECT id, owner_id, onboarding_status FROM tenants WHERE email = %s", (email,))
                tenant_record = cur.fetchone()
                
                if not tenant_record:
                    # Specific Error as requested
                    flash("You are not associated with any PG. Please verify your email or contact your PG Owner.", "error")
                    return redirect(url_for('main.signup'))
                    
                tenant_id = tenant_record[0]
                status = tenant_record[2]
                
                if status == 'DRAFT':
                    flash("Your admission is still in Draft. Please ask your Owner to finalize it.", "error")
                    return redirect(url_for('main.signup'))
                
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
                return redirect(url_for('main.tenant_dashboard'))

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
