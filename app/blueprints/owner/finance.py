from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash
from app.database.database import get_db_connection
from app.utils.decorators import role_required
from app.blueprints import bp

@bp.route('/owner/finance')
@role_required('OWNER')
def owner_finance():
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    current_date = datetime.now()
    current_month_str = current_date.strftime('%Y-%m')
    current_month_name = current_date.strftime('%B %Y')
    
    try:
        cur.execute("SELECT id FROM owners WHERE user_id = %s", (session.get('user_id'),))
        owner_id = cur.fetchone()[0]
        
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

@bp.route('/owner/add-expense', methods=['POST'])
@role_required('OWNER')
def owner_add_expense():
    
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
