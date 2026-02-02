from datetime import datetime, timedelta
from flask import render_template, session, flash
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.blueprints import bp

@bp.route('/owner/dashboard')
@role_required('OWNER')
def owner_dashboard():
    
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
        
        cur.execute("SELECT SUM(monthly_rent) FROM tenants WHERE owner_id = %s AND onboarding_status = 'ACTIVE'", (owner_id,))
        total_income = cur.fetchone()[0] or 0
        
        cur.execute("""
            SELECT SUM(amount) FROM expenses 
            WHERE owner_id = %s AND expense_month = %s
        """, (owner_id, datetime.now().strftime('%Y-%m')))
        total_spent = cur.fetchone()[0] or 0
        
        net_profit = total_income - total_spent
        
        cur.execute("""
            SELECT SUM(capacity) 
            FROM rooms 
            WHERE property_id IN (SELECT id FROM properties WHERE owner_id = %s)
        """, (owner_id,))
        capacity_row = cur.fetchone()
        total_capacity = capacity_row[0] or 0
        
        cur.execute("SELECT COUNT(*) FROM tenants WHERE owner_id = %s AND onboarding_status IN ('ACTIVE', 'PENDING', 'NOTICE')", (owner_id,))
        total_tenants = cur.fetchone()[0] or 0
        
        if total_capacity > 0:
            occupancy_rate = int((total_tenants / total_capacity) * 100)
        else:
            occupancy_rate = 0
            
        available_beds = max(0, total_capacity - total_tenants)
        occupancy_rotation = int((occupancy_rate / 100) * 360)
        occupancy_rotation_style = f"transform: rotate({occupancy_rotation}deg);"
        
        current_month = datetime.now().strftime('%Y-%m')
        
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(monthly_rent), 0) 
            FROM tenants 
            WHERE owner_id = %s AND onboarding_status = 'ACTIVE'
        """, (owner_id,))
        stats_row = cur.fetchone()
        
        total_active_tenants = stats_row[0] or 0
        total_expected_rent = stats_row[1] or 0
        
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
        
        if total_expected_rent > 0:
            collection_percentage = int((total_collected / total_expected_rent) * 100)
        else:
            collection_percentage = 0
            
        rent_collection_style = f"width: {collection_percentage}%;"

        cur.execute("""
            SELECT p.id, t.full_name, p.amount, p.payment_date, p.remarks, t.room_number 
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.id
            WHERE t.owner_id = %s AND p.status = 'PENDING'
            ORDER BY p.created_at DESC
            LIMIT 3
        """, (owner_id,))
        pending_approvals = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) FROM payments p JOIN tenants t ON p.tenant_id = t.id WHERE t.owner_id = %s AND p.status = 'PENDING'", (owner_id,))
        total_pending_count = cur.fetchone()[0] or 0

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
        
        cur.execute("""
            SELECT full_name, room_number, created_at
            FROM tenants
            WHERE owner_id = %s 
            ORDER BY created_at DESC
            LIMIT 3
        """, (owner_id,))
        recent_movements = cur.fetchall()
        
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
        
        cur.execute("""
            SELECT COUNT(*) FROM complaints 
            WHERE owner_id = %s AND status = 'PENDING' AND priority = 'HIGH'
        """, (owner_id,))
        high_priority_count = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT id, title, description, priority, created_at 
            FROM notices 
            WHERE owner_id = %s 
            ORDER BY created_at DESC 
            LIMIT 3
        """, (owner_id,))
        recent_notices = []
        for row in cur.fetchall():
            recent_notices.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'priority': row[3],
                'created_at': row[4]
            })

        cur.execute("""
            SELECT event_type, description, created_at, metadata 
            FROM activity_logs 
            WHERE owner_id = %s 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (owner_id,))
        recent_activity = []
        for row in cur.fetchall():
            recent_activity.append({
                'type': row[0],
                'description': row[1],
                'created_at': row[2],
                'metadata': row[3] if row[3] else {}
            })
        
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
                             recent_notices=recent_notices,
                             recent_activity=recent_activity)
                             
    except Exception as e:
        print(f"Dashboard Error: {e}")
        flash(f"DASHBOARD CRASH: {str(e)}", "error")
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
                             recent_notices=[],
                             recent_activity=[])
    finally:
        cur.close()
        conn.close()
