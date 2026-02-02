from flask import render_template, request, redirect, url_for, session, flash
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.blueprints import bp

@bp.route('/owner/properties')
@role_required('OWNER')
def owner_properties():
    
    conn = get_db_connection()
    if not conn:
        flash("Database Error", "error")
        return render_template('owner/properties.html', properties=[])
        
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        cur.execute("SELECT id, name, address FROM properties WHERE owner_id = %s", (owner_id,))
        prop_rows = cur.fetchall()
        
        properties = []
        for prop_row in prop_rows:
            prop_id = prop_row[0]
            
            cur.execute("""
                SELECT id, room_number, floor_number, capacity, rent_amount 
                FROM rooms WHERE property_id = %s ORDER BY room_number
            """, (prop_id,))
            room_rows = cur.fetchall()
            
            rooms = []
            for room in room_rows:
                r_id = room[0]
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
@role_required('OWNER')
def add_room():
    
    room_number = request.form.get('room_number')
    floor = request.form.get('floor')
    capacity = request.form.get('capacity')
    rent = request.form.get('rent_amount')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM properties WHERE owner_id = %s", (owner_id,))
        prop_row = cur.fetchone()
        if not prop_row:
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
@role_required('OWNER')
def edit_room():
    
    room_id = request.form.get('room_id')
    room_number = request.form.get('room_number')
    floor = request.form.get('floor')
    capacity = request.form.get('capacity')
    rent = request.form.get('rent_amount')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
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
