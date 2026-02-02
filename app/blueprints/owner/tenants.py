import csv
import io
import threading
import math
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, session, flash, Response, current_app
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.utils.mailer import send_email
from app.utils.activity import log_activity
from app.blueprints import bp

@bp.route('/owner/tenants')
@role_required('OWNER')
def owner_tenants():
    
    conn = get_db_connection()
    if not conn:
        flash("Database Error", "error")
        return render_template('owner/tenants.html', tenants=[])
        
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        filter_type = request.args.get('filter', 'all')
        
        query = """
            SELECT id, full_name, email, phone_number, room_number, 
                   onboarding_status, monthly_rent, created_at 
            FROM tenants 
            WHERE owner_id = %s 
        """
        params = [owner_id]
        
        if filter_type == 'active':
            query += " AND onboarding_status = 'ACTIVE'"
        elif filter_type == 'rent-due':
            current_month = datetime.now().strftime('%Y-%m')
            query += """ 
                AND onboarding_status = 'ACTIVE'
                AND id NOT IN (
                    SELECT tenant_id FROM payments 
                    WHERE payment_month = %s AND status = 'COMPLETED'
                )
            """
            params.append(current_month)
        elif filter_type == 'lease-expiring':
            query += " AND onboarding_status = 'ACTIVE' AND lease_end BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'"
        elif filter_type == 'past':
            query += " AND onboarding_status IN ('EXITED', 'LEFT', 'MOVED_OUT', 'REJECTED')"
        
        search_query = request.args.get('search')
        if search_query:
            query += " AND (full_name ILIKE %s OR email ILIKE %s OR room_number ILIKE %s)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY created_at DESC"
        
        page = request.args.get('page', 1, type=int)
        per_page = 3
        offset = (page - 1) * per_page
        
        count_query = f"SELECT COUNT(*) FROM ({query}) AS sub"
        cur.execute(count_query, tuple(params))
        total_count = cur.fetchone()[0]
        
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cur.execute(query, tuple(params))
        
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
            
        total_pages = math.ceil(total_count / per_page)
        
        pagination = {
            'current_page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'total_count': total_count,
            'per_page': per_page
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return render_template('owner/partials/tenant_list_with_pagination.html', tenants=tenants, pagination=pagination)

        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s", (owner_id,))
        global_total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s AND onboarding_status = 'ACTIVE'", (owner_id,))
        global_active = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s AND onboarding_status = 'NOTICE'", (owner_id,))
        global_notice = cur.fetchone()[0]

        current_month = datetime.now().strftime('%Y-%m')
        cur.execute("""
            SELECT COUNT(DISTINCT tenant_id) FROM payments 
            WHERE payment_month = %s AND status = 'COMPLETED'
        """, (current_month,))
        paid_count = cur.fetchone()[0]
        
        global_rent_due = max(0, global_active - paid_count)

        return render_template('owner/tenants.html', 
                             tenants=tenants,
                             pagination=pagination,
                             stats={
                                 'total': global_total,
                                 'active': global_active,
                                 'rent_due': global_rent_due,
                                 'notice': global_notice
                             })
        
    except Exception as e:
        print(f"Error fetching tenants: {e}")
        flash("Could not load tenants", "error")
        return render_template('owner/tenants.html', 
                             tenants=[],
                             stats={'total': 0, 'active': 0, 'rent_due': 0, 'notice': 0})
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/add-tenant', methods=['GET', 'POST'])
@role_required('OWNER')
def owner_add_tenant():
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        room_no = request.form.get('room_no')
        rent = request.form.get('rent')
        bed_no = request.form.get('bed_no')
        move_in_date = request.form.get('move_in_date')
        
        if not full_name or not email:
            flash("Name and Email are required", "error")
            return redirect(url_for('main.owner_add_tenant'))
            
        if not phone:
             flash("Phone Number is required", "error")
             return redirect(url_for('main.owner_add_tenant'))
             
        if not phone.isdigit() or len(phone) != 10:
             flash("Phone number must contain exactly 10 digits", "error")
             return redirect(url_for('main.owner_add_tenant'))

        if not rent:
            flash("Monthly Rent is mandatory", "error")
            return redirect(url_for('main.owner_add_tenant'))
            
        if not move_in_date:
            move_in_date = date.today()

        user_id = session.get('user_id')
        
        conn = get_db_connection()
        if not conn:
            flash("Database Connection Error", "error")
            return redirect(url_for('main.owner_add_tenant'))
            
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM owners WHERE user_id = %s", (user_id,))
            owner_row = cur.fetchone()
            if not owner_row:
                 flash("Owner profile not found", "error")
                 return redirect(url_for('main.login'))
            
            owner_id = owner_row[0]
            
            cur.execute("SELECT id FROM tenants WHERE email = %s AND owner_id = %s", (email, owner_id))
            if cur.fetchone():
                flash(f"Tenant with email '{email}' already exists.", "error")
                return redirect(url_for('main.owner_add_tenant'))
                
            cur.execute("SELECT id, role FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                flash(f"Email '{email}' is already registered as a {existing_user[1]}. Cannot add as new tenant.", "error")
                return redirect(url_for('main.owner_add_tenant'))

            if phone:
                cur.execute("SELECT id FROM tenants WHERE phone_number = %s AND owner_id = %s", (phone, owner_id))
                if cur.fetchone():
                    flash(f"Tenant with phone number '{phone}' is already added.", "error")
                    return redirect(url_for('main.owner_add_tenant'))
                
            action = request.form.get('action')
            status = 'DRAFT' if action == 'draft' else 'PENDING'
            
            cur.execute("""
                SELECT r.id FROM rooms r
                JOIN properties p ON r.property_id = p.id
                WHERE p.owner_id = %s AND r.room_number = %s
            """, (owner_id, room_no))
            room_row = cur.fetchone()
            room_id = room_row[0] if room_row else None

            cur.execute("""
                INSERT INTO tenants (owner_id, full_name, email, phone_number, room_number, room_id, monthly_rent, onboarding_status, bed_number, lease_start)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (owner_id, full_name, email, phone, room_no, room_id, rent, status, bed_no, move_in_date))
            
            conn.commit()
            
            # Log Activity
            log_activity(owner_id, 'TENANT_ADD', f"Added new tenant {full_name} to Room {room_no}", {'room': room_no})
            
            if status == 'DRAFT':
                flash("Tenant details saved as Draft.", "success")
            else:
                flash("Tenant added successfully! They can now sign up.", "success")
            
            return redirect(url_for('main.owner_tenants'))

        except Exception as e:
            conn.rollback()
            print(f"Error adding tenant: {e}")
            if "unique constraint" in str(e).lower():
                 flash("A record with this email or ID already exists.", "error")
            else:
                 flash("System Error: Could not add tenant. Please check connection.", "error")
        finally:
             cur.close()
             conn.close()

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        cur.execute("""
            SELECT r.id, r.room_number, r.capacity, r.rent_amount,
                   (SELECT COUNT(*) FROM tenants t WHERE t.room_id = r.id AND t.onboarding_status IN ('ACTIVE', 'PENDING', 'NOTICE')) as current_occupancy
            FROM rooms r
            JOIN properties p ON r.property_id = p.id
            WHERE p.owner_id = %s
            ORDER BY r.room_number
        """, (owner_id,))
        
        all_rooms = cur.fetchall()
        available_rooms = []
        for r in all_rooms:
            r_id, r_num, r_cap, r_rent, r_occ = r
            if r_occ < r_cap:
                available_rooms.append({
                    'id': r_id,
                    'number': r_num,
                    'available': r_cap - r_occ,
                    'rent': r_rent
                })
        
        cur.close()
        conn.close()
    else:
        available_rooms = []

    return render_template('owner/add_tenant.html', rooms=available_rooms)

@bp.route('/owner/export/tenants')
@role_required('OWNER')
def export_tenants():
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        cur.execute("""
            SELECT full_name, email, phone_number, room_number, 
                   monthly_rent, security_deposit, onboarding_status, 
                   lease_start, lease_end
            FROM tenants
            WHERE owner_id = %s
            ORDER BY room_number
        """, (owner_id,))
        
        rows = cur.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Full Name', 'Email', 'Phone', 'Room', 'Rent', 'Deposit', 'Status', 'Lease Start', 'Lease End'])
        
        for row in rows:
            row_list = list(row)
            if row_list[2]:
                row_list[2] = f"'{row_list[2]}" 
            writer.writerow(row_list)
            
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=tenants_export.csv"}
        )
        
    except Exception as e:
        print(f"Error exporting tenants: {e}")
        return f"Export Error: {str(e)}", 500
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/tenants/update-status', methods=['POST'])
@role_required('OWNER')
def update_tenant_status():
    tenant_id = request.form.get('tenant_id')
    new_status = request.form.get('status')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if new_status == 'REJECTED':
             cur.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
             flash("Draft tenant rejected and removed.", "success")
        elif new_status == 'ACTIVE':
             # Fetch tenant and property info for Welcome Kit
             cur.execute("""
                 SELECT t.full_name, t.email, t.room_number, p.name, p.wifi_ssid, p.wifi_password, 
                        p.gate_closing_time, p.house_rules
                 FROM tenants t
                 JOIN properties p ON t.owner_id = p.owner_id
                 WHERE t.id = %s
             """, (tenant_id,))
             t_data = cur.fetchone()
             
             cur.execute("UPDATE tenants SET onboarding_status = 'ACTIVE' WHERE id = %s", (tenant_id,))
             conn.commit()
             
             if t_data and t_data[1]: # If they have an email
                 send_email(
                     to_email=t_data[1],
                     subject=f"Welcome to {t_data[3]}!",
                     template="emails/welcome_kit.html",
                     tenant_name=t_data[0],
                     room_number=t_data[2],
                     property_name=t_data[3],
                     wifi_ssid=t_data[4],
                     wifi_password=t_data[5],
                     gate_closing_time=t_data[6],
                     house_rules=t_data[7]
                 )
             flash("Tenant activated! Welcome Kit sent.", "success")
        else:
             cur.execute("UPDATE tenants SET onboarding_status = %s WHERE id = %s", (new_status, tenant_id))
             conn.commit()
             flash(f"Tenant status updated to {new_status}", "success")
             
    except Exception as e:
        conn.rollback()
        print(f"Error updating status: {e}")
        flash("Failed to update status", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_tenants'))

@bp.route('/owner/tenants/remind/<tenant_id>', methods=['POST'])
@role_required('OWNER')
def remind_tenant(tenant_id):
    method = request.form.get('method') # 'email' or 'whatsapp'
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.full_name, t.email, t.phone_number, t.room_number, t.monthly_rent, o.full_name, p.name
            FROM tenants t
            JOIN owners o ON t.owner_id = o.id
            JOIN properties p ON t.owner_id = p.owner_id
            WHERE t.id = %s
        """, (tenant_id,))
        row = cur.fetchone()
        
        if not row:
            flash("Tenant not found", "error")
            return redirect(url_for('main.owner_tenants'))
            
        t_name, t_email, t_phone, t_room, t_rent, o_name, p_name = row
        
        if method == 'email':
            if not t_email:
                flash("Tenant has no email address", "error")
            else:
                success = send_email(
                    to_email=t_email,
                    subject=f"Rent Reminder - {p_name}",
                    template="emails/rent_reminder.html",
                    tenant_name=t_name,
                    rent_amount=t_rent,
                    room_number=t_room,
                    payment_month=datetime.now().strftime('%B %Y'),
                    owner_name=o_name,
                    dashboard_url=url_for('main.tenant_dashboard', _external=True)
                )
                if success: flash(f"Reminder email sent to {t_name}", "success")
                else: flash("Failed to send email", "error")
        
        elif method == 'whatsapp':
            # This is handled client-side but we could log it here if needed
            flash("WhatsApp reminder link generated", "success")

    except Exception as e:
        print(f"Remind Error: {e}")
        flash("Error processing reminder", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_tenants'))

def process_bulk_reminders(app, user_id, dashboard_url):
    """Background worker for sending bulk reminders"""
    with app.app_context():
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            print(f"Starting bulk reminder process for User {user_id}")
            current_month = datetime.now().strftime('%B %Y')
            
            # 1. Get Owner & Property Info
            cur.execute("""
                SELECT o.id, o.full_name, p.name 
                FROM owners o
                JOIN properties p ON o.id = p.owner_id
                WHERE o.user_id = %s
                LIMIT 1
            """, (user_id,))
            owner_data = cur.fetchone()
            
            if not owner_data:
                print("Owner not found in background task")
                return
                
            owner_id, owner_name, property_name = owner_data
            
            # 2. Get active tenants
            cur.execute("""
                SELECT t.id, t.full_name, t.email, t.room_number, t.monthly_rent
                FROM tenants t
                WHERE t.owner_id = %s AND t.onboarding_status = 'ACTIVE'
            """, (owner_id,))
            
            tenants = cur.fetchall()
            
            count = 0
            for t in tenants:
                t_id, t_name, t_email, t_room, t_rent = t
                
                # Check payment status
                cur.execute("""
                    SELECT id FROM payments 
                    WHERE tenant_id = %s 
                    AND EXTRACT(MONTH FROM payment_date) = EXTRACT(MONTH FROM CURRENT_DATE)
                    AND EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND status = 'APPROVED'
                """, (t_id,))
                
                if cur.fetchone():
                    continue 
                    
                if t_email:
                    try:
                        send_email(
                            to_email=t_email,
                            subject=f"Rent Reminder - {property_name}",
                            template="emails/rent_reminder.html",
                            tenant_name=t_name,
                            rent_amount=t_rent,
                            room_number=t_room,
                            payment_month=current_month,
                            owner_name=owner_name,
                            dashboard_url=dashboard_url
                        )
                        count += 1
                    except Exception as email_err:
                        print(f"Failed to send to {t_email}: {email_err}")
            
            print(f"Bulk Process Complete. Sent {count} emails.")

        except Exception as e:
            print(f"Bulk Reminder Background Error: {e}")
        finally:
            cur.close()
            conn.close()

@bp.route('/owner/tenants/remind-all', methods=['POST'])
@role_required('OWNER')
def remind_all_tenants():
    # Capture legitimate app object and context data
    app = current_app._get_current_object()
    user_id = session.get('user_id')
    dashboard_url = url_for('main.tenant_dashboard', _external=True)
    
    # Spawn background thread
    thread = threading.Thread(target=process_bulk_reminders, args=(app, user_id, dashboard_url))
    thread.daemon = True
    thread.start()
    
    flash("Background process started! Emails are being sent.", "success")
    return redirect(request.referrer or url_for('main.owner_dashboard'))

@bp.route('/owner/tenants/<tenant_id>')
@role_required('OWNER')
def owner_tenant_details(tenant_id):
    return render_template('owner/tenant_details.html', tenant_id=tenant_id)
