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
from email.mime.multipart import MIMEMultipart
from . import bp

def send_otp_email(to_email, otp):
    """Sends OTP via SMTP with a premium HTML template"""
    user = current_app.config.get('MAIL_USERNAME')
    pwd = current_app.config.get('MAIL_PASSWORD')
    
    # Premium HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#F8FAFC; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; margin-top: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            
            <!-- Header -->
            <div style="background-color: #1E293B; padding: 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px;">PG Manager</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 40px 32px; text-align: center;">
                <h2 style="color: #0F172A; font-size: 20px; font-weight: 600; margin: 0 0 16px;">Verify your email address</h2>
                <p style="color: #64748B; font-size: 16px; line-height: 24px; margin: 0 0 32px;">
                    Use the code below to verify your email and complete your registration.
                </p>
                
                <!-- OTP Box -->
                <div style="background-color: #F1F5F9; border-radius: 12px; padding: 24px; margin: 0 auto; width: fit-content; border: 1px solid #E2E8F0;">
                    <span style="font-family: monospace; color: #0F172A; font-size: 32px; font-weight: 700; letter-spacing: 8px; display: block;">{otp}</span>
                </div>
                
                <p style="color: #94A3B8; font-size: 14px; margin-top: 32px;">
                    This code will expire in <strong>10 minutes</strong>.<br>
                    If you didn't request this, please ignore this email.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #F8FAFC; padding: 24px; text-align: center; border-top: 1px solid #E2E8F0;">
                <p style="color: #94A3B8; font-size: 12px; margin: 0;">
                    &copy; {datetime.now().year} PG Manager. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Your PG-Manager Verification Code is: {otp}\n\nThis code expires in 10 minutes."
    
    # Mock Mode
    if not user or not pwd:
        print(f"\n{'='*50}")
        print(f"[MOCK EMAIL] To: {to_email}")
        print(f"Subject: PG-Manager Verification Code")
        print(f"OTP: {otp}")
        print(f"{'='*50}\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = "Your Verification Code - PG Manager"
        msg['From'] = user
        msg['To'] = to_email

        # Attach parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

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
        # Support both JSON (API) and Form Data (Classic)
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')
            otp_input = data.get('otp')
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            otp_input = request.form.get('otp')

        if not otp_input:
            msg = "OTP is required to verify email."
            if request.is_json: return jsonify({'success': False, 'message': msg}), 400
            flash(msg, "error")
            return redirect(url_for('main.signup'))
        
        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            msg = "Database Error"
            if request.is_json: return jsonify({'success': False, 'message': msg}), 500
            flash(msg, "error")
            return redirect(url_for('main.signup'))
            
        cur = conn.cursor()
        try:
            # 1. Verify OTP
            cur.execute("SELECT otp_code, expires_at FROM otp_verifications WHERE email = %s", (email,))
            otp_record = cur.fetchone()
            
            if not otp_record:
                msg = "OTP not found. Please request a new one."
                if request.is_json: return jsonify({'success': False, 'message': msg}), 400
                flash(msg, "error")
                return redirect(url_for('main.signup'))
            
            stored_otp, expires = otp_record
            if stored_otp != otp_input:
                msg = "Invalid OTP. Please try again."
                if request.is_json: return jsonify({'success': False, 'message': msg}), 400
                flash(msg, "error")
                return redirect(url_for('main.signup'))
            
            if datetime.now() > expires:
                msg = "OTP has expired. Please request a new one."
                if request.is_json: return jsonify({'success': False, 'message': msg}), 400
                flash(msg, "error")
                return redirect(url_for('main.signup'))

            # 2. Proceed with Signup
             # Check if email already taken (double check)
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                msg = "Email already registered. Please Login."
                if request.is_json: return jsonify({'success': False, 'message': msg}), 400
                flash(msg, "error")
                return redirect(url_for('main.signup'))

            redirect_target = url_for('main.login') # Default

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
                redirect_target = url_for('main.owner_dashboard')

            elif role == 'TENANT':
                # 1. Verify Invitation
                cur.execute("SELECT id, owner_id, onboarding_status, full_name FROM tenants WHERE email = %s", (email,))
                tenant_record = cur.fetchone()
                
                if not tenant_record:
                    msg = "You are not associated with any PG. Please verify your email or contact your PG Owner."
                    if request.is_json: return jsonify({'success': False, 'message': msg}), 400
                    flash(msg, "error")
                    return redirect(url_for('main.signup'))
                    
                tenant_id = tenant_record[0]
                status = tenant_record[2]
                
                if status == 'DRAFT':
                    msg = "Your admission is still in Draft. Please ask your Owner to finalize it."
                    if request.is_json: return jsonify({'success': False, 'message': msg}), 400
                    flash(msg, "error")
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
                redirect_target = url_for('main.tenant_dashboard')
            
            if request.is_json:
                return jsonify({'success': True, 'redirect_url': redirect_target})
            return redirect(redirect_target)

        except Exception as e:
            conn.rollback()
            print(f"Signup Error: {e}")
            msg = "Registration failed. Please try again."
            if request.is_json: return jsonify({'success': False, 'message': msg}), 500
            flash(msg, "error")
        finally:
            cur.close()
            conn.close()

    return render_template('signup.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

def send_reset_email(to_email, link):
    """Sends Password Reset Link via SMTP with a premium HTML template"""
    user = current_app.config.get('MAIL_USERNAME')
    pwd = current_app.config.get('MAIL_PASSWORD')
    
    # Premium HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#F8FAFC; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; margin-top: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            
            <div style="background-color: #1E293B; padding: 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px;">PG Manager</h1>
            </div>
            
            <div style="padding: 40px 32px; text-align: center;">
                <h2 style="color: #0F172A; font-size: 20px; font-weight: 600; margin: 0 0 16px;">Reset your password</h2>
                <p style="color: #64748B; font-size: 16px; line-height: 24px; margin: 0 0 32px;">
                    We received a request to reset your password. Click the button below to choose a new one.
                </p>
                
                <a href="{link}" style="background-color: #2563EB; color: #ffffff; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; font-size: 16px;">Reset Password</a>
                
                <p style="color: #94A3B8; font-size: 14px; margin-top: 32px;">
                    This link will expire in <strong>30 minutes</strong>.<br>
                    If you didn't ask for this, you can safely ignore this email.
                </p>
            </div>
            
             <div style="background-color: #F8FAFC; padding: 24px; text-align: center; border-top: 1px solid #E2E8F0;">
                <p style="color: #94A3B8; font-size: 12px; margin: 0;">
                    &copy; {datetime.now().year} PG Manager. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Reset your password here: {link}\n\nThis link expires in 30 minutes."
    
    if not user or not pwd:
        print(f"\n{'='*50}")
        print(f"[MOCK EMAIL] To: {to_email}")
        print(f"Subject: Reset Password")
        print(f"Link: {link}")
        print(f"{'='*50}\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = "Reset Your Password - PG Manager"
        msg['From'] = user
        msg['To'] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@bp.route('/auth/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if not cur.fetchone():
                # Don't reveal if user exists or not for security, but for UX we usually say "If account exists..."
                # Here we will just say it sent.
                flash("If an account exists with that email, we have sent a reset link.", "success")
                return redirect(url_for('main.login'))
            
            token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(minutes=30)
            
            cur.execute("""
                INSERT INTO password_resets (email, token, expires_at) 
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE 
                SET token = EXCLUDED.token, expires_at = EXCLUDED.expires_at
            """, (email, token, expires))
            conn.commit()
            
            link = url_for('main.reset_password', token=token, _external=True)
            send_reset_email(email, link)
            
            flash("Reset link sent! Please check your email inbox.", "success")
            return redirect(url_for('main.login'))
            
        except Exception as e:
            print(e)
            flash("Error sending reset link.", "error")
        finally:
            cur.close()
            conn.close()
            
    return render_template('forgot_password.html')

@bp.route('/auth/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify Token
    cur.execute("SELECT email, expires_at FROM password_resets WHERE token = %s", (token,))
    record = cur.fetchone()
    
    conn.close() # Close strictly to avoid holding connection during render
    
    if not record:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for('main.login'))
        
    email, expires_at = record
    if datetime.now() > expires_at:
        flash("Link has expired. Please request a new one.", "error")
        return redirect(url_for('main.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', token=token)
            
        hashed = generate_password_hash(password)
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Update Password
            cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed, email))
            # Delete Token
            cur.execute("DELETE FROM password_resets WHERE email = %s", (email,))
            conn.commit()
            
            flash("Password updated successfully! You can now login.", "success")
            return redirect(url_for('main.login'))
        except Exception as e:
            conn.rollback()
            print(e)
            flash("Error updating password.", "error")
        finally:
            cur.close()
            conn.close()
            
    return render_template('reset_password.html', token=token)
