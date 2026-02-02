import json
import io
import psycopg2
from flask import render_template, request, redirect, url_for, session, flash, send_file
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.blueprints import bp

@bp.route('/owner/settings')
@role_required('OWNER')
def owner_settings():
    
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
        qr_url = owner_row[10]
        if owner_row[11]:
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
        return render_template('owner/settings.html', owner={'preferences': {}}, property={})
    finally:
        cur.close()
        conn.close()

@bp.route('/owner/settings/update', methods=['POST'])
@role_required('OWNER')
def owner_settings_update():
    
    def clean(val):
        return val if val and val.strip() != "" else None

    def clean_int(val, default=0):
        try:
            if not val or val.strip() == "": return default
            return int(val)
        except ValueError:
            return default

    full_name = clean(request.form.get('full_name'))
    phone_number = clean(request.form.get('phone_number'))
    
    upi_id = clean(request.form.get('upi_id'))
    account_holder = clean(request.form.get('account_holder_name'))
    bank_name = clean(request.form.get('bank_name'))
    account_number = clean(request.form.get('account_number'))
    ifsc_code = clean(request.form.get('ifsc_code'))
    
    late_fee = clean_int(request.form.get('late_fee_daily'), 0)
    grace_period = clean_int(request.form.get('rent_grace_period_days'), 5)
    
    wifi_ssid = clean(request.form.get('wifi_ssid'))
    wifi_password = clean(request.form.get('wifi_password'))
    
    gate_closing = clean(request.form.get('gate_closing_time'))
    breakfast_start = clean(request.form.get('breakfast_start_time'))
    breakfast_end = clean(request.form.get('breakfast_end_time'))
    
    house_rules = clean(request.form.get('house_rules'))
    
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
        
        qr_binary = None
        if 'qr_code' in request.files:
            file = request.files['qr_code']
            if file and file.filename != '':
                qr_binary = file.read() 
                
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

@bp.route('/owner/qr-image/<owner_id>')
def owner_qr_image(owner_id):
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
