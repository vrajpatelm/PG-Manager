import os
from psycopg2 import OperationalError
import psycopg2
from dotenv import load_dotenv
from flask import Blueprint, jsonify, redirect, render_template, request, url_for

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO: implement authentication
        # email = request.form.get('email')
        # password = request.form.get('password')
        return redirect(url_for('main.index'))
    return render_template('login.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # TODO: implement user creation and validation
        # name = request.form.get('name')
        # email = request.form.get('email')
        # password = request.form.get('password')
       
        return redirect(url_for('main.index'))
    return render_template('signup.html')


@bp.route('/owner/dashboard')
def owner_dashboard():
    return render_template('owner/dashboard.html')


@bp.route('/owner/tenants')
def owner_tenants():
    return render_template('owner/tenants.html')

@bp.route('/owner/add-tenant')
def owner_add_tenant():
    return render_template('owner/add_tenant.html')


@bp.route('/owner/settings')
def owner_settings():
    return render_template('owner/settings.html')


@bp.route('/owner/export/tenants')
def export_tenants():
    # TODO: Implement actual CSV generation from database
    # For now, return a mock CSV
    csv_content = "Name,Email,Room,Status\nJohn Doe,john@example.com,101,Active\nJane Smith,jane@example.com,202,Paid"
    
    from flask import Response
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=tenants.csv"}
    )


@bp.route('/owner/tenants/<int:tenant_id>')
def owner_tenant_details(tenant_id):
    return render_template('owner/tenant_details.html', tenant_id=tenant_id)

DB_CONFIG = {
    "dbname":os.getenv("DB_NAME"),
            "user":os.getenv("DB_USER"),
            "password":os.getenv("DB_PASSWORD"),
            "host":os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", "5432")),
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except OperationalError as e:
         print("DB connection error:", e)
         return None


@bp.route("/admin", methods=["GET"])
def get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": f"DB connection failed"}), 500

    cur = conn.cursor()
    cur.execute("SELECT t_id, t_name, t_email , t_password FROM tenants;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "name": r[1], "email": r[2] , "password": r[3]}
        for r in rows
    ])


@bp.route("/admin", methods=["POST"])
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tenants (t_name, t_email) VALUES (%s, %s) RETURNING t_id;",
        (data["name"], data["email"])
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": new_id}), 201