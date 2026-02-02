from datetime import datetime
from flask import redirect, url_for, flash, current_app, request, session
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.utils.mailer import send_email
from app.utils.activity import log_activity
from app.utils.pdf import generate_receipt
from app.blueprints import bp

@bp.route('/owner/payment/approve/<payment_id>', methods=['POST'])
@role_required('OWNER')
def approve_payment(payment_id):
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE payments SET status = 'COMPLETED' WHERE id = %s", (payment_id,))
        
        # Log Activity
        cur.execute("""
            SELECT p.amount, t.full_name, t.owner_id, t.email, t.room_number, p.payment_month, p.payment_mode, p.payment_date, o.full_name
            FROM payments p 
            JOIN tenants t ON p.tenant_id = t.id 
            JOIN owners o ON t.owner_id = o.id
            WHERE p.id = %s
        """, (payment_id,))
        pay_row = cur.fetchone()
        
        if pay_row:
             # Unpack Details
             amount, tenant_name, owner_id, tenant_email, room_no, month, mode, pay_date, owner_name = pay_row
             
             # 1. Log Activity
             log_activity(owner_id, 'PAYMENT', f"Verified payment of ₹{amount} from {tenant_name}", {'payment_id': payment_id})
             
             # 2. Generate Receipt
             receipt_data = {
                 'transaction_id': str(payment_id),
                 'date': pay_date,
                 'tenant_name': tenant_name,
                 'tenant_room': room_no,
                 'amount': amount,
                 'month': month,
                 'payment_mode': mode,
                 'owner_name': owner_name
             }
             pdf_buffer = generate_receipt(receipt_data)
             pdf_bytes = pdf_buffer.getvalue()
             
             # 3. Send Email to Tenant (with Attachment)
             send_email(
                 to_email=tenant_email,
                 subject=f"Rent Receipt: {month}",
                 template="emails/rent_receipt.html",
                 attachments=[{'name': f"Receipt_{month}.pdf", 'data': pdf_bytes, 'mime': 'application/pdf'}],
                 tenant_name=tenant_name,
                 month=month,
                 amount=amount
             )
             
             send_email(
                 to_email=session.get('email', 'dhruvharani8@gmail.com'), # Fallback if session missing
                 subject=f"💰 Payment Verified: ₹{amount}",
                 template="emails/payment_notification.html",
                 owner_name=owner_name,
                 tenant_name=tenant_name,
                 room_number=room_no,
                 month=month,
                 amount=amount,
                 mode=mode
             )
             
             # Audit Log
             current_app.logger.info(
                 f"Payment {payment_id} Verified by Owner {owner_id}", 
                 extra={'event': 'PAYMENT_VERIFIED', 'amount': amount, 'tenant': tenant_name, 'owner_id': owner_id}
             )

        conn.commit()
        flash("Payment verified successfully!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error verifying payment: {e}")
        flash("Error verifying payment.", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('main.owner_dashboard'))

@bp.route('/owner/payment/reject/<payment_id>', methods=['POST'])
@role_required('OWNER')
def reject_payment(payment_id):
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE payments SET status = 'FAILED' WHERE id = %s", (payment_id,))
        
        # Log Activity
        cur.execute("SELECT p.amount, t.full_name, t.owner_id FROM payments p JOIN tenants t ON p.tenant_id = t.id WHERE p.id = %s", (payment_id,))
        pay_row = cur.fetchone()
        if pay_row:
             log_activity(pay_row[2], 'PAYMENT', f"Rejected payment of ₹{pay_row[0]} from {pay_row[1]}", {'payment_id': payment_id})
             
        conn.commit()
        flash("Payment rejected.", "info")
    except Exception as e:
        conn.rollback()
        flash("Error rejecting payment.", "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('main.owner_dashboard'))

@bp.route('/owner/record-payment', methods=['POST'])
@role_required('OWNER')
def owner_record_payment():
    
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
