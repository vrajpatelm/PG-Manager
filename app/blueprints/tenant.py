import json
import uuid
import psycopg2
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.utils.pdf import generate_receipt
import io
from . import bp

@bp.route('/tenant/dashboard')
@role_required('TENANT')
def tenant_dashboard():
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.id, t.full_name, t.room_number, t.bed_number, t.phone_number, t.email, t.monthly_rent, t.onboarding_status
            FROM tenants t
            WHERE t.user_id = %s
        """, (session.get('user_id'),))
        tenant = cur.fetchone()
        
        if not tenant:
            flash("Tenant record not found.", "error")
            return redirect(url_for('main.login'))

        current_month = datetime.now().strftime('%Y-%m')
        
        cur.execute("""
            SELECT status FROM payments 
            WHERE tenant_id = %s AND payment_month = %s
            ORDER BY created_at DESC LIMIT 1
        """, (tenant[0], current_month))
        
        payment_record = cur.fetchone()
        
        rent_status = 'UNPAID'
        if payment_record:
            status_val = payment_record[0]
            if status_val == 'COMPLETED':
                rent_status = 'PAID'
            elif status_val == 'PENDING':
                rent_status = 'VERIFYING'
            
        cur.execute("""
            SELECT o.upi_id, o.id 
            FROM owners o 
            JOIN tenants t ON t.owner_id = o.id 
            WHERE t.id = %s
        """, (tenant[0],))
        owner_details = cur.fetchone()
        
        tenant_data = {
            'id': tenant[0],
            'full_name': tenant[1],
            'room_number': tenant[2],
            'bed_number': tenant[3],
            'phone': tenant[4],
            'email': tenant[5],
            'rent': tenant[6],
            'status': tenant[7],
            'rent_status': rent_status,
            'owner_upi': owner_details[0] if owner_details else None,
            'owner_id': owner_details[1] if owner_details else None
        }

        # Fetch Recent Notices
        owner_id = owner_details[1] if owner_details else None
        recent_notices = []
        
        if owner_id:
             cur.execute("""
                SELECT id, title, description, priority, created_at 
                FROM notices 
                WHERE owner_id = %s 
                ORDER BY created_at DESC 
                LIMIT 3
            """, (owner_id,))
             for row in cur.fetchall():
                 recent_notices.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'created_at': row[4]
                })

        # Fetch Property Settings (WiFi, Rules, Timings)
        property_settings = None
        if owner_id:
             cur.execute("""
                SELECT wifi_ssid, wifi_password, gate_closing_time, house_rules, 
                       breakfast_start_time, breakfast_end_time
                FROM properties 
                WHERE owner_id = %s
                LIMIT 1
            """, (owner_id,))
             p_row = cur.fetchone()
             if p_row:
                 property_settings = {
                     'wifi_ssid': p_row[0],
                     'wifi_password': p_row[1],
                     'gate_time': p_row[2].strftime('%I:%M %p') if p_row[2] else None,
                     'rules': p_row[3],
                     'bf_start': p_row[4].strftime('%I:%M %p') if p_row[4] else None,
                     'bf_end': p_row[5].strftime('%I:%M %p') if p_row[5] else None
                 }

        return render_template('tenant/dashboard.html', tenant=tenant_data, recent_notices=recent_notices, property=property_settings)
    except Exception as e:
        print(f"Tenant Dashboard Error: {e}")
        return render_template('tenant/dashboard.html',
                         tenant=tenant_data,
                         current_date=datetime.now(),
                         recent_notices=[],
                         property=None)
    finally:
        cur.close()
        conn.close()

@bp.route('/tenant/pay', methods=['POST'])
@role_required('TENANT')
def tenant_pay_rent():

    amount = request.form['amount']
    txn_id = request.form['transaction_id']
    tenant_id = request.form['tenant_id']
    payment_month = datetime.now().strftime('%Y-%m') 

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id FROM payments
            WHERE tenant_id = %s AND payment_month = %s AND status IN ('COMPLETED', 'PENDING')
        """, (tenant_id, payment_month))

        if cur.fetchone():
            flash("Payment for this month is already recorded or pending.", "warning")
            return redirect(url_for('main.tenant_dashboard'))

        cur.execute("""
            INSERT INTO payments (id, tenant_id, amount, payment_date, payment_month, payment_mode, remarks, status)
            VALUES (%s, %s, %s, CURRENT_DATE, %s, 'UPI', %s, 'PENDING')
        """, (str(uuid.uuid4()), tenant_id, amount, payment_month, f"Txn Ref: {txn_id}"))

        conn.commit()
        flash("Payment submitted for verification!", "success")

    except Exception as e:
        conn.rollback()
        print(f"Error submitting payment: {e}")
        flash("Failed to submit payment.", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('main.tenant_dashboard'))

@bp.route('/tenant/complaints')
@role_required('TENANT')
def tenant_complaints():

    user_id = session.get('user_id')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, full_name, email FROM tenants WHERE user_id = %s", (user_id,))
        tenant = cur.fetchone()

        if not tenant:
            return "Tenant profile not found", 404

        tenant_id = tenant[0]

        cur.execute("""
            SELECT id, title, description, priority, status, created_at
            FROM complaints
            WHERE tenant_id = %s
            ORDER BY created_at DESC
        """, (tenant_id,))

        complaints = []
        for row in cur.fetchall():
            complaints.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'priority': row[3],
                'status': row[4],
                'created_at': row[5].strftime('%Y-%m-%d')
            })

        cur.close()
        conn.close()

        return render_template('tenant/complaints.html', complaints=complaints, session=session)

    except Exception as e:
        print(f"Error fetching tenant complaints: {e}")
        return redirect(url_for('main.tenant_dashboard'))

@bp.route('/tenant/complaint', methods=['POST'])
@role_required('TENANT')
def tenant_raise_complaint():

    title = request.form['title']
    description = request.form['description']
    priority = request.form['priority']
    user_id = session.get('user_id')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, owner_id FROM tenants WHERE user_id = %s", (user_id,))
        res = cur.fetchone()
        tenant_id = res[0]
        owner_id = res[1]

        cur.execute("""
            INSERT INTO complaints (id, tenant_id, owner_id, title, description, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
        """, (str(uuid.uuid4()), tenant_id, owner_id, title, description, priority))

        conn.commit()
        flash("Complaint submitted successfully!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error raising complaint: {e}")
        flash("Failed to submit complaint", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('main.tenant_complaints'))

@bp.route('/tenant/qr/<tenant_id>')
def tenant_qr_code(tenant_id):
    import qrcode
    from io import BytesIO

    qr_content = f"TENANT:{tenant_id}"
    
    img = qrcode.make(qr_content)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@bp.route('/tenant/settings')
@role_required('TENANT')
def tenant_settings():
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.full_name, t.email, t.phone_number, t.room_number, t.bed_number, t.lease_start
            FROM tenants t
            WHERE t.user_id = %s
        """, (user_id,))
        tenant = cur.fetchone()
        
        if not tenant:
            return "Tenant not found", 404
            
        profile = {
            'full_name': tenant[0],
            'email': tenant[1],
            'phone': tenant[2],
            'room': tenant[3],
            'bed': tenant[4],
            'move_in': tenant[5]
        }
            
        return render_template('tenant/settings.html', profile=profile, session=session)
        
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return redirect(url_for('main.tenant_dashboard'))
    finally:
        cur.close()
        conn.close()

@bp.route('/tenant/settings/update', methods=['POST'])
@role_required('TENANT')
def tenant_update_settings():
    
    phone = request.form.get('phone')
    password = request.form.get('password')
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE tenants SET phone_number = %s WHERE user_id = %s", (phone, user_id))
        
        if password:
            hashed_pw = generate_password_hash(password)
            cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_pw, user_id))
            flash("Settings updated successfully!", "success")
        else:
            flash("Profile settings updated!", "success")
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating settings: {e}")
        flash("Failed to update settings", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.tenant_settings'))

# Keeping profile route for backward compatibility but redirecting or reusing logic is better
@bp.route('/tenant/profile')
def tenant_profile():
    return redirect(url_for('main.tenant_settings'))

@bp.route('/tenant/payments')
@role_required('TENANT')
def tenant_payments():
    
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM tenants WHERE user_id = %s", (user_id,))
        tenant = cur.fetchone()
        
        if not tenant:
            return "Tenant not found", 404
            
        tenant_id = tenant[0]
        
        cur.execute("""
            SELECT id, amount, payment_date, payment_month, status, payment_mode, remarks, created_at
            FROM payments 
            WHERE tenant_id = %s 
            ORDER BY payment_date DESC, created_at DESC
        """, (tenant_id,))
        
        payments = []
        for row in cur.fetchall():
            payments.append({
                'id': row[0],
                'amount': row[1],
                'date': row[2],
                'month': row[3],
                'status': row[4],
                'mode': row[5],
                'remarks': row[6],
                'created_at': row[7]
            })
            
        return render_template('tenant/payments.html', payments=payments, session=session)
        
    except Exception as e:
        print(f"Error fetching payments: {e}")
        return redirect(url_for('main.tenant_dashboard'))
    finally:
        cur.close()
        conn.close()

@bp.route('/tenant/notices')
@role_required('TENANT')
def tenant_notices():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT owner_id FROM tenants WHERE user_id = %s", (session.get('user_id'),))
        tenant_row = cur.fetchone()
        
        notices = []
        if tenant_row:
             owner_id = tenant_row[0]
             cur.execute("""
                SELECT id, title, description, priority, created_at 
                FROM notices 
                WHERE owner_id = %s 
                ORDER BY created_at DESC
            """, (owner_id,))
             
             for row in cur.fetchall():
                notices.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'created_at': row[4]
                })
        
        return render_template('tenant/notices.html', notices=notices)
        
    except Exception as e:
        print(f"Error fetching tenant notices: {e}")
        return render_template('tenant/notices.html', notices=[])
    finally:
        cur.close()
        conn.close()

@bp.route('/tenant/payment/<payment_id>/download')
@role_required('TENANT')
def download_receipt(payment_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch payment details with joins for Tenant and Owner info
        cur.execute("""
            SELECT p.id, p.amount, p.payment_date, p.payment_month, p.payment_mode, p.status, 
                   t.full_name, t.room_number, o.full_name
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.id
            JOIN owners o ON t.owner_id = o.id
            WHERE p.id = %s AND t.user_id = %s
        """, (payment_id, session.get('user_id')))
        
        row = cur.fetchone()
        if not row:
            flash("Receipt not found or access denied.", "error")
            return redirect(url_for('main.tenant_payments'))
            
        if row[5] != 'COMPLETED':
            flash("Receipt available only for completed payments.", "warning")
            return redirect(url_for('main.tenant_payments'))

        # Generate Receipt
        receipt_data = {
            'transaction_id': str(row[0]),
            'amount': row[1],
            'date': row[2],
            'month': row[3],
            'payment_mode': row[4],
            'tenant_name': row[6],
            'tenant_room': row[7],
            'owner_name': row[8]
        }
        
        pdf_buffer = generate_receipt(receipt_data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Receipt_{row[3]}.pdf"
        )

    except Exception as e:
        print(f"Error generating receipt: {e}")
        flash("Error generating receipt.", "error")
        return redirect(url_for('main.tenant_payments'))
    finally:
        cur.close()
        conn.close()
