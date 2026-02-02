from flask import render_template, request, redirect, url_for, session, flash
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.blueprints import bp

@bp.route('/owner/complaints')
@role_required('OWNER')
def owner_complaints():
    
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
@role_required('OWNER')
def resolve_complaint(complaint_id):
    
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
