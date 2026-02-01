import traceback
import random
import smtplib
import os
import secrets
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.database import get_db_connection
from . import bp

def send_otp_email(to_email, otp):
    """Sends OTP via SMTP or prints to console if not configured"""
    user = current_app.config.get('MAIL_USERNAME')
    pwd = current_app.config.get('MAIL_PASSWORD')
    
    msg_body = f"Your PG-Manager Verification Code is: {otp}\n\nThis code expires in 10 minutes."
    
    if not user or not pwd:
        print(f"\n[MOCK EMAIL] To: {to_email} | Subject: Verification OTP | Body: {msg_body}\n")
        return True

    try:
        msg = MIMEText(msg_body)
        msg['Subject'] = "PG-Manager Verification Code"
        msg['From'] = user
        msg['To'] = to_email

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@bp.route('/auth/send-otp', methods=['POST'])
def send_otp():
    """API endpoint to generate and send OTP"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if email taken
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({'success': False, 'message': 'Email already registered. Please Login.'}), 400

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=10)

        # Store in DB (Upsert)
        cur.execute("""
            INSERT INTO otp_verifications (email, otp_code, expires_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE 
            SET otp_code = EXCLUDED.otp_code, expires_at = EXCLUDED.expires_at
        """, (email, otp, expires_at))
        conn.commit()

        # Send Email
        send_otp_email(email, otp)
        
        return jsonify({'success': True, 'message': 'OTP sent successfully!'})

    except Exception as e:
        print(f"OTP Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500
    finally:
        cur.close()
        conn.close()

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
                    # Need to fetch tenant name properly too
                    cur.execute("SELECT full_name FROM tenants WHERE user_id = %s", (user[0],))
                    tn = cur.fetchone()
                    if tn: session['name'] = tn[0]
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
        otp_input = request.form.get('otp')

        if not otp_input:
            flash("OTP is required to verify email.", "error")
            return redirect(url_for('main.signup'))
        
        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash("Database Error", "error")
            return redirect(url_for('main.signup'))
            
        cur = conn.cursor()
        try:
            # 1. Verify OTP
            cur.execute("SELECT otp_code, expires_at FROM otp_verifications WHERE email = %s", (email,))
            otp_record = cur.fetchone()
            
            if not otp_record:
                flash("OTP not found. Please request a new one.", "error")
                return redirect(url_for('main.signup'))
            
            stored_otp, expires = otp_record
            if stored_otp != otp_input:
                flash("Invalid OTP. Please try again.", "error")
                return redirect(url_for('main.signup'))
            
            if datetime.now() > expires:
                flash("OTP has expired. Please request a new one.", "error")
                return redirect(url_for('main.signup'))

            # 2. Proceed with Signup
             # Check if email already taken (double check)
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("Email already registered. Please Login.", "error")
                return redirect(url_for('main.signup'))

            if role == 'OWNER':
                # ... (Owner creation logic) ...
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'OWNER') RETURNING id",
                    (email, hashed_pw)
                )
                user_id = cur.fetchone()[0]
                cur.execute("INSERT INTO owners (user_id, full_name) VALUES (%s, %s)", (user_id, name))
                conn.commit()
                
                # Clear OTP
                cur.execute("DELETE FROM otp_verifications WHERE email = %s", (email,))
                conn.commit()

                session['user_id'] = user_id
                session['role'] = 'OWNER'
                session['name'] = name
                return redirect(url_for('main.owner_dashboard'))

            elif role == 'TENANT':
                # 1. Verify Invitation
                cur.execute("SELECT id, owner_id, onboarding_status, full_name FROM tenants WHERE email = %s", (email,))
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
                
                # ... (Tenant creation logic) ...
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'TENANT') RETURNING id",
                    (email, hashed_pw)
                )
                user_id = cur.fetchone()[0]
                cur.execute("UPDATE tenants SET user_id = %s, onboarding_status = 'ACTIVE' WHERE id = %s", (user_id, tenant_id))
                conn.commit()
                
                # Clear OTP
                cur.execute("DELETE FROM otp_verifications WHERE email = %s", (email,))
                conn.commit()

                session['user_id'] = user_id
                session['role'] = 'TENANT'
                session['name'] = tenant_record[3] # Use tenant name from record
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
