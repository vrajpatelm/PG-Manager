from flask import render_template, request, redirect, url_for, session, flash
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.utils.activity import log_activity
from app.blueprints import bp

@bp.route('/owner/notices')
@role_required('OWNER')
def owner_notices():
    conn = get_db_connection()
    cur = conn.cursor()
    notices = []
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        row = cur.fetchone()
        if not row:
            return render_template('owner/notices.html', notices=[])
        
        owner_id = row[0]
        
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
            
    except Exception as e:
        print(f"Error fetching notices: {e}")
        notices = []
    finally:
        cur.close()
        conn.close()
        
    return render_template('owner/notices.html', notices=notices)

@bp.route('/owner/notices/add', methods=['POST'])
@role_required('OWNER')
def add_notice():
    title = request.form.get('title')
    description = request.form.get('description')
    priority = request.form.get('priority')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        row = cur.fetchone()
        if not row:
            flash("Owner profile not found", "error")
            return redirect(url_for('main.owner_notices'))
            
        owner_id = row[0]
        
        cur.execute("""
            INSERT INTO notices (owner_id, title, description, priority)
            VALUES (%s, %s, %s, %s)
        """, (owner_id, title, description, priority))
        
        conn.commit()
        
        # Log Activity
        log_activity(owner_id, 'NOTICE', f"Posted notice: {title}", {'priority': priority})
        
        flash("Notice posted successfully!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error posting notice: {e}")
        flash("Failed to post notice", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_notices'))

@bp.route('/owner/notices/delete/<notice_id>', methods=['POST'])
@role_required('OWNER')
def delete_notice(notice_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if the notice belongs to the owner
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        cur.execute("DELETE FROM notices WHERE id = %s AND owner_id = %s", (notice_id, owner_id))
        
        if cur.rowcount > 0:
            conn.commit()
            flash("Notice deleted successfully!", "success")
        else:
            flash("Notice not found or permission denied.", "error")
    except Exception as e:
        conn.rollback()
        print(f"Error deleting notice: {e}")
        flash("Failed to delete notice", "error")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('main.owner_notices'))
