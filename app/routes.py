
import os
import json
import uuid
import psycopg2
from flask import Blueprint, jsonify, redirect, render_template, request, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.database.database import get_db_connection

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    if 'user_id' in session:
        if session.get('role') == 'OWNER':
            return redirect(url_for('main.owner_dashboard'))
        elif session.get('role') == 'TENANT':
             return redirect(url_for('main.tenant_dashboard'))
            
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


# --- Owner Routes ---

@bp.app_template_filter('time_ago')
def time_ago(date):
    if not date: return ''
    from datetime import datetime, timezone, date as d
    
    # Handle datetime.date objects (no time)
    if not isinstance(date, datetime) and isinstance(date, d):
        date = datetime.combine(date, datetime.min.time())
        
    now = datetime.now(timezone.utc) if date.tzinfo else datetime.now()
    
    diff = now - date
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        return f'{int(seconds // 60)} mins ago'
    elif seconds < 86400:
        return f'{int(seconds // 3600)} hours ago'
    else:
        return f'{int(seconds // 86400)} days ago'

@bp.route('/owner/dashboard')
def owner_dashboard():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    # Import datetime here to ensure it's available
    from datetime import datetime, timedelta, timezone
    
    conn = get_db_connection()
    if not conn: 
        return render_template('owner/dashboard.html', 
                             name=session.get('name', 'Owner'),
                             total_income=0,
                             total_spent=0,
                             net_profit=0,
                             occupancy_rate=0,
                             occupancy_rotation=0,
                             occupancy_rotation_style="transform: rotate(0deg);",
                             available_beds=0,
                             total_occupied=0,
                             tenants_paid=0,
                             tenants_pending=0,
                             collection_percentage=0,
                             rent_collection_style="width: 0%;",
                             expiring_leases=[],
                             recent_movements=[],
                             pending_complaints=[],
                             high_priority_count=0,
                             recent_activity=[])
    
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_row = cur.fetchone()
        if not owner_row:
             return render_template('owner/dashboard.html', 
                                  name=session.get('name', 'Owner'),
                                  total_income=0,
                                  total_spent=0,
                                  net_profit=0,
                                  occupancy_rate=0,
                                  occupancy_rotation=0,
                                  occupancy_rotation_style="transform: rotate(0deg);",
                                  available_beds=0,
                                  total_occupied=0,
                                  tenants_paid=0,
                                  tenants_pending=0,
                                  collection_percentage=0,
                                  rent_collection_style="width: 0%;",
                                  expiring_leases=[],
                                  recent_movements=[],
                                  pending_complaints=[],
                                  pending_approvals=[],
                                  high_priority_count=0,
                                  recent_activity=[])
        
        owner_id = owner_row[0]
        
        # Calculate Total Monthly Potential Income (Sum of rents of ACTIVE tenants only)
        cur.execute("SELECT SUM(monthly_rent) FROM tenants WHERE owner_id = %s AND onboarding_status = 'ACTIVE'", (owner_id,))
        total_income = cur.fetchone()[0] or 0
        
        # 2. Calculate Total Spent (Sum of expenses for current month)
        cur.execute("""
            SELECT SUM(amount) FROM expenses 
            WHERE owner_id = %s AND expense_month = %s
        """, (owner_id, datetime.now().strftime('%Y-%m')))
        total_spent = cur.fetchone()[0] or 0
        
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
        
        # 2. Total Tenants (Occupied Beds - Exclude Drafts/Past)
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s AND onboarding_status IN ('ACTIVE', 'PENDING', 'NOTICE')", (owner_id,))
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
        # Total Collected (Payments this month - COMPLETED ONLY)
        cur.execute("""
            SELECT COUNT(DISTINCT tenant_id), COALESCE(SUM(amount), 0)
            FROM payments
            JOIN tenants ON payments.tenant_id = tenants.id
            WHERE tenants.owner_id = %s AND payment_month = %s AND payments.status = 'COMPLETED'
        """, (owner_id, current_month))
        payment_row = cur.fetchone()
        
        tenants_paid = payment_row[0] or 0
        total_collected = payment_row[1] or 0
        
        tenants_pending = max(0, total_active_tenants - tenants_paid)
        
        # Progress Calculation
        if total_expected_rent > 0:
            collection_percentage = int((total_collected / total_expected_rent) * 100)
        else:
            collection_percentage = 0
            
        rent_collection_style = f"width: {collection_percentage}%;"

        # 5. Fetch Pending Payments & Approvals
        cur.execute("""
            SELECT p.id, t.full_name, p.amount, p.payment_date, p.remarks, t.room_number 
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.id
            WHERE t.owner_id = %s AND p.status = 'PENDING'
            ORDER BY p.created_at DESC
            LIMIT 3
        """, (owner_id,))
        pending_approvals = cur.fetchall()
        
        # Count total pending for "View All" link
        cur.execute("SELECT COUNT(*) FROM payments p JOIN tenants t ON p.tenant_id = t.id WHERE t.owner_id = %s AND p.status = 'PENDING'", (owner_id,))
        total_pending_count = cur.fetchone()[0] or 0

         # 5. Lease Expiries (Next 30 Days)
        thirty_days_later = datetime.now().date() + timedelta(days=30)
        
        cur.execute("""
            SELECT full_name, lease_end, 
                   (lease_end - CURRENT_DATE) as days_remaining 
            FROM tenants 
            WHERE owner_id = %s 
              AND lease_end BETWEEN CURRENT_DATE AND %s
              AND onboarding_status = 'ACTIVE'
            ORDER BY lease_end ASC
            LIMIT 5
        """, (owner_id, thirty_days_later))
        expiring_leases = cur.fetchall()
        
        # 6. New Movements (Recent Check-ins in last 30 days)
        cur.execute("""
            SELECT full_name, room_number, created_at
            FROM tenants
            WHERE owner_id = %s 
            ORDER BY created_at DESC
            LIMIT 3
        """, (owner_id,))
        recent_movements = cur.fetchall()
        
        # 7. Pending Complaints (High Priority First)
        cur.execute("""
            SELECT c.title, t.room_number, t.full_name, c.priority, c.description
            FROM complaints c
            JOIN tenants t ON c.tenant_id = t.id
            WHERE c.owner_id = %s AND c.status = 'PENDING'
            ORDER BY 
                CASE c.priority 
                    WHEN 'HIGH' THEN 1 
                    WHEN 'MEDIUM' THEN 2 
                    WHEN 'LOW' THEN 3 
                END, 
                c.created_at DESC
            LIMIT 3
        """, (owner_id,))
        pending_complaints = cur.fetchall()
        
        # Count total high priority pending
        cur.execute("""
            SELECT COUNT(*) FROM complaints 
            WHERE owner_id = %s AND status = 'PENDING' AND priority = 'HIGH'
        """, (owner_id,))
        high_priority_count = cur.fetchone()[0] or 0

        # 8. Recent Activity Feed (Aggregated)
        # (This query remains the same as previously viewed)
        cur.execute("""
            SELECT type, title, description, created_at, metadata FROM (
                SELECT 'PAYMENT' as type, 
                       'Rent Received' as title, 
                       'From ' || t.full_name || ' (₹' || p.amount || ')' as description, 
                       p.created_at,
                       'green' as metadata
                FROM payments p 
                JOIN tenants t ON p.tenant_id = t.id 
                WHERE t.owner_id = %s
                
                UNION ALL
                
                SELECT 'MOVEMENT' as type, 
                       'New Tenant' as title, 
                       full_name || ' joined Room ' || room_number as description, 
                       created_at,
                       'blue' as metadata
                FROM tenants 
                WHERE owner_id = %s
                
                UNION ALL
                
                SELECT 'COMPLAINT' as type, 
                       'New Complaint' as title, 
                       title || ' in Room ' || (SELECT room_number FROM tenants WHERE id = complaints.tenant_id) as description, 
                       created_at,
                       'red' as metadata
                FROM complaints 
                WHERE owner_id = %s
            ) as activity
            ORDER BY created_at DESC
            LIMIT 5
        """, (owner_id, owner_id, owner_id))
        recent_activity = cur.fetchall()
        
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
                             tenants_paid=tenants_paid,
                             tenants_pending=tenants_pending,
                             collection_percentage=collection_percentage,
                             rent_collection_style=rent_collection_style,
                             expiring_leases=expiring_leases,
                             recent_movements=recent_movements,
                             pending_complaints=pending_complaints,
                             pending_approvals=pending_approvals,
                             total_pending_count=total_pending_count,
                             high_priority_count=high_priority_count,
                             recent_activity=recent_activity)
                             
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return render_template('owner/dashboard.html', 
                             name=session.get('name', 'Owner'),
                             total_income=0,
                             total_spent=0,
                             net_profit=0,
                             occupancy_rate=0,
                             occupancy_rotation=0,
                             occupancy_rotation_style="transform: rotate(0deg);",
                             available_beds=0,
                             total_occupied=0,
                             tenants_paid=0,
                             tenants_pending=0,
                             collection_percentage=0,
                             rent_collection_style="width: 0%;",
                             expiring_leases=[],
                             recent_movements=[],
                             pending_complaints=[],
                             pending_approvals=[],
                             high_priority_count=0,
                             recent_activity=[])
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/payment/approve/<payment_id>', methods=['POST'])
def approve_payment(payment_id):
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE payments SET status = 'COMPLETED' WHERE id = %s", (payment_id,))
        conn.commit()
        flash("Payment verified successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash("Error verifying payment.", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('main.owner_dashboard'))

@bp.route('/owner/payment/reject/<payment_id>', methods=['POST'])
def reject_payment(payment_id):
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE payments SET status = 'FAILED' WHERE id = %s", (payment_id,))
        conn.commit()
        flash("Payment rejected.", "info")
    except Exception as e:
        conn.rollback()
        flash("Error rejecting payment.", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('main.owner_dashboard'))


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
        filter_type = request.args.get('filter', 'all')
        
        # Base Query
        query = """
            SELECT id, full_name, email, phone_number, room_number, 
                   onboarding_status, monthly_rent, created_at 
            FROM tenants 
            WHERE owner_id = %s 
        """
        params = [owner_id]
        
        # Apply Filters
        if filter_type == 'active':
            query += " AND onboarding_status = 'ACTIVE'"
        elif filter_type == 'rent-due':
            # Active tenants who strictly haven't paid properly for the current month
            import datetime
            current_month = datetime.datetime.now().strftime('%Y-%m')
            query += """ 
                AND onboarding_status = 'ACTIVE'
                AND id NOT IN (
                    SELECT tenant_id FROM payments 
                    WHERE payment_month = %s AND status = 'COMPLETED'
                )
            """
            params.append(current_month)
        elif filter_type == 'lease-expiring':
            # Expiring in next 30 days
            query += " AND onboarding_status = 'ACTIVE' AND lease_end BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'"
        elif filter_type == 'past':
            query += " AND onboarding_status IN ('EXITED', 'LEFT', 'MOVED_OUT', 'REJECTED')"
        
        # Apply Search
        search_query = request.args.get('search')
        if search_query:
            query += " AND (full_name ILIKE %s OR email ILIKE %s OR room_number ILIKE %s)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY created_at DESC"
        
        # --- PAGINATION ---
        page = request.args.get('page', 1, type=int)
        per_page = 3
        offset = (page - 1) * per_page
        
        # Count Total Matches (for this filter/search)
        count_query = f"SELECT COUNT(*) FROM ({query}) AS sub"
        cur.execute(count_query, tuple(params))
        total_count = cur.fetchone()[0]
        
        # Add LIMIT/OFFSET
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cur.execute(query, tuple(params))
        
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
            
        import math
        total_pages = math.ceil(total_count / per_page)
        
        pagination = {
            'current_page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'total_count': total_count,
            'per_page': per_page
        }

        # Check for AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return render_template('owner/partials/tenant_list_with_pagination.html', tenants=tenants, pagination=pagination)

        # Stats (Need separate query independent of pagination/filtering?)
        # For now, stats are global or per filter? Let's keep stats global for the top cards.
        # But wait, original code did stats calculation on `tenants` list. Now `tenants` is paginated.
        # We need to fetch global stats separately to keep the top cards accurate.
        
        # Global Tenant Count
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s", (owner_id,))
        global_total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s AND onboarding_status = 'ACTIVE'", (owner_id,))
        global_active = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s AND onboarding_status = 'NOTICE'", (owner_id,))
        global_notice = cur.fetchone()[0]

        import datetime
        current_month = datetime.datetime.now().strftime('%Y-%m')
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
                
            # 1.5 Check if email already registered in system (as User/Owner)
            cur.execute("SELECT id, role FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                flash(f"Email '{email}' is already registered as a {existing_user[1]}. Cannot add as new tenant.", "error")
                return redirect(url_for('main.owner_add_tenant'))

            # 2. Check if Phone Number already exists
            if phone:
                cur.execute("SELECT id FROM tenants WHERE phone_number = %s AND owner_id = %s", (phone, owner_id))
                if cur.fetchone():
                    flash(f"Tenant with phone number '{phone}' is already added.", "error")
                    return redirect(url_for('main.owner_add_tenant'))
                
            # Determine Status
            action = request.form.get('action')
            status = 'DRAFT' if action == 'draft' else 'PENDING'
            
            # Lookup Room ID
            cur.execute("""
                SELECT r.id FROM rooms r
                JOIN properties p ON r.property_id = p.id
                WHERE p.owner_id = %s AND r.room_number = %s
            """, (owner_id, room_no))
            room_row = cur.fetchone()
            room_id = room_row[0] if room_row else None

            # Insert Tenant
            cur.execute("""
                INSERT INTO tenants (owner_id, full_name, email, phone_number, room_number, room_id, monthly_rent, onboarding_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (owner_id, full_name, email, phone, room_no, room_id, rent, status))
            
            conn.commit()
            if status == 'DRAFT':
                flash("Tenant details saved as Draft.", "success")
            else:
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

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # Fetch Rooms with Availability
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


@bp.route('/owner/settings')
def owner_settings():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT o.id, o.full_name, o.phone_number, u.email,
                   o.account_holder_name, o.bank_name, o.account_number, o.ifsc_code, o.upi_id,
                   o.preferences, o.qr_code_url, o.qr_code_data
            FROM owners o
            JOIN users u ON o.user_id = u.id
            WHERE o.user_id = %s
        """, (session.get('user_id'),))
        owner_row = cur.fetchone()
        
        if not owner_row: return redirect(url_for('main.login'))
        
        owner_id = owner_row[0]
        # Determine QR URL: Use DB route if data exists, else fallback to old URL logic
        qr_url = owner_row[10]
        if owner_row[11]: # If BLOB data exists
             qr_url = url_for('main.owner_qr_image', owner_id=owner_id)

        owner = {
            'full_name': owner_row[1],
            'phone_number': owner_row[2],
            'email': owner_row[3],
            'account_holder_name': owner_row[4],
            'bank_name': owner_row[5],
            'account_number': owner_row[6],
            'ifsc_code': owner_row[7],
            'upi_id': owner_row[8],
            'preferences': owner_row[9] or {'email_alerts': True, 'sms_alerts': True, 'dark_mode': False},
            'qr_code_url': qr_url
        }
        
        # Fetch Property Details (Assuming single property for now)
        cur.execute("""
            SELECT id, wifi_ssid, wifi_password, gate_closing_time, 
                   breakfast_start_time, breakfast_end_time, house_rules,
                   late_fee_daily, rent_grace_period_days
            FROM properties WHERE owner_id = %s LIMIT 1
        """, (owner_id,))
        prop_row = cur.fetchone()
        
        property_obj = {}
        if prop_row:
             property_obj = {
                'id': prop_row[0],
                'wifi_ssid': prop_row[1],
                'wifi_password': prop_row[2],
                'gate_closing_time': prop_row[3],
                'breakfast_start_time': prop_row[4],
                'breakfast_end_time': prop_row[5],
                'house_rules': prop_row[6],
                'late_fee_daily': prop_row[7],
                'rent_grace_period_days': prop_row[8]
             }
        
        return render_template('owner/settings.html', owner=owner, property=property_obj)
        
    except Exception as e:
        print(f"Error fetching settings: {e}")
        # Return object with minimal required fields to prevent template crash
        return render_template('owner/settings.html', owner={'preferences': {}}, property={})
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/settings/update', methods=['POST'])
def owner_settings_update():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    # Helper to clean empty strings to None
    def clean(val):
        return val if val and val.strip() != "" else None

    # Helper for integers (default to 0 if invalid/empty)
    def clean_int(val, default=0):
        try:
            if not val or val.strip() == "": return default
            return int(val)
        except ValueError:
            return default

    # 1. Profile Data
    full_name = clean(request.form.get('full_name'))
    phone_number = clean(request.form.get('phone_number'))
    
    # 2. Billing Data
    upi_id = clean(request.form.get('upi_id'))
    account_holder = clean(request.form.get('account_holder_name'))
    bank_name = clean(request.form.get('bank_name'))
    account_number = clean(request.form.get('account_number'))
    ifsc_code = clean(request.form.get('ifsc_code'))
    
    # Integers
    late_fee = clean_int(request.form.get('late_fee_daily'), 0)
    grace_period = clean_int(request.form.get('rent_grace_period_days'), 5)
    
    # 3. Property Rules
    wifi_ssid = clean(request.form.get('wifi_ssid'))
    wifi_password = clean(request.form.get('wifi_password'))
    
    # Time Fields (Must be None if empty, else Postgres errs)
    gate_closing = clean(request.form.get('gate_closing_time'))
    breakfast_start = clean(request.form.get('breakfast_start_time'))
    breakfast_end = clean(request.form.get('breakfast_end_time'))
    
    house_rules = clean(request.form.get('house_rules'))
    
    # 4. Preferences
    email_alerts = 'on' in request.form if 'email_alerts' in request.form else False
    sms_alerts = 'on' in request.form if 'sms_alerts' in request.form else False
    dark_mode = 'on' in request.form if 'dark_mode' in request.form else False
    
    preferences = json.dumps({
        'email_alerts': email_alerts,
        'sms_alerts': sms_alerts,
        'dark_mode': dark_mode
    })
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # QR Code Upload Handling (Database Storage)
        qr_binary = None
        if 'qr_code' in request.files:
            file = request.files['qr_code']
            if file and file.filename != '':
                qr_binary = file.read() # Read file into memory
                
        # Update Owner
        # Dynamic SQL: Update blob if present
        if qr_binary:
            cur.execute("""
                UPDATE owners 
                SET full_name = %s, phone_number = %s, 
                    upi_id = %s, account_holder_name = %s, bank_name = %s, 
                    account_number = %s, ifsc_code = %s, preferences = %s,
                    qr_code_data = %s
                WHERE id = %s
            """, (full_name, phone_number, upi_id, account_holder, bank_name, 
                  account_number, ifsc_code, preferences, psycopg2.Binary(qr_binary), owner_id))
        else:
             cur.execute("""
                UPDATE owners 
                SET full_name = %s, phone_number = %s, 
                    upi_id = %s, account_holder_name = %s, bank_name = %s, 
                    account_number = %s, ifsc_code = %s, preferences = %s
                WHERE id = %s
            """, (full_name, phone_number, upi_id, account_holder, bank_name, 
                  account_number, ifsc_code, preferences, owner_id))
              
        # Update Property
        # Check if property exists first, if not create one
        cur.execute("SELECT id FROM properties WHERE owner_id = %s", (owner_id,))
        if cur.fetchone():
            cur.execute("""
                UPDATE properties
                SET wifi_ssid = %s, wifi_password = %s, gate_closing_time = %s,
                    breakfast_start_time = %s, breakfast_end_time = %s, house_rules = %s,
                     late_fee_daily = %s, rent_grace_period_days = %s
                WHERE owner_id = %s
            """, (wifi_ssid, wifi_password, gate_closing, breakfast_start, breakfast_end, house_rules, late_fee, grace_period, owner_id))
        else:
             cur.execute("""
                INSERT INTO properties (owner_id, name, wifi_ssid, wifi_password, gate_closing_time, 
                                        breakfast_start_time, breakfast_end_time, house_rules, late_fee_daily, rent_grace_period_days)
                VALUES (%s, 'Main Building', %s, %s, %s, %s, %s, %s, %s, %s)
            """, (owner_id, wifi_ssid, wifi_password, gate_closing, breakfast_start, breakfast_end, house_rules, late_fee, grace_period))
        
        conn.commit()
        flash("Settings updated successfully!", "success")
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating settings: {e}")
        flash(f"Failed to update settings. Error: {str(e)}", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_settings'))


@bp.route('/owner/export/tenants')
def export_tenants():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    import csv
    import io
    from flask import Response
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # Fetch Tenant Data (Real)
        cur.execute("""
            SELECT full_name, email, phone_number, room_number, 
                   monthly_rent, security_deposit, onboarding_status, 
                   lease_start, lease_end
            FROM tenants
            WHERE owner_id = %s
            ORDER BY room_number
        """, (owner_id,))
        
        rows = cur.fetchall()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Full Name', 'Email', 'Phone', 'Room', 'Rent', 'Deposit', 'Status', 'Lease Start', 'Lease End'])
        
        # Data
        for row in rows:
            # Convert row to list to modify
            row_list = list(row)
            # Prepend ' to phone number (index 2) to force Excel string format
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


@bp.route('/owner/qr-image/<owner_id>')
def owner_qr_image(owner_id):
    import io
    from flask import send_file
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT qr_code_data FROM owners WHERE id = %s", (owner_id,))
        row = cur.fetchone()
        if row and row[0]:
            return send_file(
                io.BytesIO(row[0]),
                mimetype='image/png', 
                as_attachment=False,
                download_name='qr_code.png'
            )
        else:
            return "No Image", 404
    except Exception as e:
        print(f"Error serving image: {e}")
        return "Error", 500
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/tenants/update-status', methods=['POST'])
def update_tenant_status():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    tenant_id = request.form.get('tenant_id')
    new_status = request.form.get('status')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if new_status == 'REJECTED':
             cur.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
             flash("Draft tenant rejected and removed.", "success")
        else:
             cur.execute("UPDATE tenants SET onboarding_status = %s WHERE id = %s", (new_status, tenant_id))
             flash(f"Tenant status updated to {new_status}", "success")
             
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash("Failed to update status", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_tenants'))

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
                # Count current tenants in this room (Include ACTIVE, PENDING, NOTICE, DRAFT)
                cur.execute("SELECT COUNT(*) FROM tenants WHERE room_id = %s AND onboarding_status IN ('ACTIVE', 'PENDING', 'NOTICE', 'DRAFT')", (r_id,))
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


@bp.route('/owner/properties/edit-room', methods=['POST'])
def edit_room():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    room_id = request.form.get('room_id')
    room_number = request.form.get('room_number')
    floor = request.form.get('floor')
    capacity = request.form.get('capacity')
    rent = request.form.get('rent_amount')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Verify ownership via property
        cur.execute("""
            SELECT r.id FROM rooms r
            JOIN properties p ON r.property_id = p.id
            JOIN owners o ON p.owner_id = o.id
            WHERE r.id = %s AND o.user_id = %s
        """, (room_id, session.get('user_id')))
        
        if not cur.fetchone():
            flash("Unauthorized or Room not found", "error")
            return redirect(url_for('main.owner_properties'))

        cur.execute("""
            UPDATE rooms 
            SET room_number = %s, floor_number = %s, capacity = %s, rent_amount = %s
            WHERE id = %s
        """, (room_number, floor, capacity, rent, room_id))
        
        conn.commit()
        flash("Room details updated successfully!", "success")
        
    except Exception as e:
        conn.rollback()
        print(f"Error editing room: {e}")
        if "unique constraint" in str(e).lower():
            flash("Room number already exists!", "error")
        else:
            flash("Failed to update room", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_properties'))

from datetime import datetime

@bp.route('/owner/finance')
def owner_finance():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Defaults
    current_date = datetime.now()
    current_month_str = current_date.strftime('%Y-%m')
    current_month_name = current_date.strftime('%B %Y')
    
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        # 1. Fetch Income (Tenants)
        cur.execute("""
            SELECT t.id, t.full_name, t.room_number, t.monthly_rent,
                   p.amount, p.payment_date
            FROM tenants t
            LEFT JOIN payments p ON t.id = p.tenant_id AND p.payment_month = %s AND p.status = 'COMPLETED'
            WHERE t.owner_id = %s AND t.onboarding_status IN ('ACTIVE', 'NOTICE')
            ORDER BY t.room_number
        """, (current_month_str, owner_id))
        
        income_rows = cur.fetchall()
        tenants = []
        total_income = 0
        
        for row in income_rows:
            is_paid = row[4] is not None
            paid_amount = row[4] if is_paid else 0
            total_income += paid_amount
            
            tenants.append({
                'id': row[0],
                'name': row[1],
                'room': row[2],
                'rent': int(row[3]),
                'payment_status': 'PAID' if is_paid else 'PENDING',
                'paid_amount': paid_amount,
                'paid_date': row[5].strftime('%d %b') if row[5] else None
            })

        # 2. Fetch Expenses
        cur.execute("""
            SELECT id, category, amount, description, expense_date 
            FROM expenses 
            WHERE owner_id = %s AND expense_month = %s
            ORDER BY expense_date DESC
        """, (owner_id, current_month_str))
        
        expense_rows = cur.fetchall()
        expenses = []
        total_expenses = 0
        
        for row in expense_rows:
            amount = row[2]
            total_expenses += amount
            expenses.append({
                'id': row[0],
                'category': row[1],
                'amount': amount,
                'description': row[3],
                'date': row[4].strftime('%d %b')
            })
            
        # Fetch Pending Approvals (ALL)
        cur.execute("""
            SELECT p.id, t.full_name, p.amount, p.payment_date, p.remarks, t.room_number, p.created_at 
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.id
            WHERE t.owner_id = %s AND p.status = 'PENDING'
            ORDER BY p.created_at DESC
        """, (owner_id,))
        pending_approvals_rows = cur.fetchall()

        pending_approvals = []
        for row in pending_approvals_rows:
            pending_approvals.append({
                'id': row[0],
                'tenant_name': row[1],
                'amount': row[2],
                'payment_date': row[3].strftime('%d %b %Y'),
                'remarks': row[4],
                'room_number': row[5],
                'created_at': row[6].strftime('%d %b %Y %H:%M')
            })

        cur.close()
        conn.close()
        
        return render_template('owner/finance.html', 
                             tenants=tenants,
                             expenses=expenses,
                             pending_approvals=pending_approvals,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             net_profit=total_income - total_expenses,
                             current_month_name=current_month_name,
                             current_date=current_date.strftime('%Y-%m-%d'))
                             
    except Exception as e:
        print(f"Error fetching finance data: {e}")
        return render_template('owner/finance.html', tenants=[], expenses=[], current_month_name=current_month_name)

@bp.route('/owner/record-payment', methods=['POST'])
def owner_record_payment():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    tenant_id = request.form.get('tenant_id')
    amount = request.form.get('amount')
    payment_date_str = request.form.get('payment_date')
    mode = request.form.get('payment_mode')
    remarks = request.form.get('remarks')
    
    payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d')
    payment_month = payment_date.strftime('%Y-%m')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO payments (tenant_id, amount, payment_date, payment_month, status, payment_mode, remarks)
            VALUES (%s, %s, %s, %s, 'COMPLETED', %s, %s)
        """, (tenant_id, amount, payment_date, payment_month, mode, remarks))
        conn.commit()
        flash("Payment recorded!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error recording payment: {e}")
        flash("Failed to record payment", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_finance'))

@bp.route('/owner/add-expense', methods=['POST'])
def owner_add_expense():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    category = request.form.get('category')
    amount = request.form.get('amount')
    date_str = request.form.get('expense_date')
    description = request.form.get('description')
    
    expense_date = datetime.strptime(date_str, '%Y-%m-%d')
    expense_month = expense_date.strftime('%Y-%m')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO expenses (owner_id, category, amount, description, expense_date, expense_month)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (owner_id, category, amount, description, expense_date, expense_month))
        
        conn.commit()
        flash("Expense added!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error adding expense: {e}")
        flash("Failed to add expense", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_finance'))

@bp.route('/owner/complaints')
def owner_complaints():
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    status_filter = request.args.get('status', 'PENDING')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        cur.execute("""
            SELECT c.id, c.title, c.description, c.priority, c.status, c.created_at,
                   t.full_name, t.room_number
            FROM complaints c
            JOIN tenants t ON c.tenant_id = t.id
            WHERE c.owner_id = %s AND c.status = %s
            ORDER BY 
                CASE c.priority 
                    WHEN 'HIGH' THEN 1 
                    WHEN 'MEDIUM' THEN 2 
                    WHEN 'LOW' THEN 3 
                END, 
                c.created_at DESC
        """, (owner_id, status_filter))
        
        complaints = []
        rows = cur.fetchall()
        for row in rows:
            complaints.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'priority': row[3],
                'status': row[4],
                'created_at': row[5],
                'tenant_name': row[6],
                'room_number': row[7]
            })
            
        cur.close()
        conn.close()
        
        return render_template('owner/complaints.html', 
                             complaints=complaints, 
                             status_filter=status_filter)
                             
    except Exception as e:
        print(f"Error fetching complaints: {e}")
        return render_template('owner/complaints.html', complaints=[], status_filter=status_filter)

@bp.route('/owner/complaints/resolve/<uuid:complaint_id>', methods=['POST'])
def resolve_complaint(complaint_id):
    if session.get('role') != 'OWNER': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE complaints SET status = 'RESOLVED' WHERE id = %s", (str(complaint_id),))
        conn.commit()
        flash("Complaint marked as resolved!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error resolving complaint: {e}")
        flash("Failed to update complaint", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_complaints', status='PENDING'))


@bp.route('/tenant/dashboard')
def tenant_dashboard():
    if session.get('role') != 'TENANT': return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch Tenant Details
        cur.execute("""
            SELECT t.id, t.full_name, t.room_number, t.bed_number, t.phone_number, t.email, t.monthly_rent, t.onboarding_status
            FROM tenants t
            WHERE t.user_id = %s
        """, (session.get('user_id'),))
        tenant = cur.fetchone()
        
        if not tenant:
            flash("Tenant record not found.", "error")
            return redirect(url_for('main.login'))

        # Check Rent Status for Current Month
        from datetime import datetime
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
            
        # Fetch Owner Payment Details
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

        return render_template('tenant/dashboard.html', tenant=tenant_data)
    except Exception as e:
        return render_template('tenant/dashboard.html',
                         tenant=tenant_data,
                         current_date=datetime.now())
    finally:
        cur.close()
        conn.close()

@bp.route('/tenant/pay', methods=['POST'])
def tenant_pay_rent():
    if session.get('role') != 'TENANT': return redirect(url_for('main.login'))

    amount = request.form['amount']
    txn_id = request.form['transaction_id']
    tenant_id = request.form['tenant_id']
    payment_month = datetime.now().strftime('%Y-%m') # Current month payment

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if already paid/pending for this month to prevent duplicates
        cur.execute("""
            SELECT id FROM payments
            WHERE tenant_id = %s AND payment_month = %s AND status IN ('COMPLETED', 'PENDING')
        """, (tenant_id, payment_month))

        if cur.fetchone():
            flash("Payment for this month is already recorded or pending.", "warning")
            return redirect(url_for('main.tenant_dashboard'))

        # Fetch Owner ID from Tenant
        cur.execute("SELECT owner_id FROM tenants WHERE id = %s", (tenant_id,))
        owner_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO payments (id, tenant_id, owner_id, amount, payment_date, payment_month, payment_method, remarks, status)
            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, 'UPI', %s, 'PENDING')
        """, (str(uuid.uuid4()), tenant_id, owner_id, amount, payment_month, f"Txn Ref: {txn_id}"))

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
def tenant_complaints():
    if session.get('role') != 'TENANT': return redirect(url_for('main.login'))

    user_id = session.get('user_id')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Get Tenant ID
        cur.execute("SELECT id, full_name, email FROM tenants WHERE user_id = %s", (user_id,))
        tenant = cur.fetchone()

        if not tenant:
            return "Tenant profile not found", 404

        tenant_id = tenant[0]

        # Fetch Complaints
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
def tenant_raise_complaint():
    if session.get('role') != 'TENANT': return redirect(url_for('main.login'))

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
    from flask import send_file

    # Generate QR Code content (e.g., JSON with ID and Name for easy scanning)
    # In a real app, this might be a signed token.
    qr_content = f"TENANT:{tenant_id}"
    
    img = qrcode.make(qr_content)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@bp.route('/tenant/payments')
def tenant_payments():
    if session.get('role') != 'TENANT': return redirect(url_for('main.login'))
    
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
            SELECT amount, payment_date, payment_month, status, payment_mode, remarks, created_at
            FROM payments 
            WHERE tenant_id = %s 
            ORDER BY payment_date DESC, created_at DESC
        """, (tenant_id,))
        
        payments = []
        for row in cur.fetchall():
            payments.append({
                'amount': row[0],
                'date': row[1],
                'month': row[2],
                'status': row[3],
                'mode': row[4],
                'remarks': row[5],
                'created_at': row[6]
            })
            
        return render_template('tenant/payments.html', payments=payments, session=session)
        
    except Exception as e:
        print(f"Error fetching payments: {e}")
        return redirect(url_for('main.tenant_dashboard'))
    finally:
        cur.close()
        conn.close()
