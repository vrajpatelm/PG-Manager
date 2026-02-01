from flask import render_template, session, redirect, url_for, request, flash, current_app
from . import bp
import os
from werkzeug.utils import secure_filename
from app.database.database import get_db_connection

@bp.route("/")
def index():
    if 'user_id' in session:
        if session.get('role') == 'OWNER':
            return redirect(url_for('main.owner_dashboard'))
        elif session.get('role') == 'TENANT':
             return redirect(url_for('main.tenant_dashboard'))
            
    return render_template("index.html")

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/careers')
def careers():
    return render_template('careers.html')

@bp.route('/careers/apply', methods=['POST'])
def apply_for_job():
    if request.method == 'POST':
        # 1. Capture Form Data
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        cover_letter = request.form.get('cover_letter', '')
        
        linkedin_url = request.form.get('linkedin_url', '')
        portfolio_url = request.form.get('portfolio_url', '')
        experience_years = request.form.get('experience_years', '')
        current_ctc = request.form.get('current_ctc', '')
        expected_ctc = request.form.get('expected_ctc', '')
        notice_period = request.form.get('notice_period', '')

        # 2. Handle File Upload
        resume_data = None
        resume_filename = None
        resume_mimetype = None
        
        if 'resume' in request.files:
            file = request.files['resume']
            if file.filename != '':
                resume_filename = secure_filename(file.filename)
                resume_mimetype = file.mimetype
                resume_data = file.read() # Read binary data
                
        # 3. Save to Database
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO job_applications 
                (full_name, email, phone, role_applied, resume_filename, resume_data, resume_mimetype, cover_letter,
                 linkedin_url, portfolio_url, experience_years, current_ctc, expected_ctc, notice_period)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, role, resume_filename, resume_data, resume_mimetype, cover_letter,
                  linkedin_url, portfolio_url, experience_years, current_ctc, expected_ctc, notice_period))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")
            flash('Error saving application. Please try again.', 'error')
            return redirect(url_for('main.careers'))

        # 4. Send Email via SMTP
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication

        smtp_server = os.environ.get('MAIL_SERVER')
        smtp_port = os.environ.get('MAIL_PORT')
        smtp_user = os.environ.get('MAIL_USERNAME')
        smtp_password = os.environ.get('MAIL_PASSWORD')

        if smtp_server and smtp_user and smtp_password:
            try:
                # --- A. Email to Admin ---
                msg_admin = MIMEMultipart()
                msg_admin['From'] = smtp_user
                msg_admin['To'] = smtp_user
                msg_admin['Subject'] = f"🚀 New Application: {role} - {full_name}"
                
                # Admin HTML Template
                html_admin = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #4F46E5; padding: 20px; text-align: center; color: white;">
                        <h2 style="margin: 0;">New Job Application</h2>
                    </div>
                    <div style="padding: 20px; background-color: #f9fafb;">
                        <p style="font-size: 16px; color: #374151;"><strong>{full_name}</strong> has applied for <strong>{role}</strong>.</p>
                        
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px; font-weight: bold; color: #6b7280;">Email</td><td style="padding: 12px;">{email}</td></tr>
                            <tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px; font-weight: bold; color: #6b7280;">Phone</td><td style="padding: 12px;">{phone}</td></tr>
                            <tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px; font-weight: bold; color: #6b7280;">Experience</td><td style="padding: 12px;">{experience_years}</td></tr>
                            <tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px; font-weight: bold; color: #6b7280;">Current / Expected CTC</td><td style="padding: 12px;">{current_ctc} / {expected_ctc}</td></tr>
                            <tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px; font-weight: bold; color: #6b7280;">Notice Period</td><td style="padding: 12px;">{notice_period}</td></tr>
                            <tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px; font-weight: bold; color: #6b7280;">LinkedIn</td><td style="padding: 12px;"><a href="{linkedin_url}">{linkedin_url}</a></td></tr>
                            <tr><td style="padding: 12px; font-weight: bold; color: #6b7280;">Portfolio</td><td style="padding: 12px;"><a href="{portfolio_url}">{portfolio_url}</a></td></tr>
                        </table>

                        <p style="margin-top: 20px; font-size: 14px; color: #6b7280;">The resume is attached to this email.</p>
                    </div>
                </div>
                """
                msg_admin.attach(MIMEText(html_admin, 'html'))

                # Attach Resume
                if resume_data:
                    part = MIMEApplication(resume_data, Name=resume_filename)
                    part['Content-Disposition'] = f'attachment; filename="{resume_filename}"'
                    msg_admin.attach(part)

                server = smtplib.SMTP(smtp_server, int(smtp_port) if smtp_port else 587)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg_admin)

                # --- B. Email to Applicant ---
                msg_user = MIMEMultipart()
                msg_user['From'] = smtp_user
                msg_user['To'] = email
                msg_user['Subject'] = f"Application Received - {role} at PG-Manager"
                
                # Applicant HTML Template
                html_user = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
                    <!-- Header -->
                    <div style="background-color: #ffffff; padding: 30px 20px; text-align: center; border-bottom: 3px solid #4F46E5;">
                        <h1 style="color: #111827; margin: 0; font-size: 24px;">PG-Manager</h1>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 40px 30px; background-color: #f9fafb;">
                        <h2 style="color: #1F2937; margin-top: 0; font-size: 20px;">Hi {full_name},</h2>
                        <p style="color: #4B5563; line-height: 1.6; font-size: 16px;">
                            Thanks for applying for the <strong>{role}</strong> position. We've received your application and are excited to review it!
                        </p>
                        
                        <div style="background-color: #EEF2FF; border-left: 4px solid #4F46E5; padding: 15px; margin: 25px 0; border-radius: 0 4px 4px 0;">
                            <p style="margin: 0; color: #4338CA; font-weight: 500;">
                                "We believe co-living is the future, and we're glad you want to build it with us."
                            </p>
                        </div>
                        
                        <p style="color: #4B5563; line-height: 1.6;">
                            Our team is currently reviewing your profile. If your skills match our requirements, we will reach out to schedule an interview within the next <strong>3-5 business days</strong>.
                        </p>
                    </div>

                    <!-- Footer -->
                    <div style="background-color: #1F2937; padding: 20px; text-align: center; color: #9CA3AF; font-size: 13px;">
                        <p style="margin: 0;">&copy; 2026 PG-Manager. All rights reserved.</p>
                        <p style="margin: 5px 0 0 0;">This is an automated message, please do not reply directly.</p>
                    </div>
                </div>
                """
                msg_user.attach(MIMEText(html_user, 'html'))
                
                server.send_message(msg_user)
                server.quit()
                print("HTML Emails sent successfully.")

            except Exception as e:
                print(f"SMTP Error: {e}")
        else:
            print("SMTP credentials not found.")

        flash('Application submitted! Check your email for confirmation.', 'success')
        return redirect(url_for('main.careers'))

    return redirect(url_for('main.careers'))
@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/contact/submit', methods=['POST'])
def contact_submit():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        # Send Email to Admin
        smtp_server = os.environ.get('MAIL_SERVER')
        smtp_port = os.environ.get('MAIL_PORT')
        smtp_user = os.environ.get('MAIL_USERNAME')
        smtp_password = os.environ.get('MAIL_PASSWORD')

        if smtp_server and smtp_user and smtp_password:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = smtp_user  # Admin receives it
                msg['Subject'] = f"📩 New Inquiry: {subject}"
                
                body = f"""
                New Contact Message
                -------------------
                Name: {name}
                Email: {email}
                Subject: {subject}
                
                Message:
                {message}
                """
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(smtp_server, int(smtp_port) if smtp_port else 587)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                server.quit()
                
            except Exception as e:
                print(f"Contact Email Error: {e}")
                flash('Something went wrong. Please try again.', 'error')
                return redirect(url_for('main.contact'))
        
        flash('Message sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
        
    return redirect(url_for('main.contact'))



@bp.route('/terms')
def terms():
    return render_template('terms.html')

@bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@bp.route('/team')
def team():
    return render_template('team.html')

@bp.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    
    if not email:
        flash('Please provide an email address.', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if already subscribed
        cur.execute('SELECT id FROM subscribers WHERE email = %s', (email,))
        if cur.fetchone():
            flash('You are already subscribed!', 'info')
        else:
            cur.execute('INSERT INTO subscribers (email) VALUES (%s)', (email,))
            conn.commit()
            
            # Send Welcome Email
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                smtp_server = os.environ.get('MAIL_SERVER')
                smtp_port = os.environ.get('MAIL_PORT')
                smtp_user = os.environ.get('MAIL_USERNAME')
                smtp_password = os.environ.get('MAIL_PASSWORD')
                
                if smtp_server and smtp_user and smtp_password:
                    msg = MIMEMultipart()
                    msg['From'] = f"PG-Manager <{smtp_user}>"
                    msg['To'] = email
                    msg['Subject'] = "🌟 You're In! Welcome to the Future of Living"
                    
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f3f4f6; }}
                            .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
                            .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 40px 20px; text-align: center; position: relative; }}
                            .header::after {{ content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #D61C4E, #FEB139); }}
                            .logo {{ font-size: 28px; font-weight: 800; color: #ffffff; text-decoration: none; letter-spacing: -1px; }}
                            .logo span {{ color: #D61C4E; }}
                            .content {{ padding: 40px 30px; color: #334155; line-height: 1.7; }}
                            .h1 {{ font-size: 26px; font-weight: 700; color: #1e293b; margin-bottom: 15px; }}
                            .intro {{ font-size: 16px; margin-bottom: 30px; color: #475569; }}
                            .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; margin-bottom: 25px; transition: transform 0.2s; }}
                            .card-title {{ font-weight: 600; color: #D61C4E; margin-bottom: 8px; font-size: 18px; display: flex; align-items: center; gap: 10px; }}
                            .footer {{ background: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 13px; color: #94a3b8; }}
                            .btn {{ display: inline-block; background: #D61C4E; color: #ffffff; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: 600; margin-top: 20px; box-shadow: 0 4px 6px rgba(214, 28, 78, 0.2); }}
                            .btn:hover {{ background: #be123c; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <div class="logo">PG-<span>Manager</span></div>
                            </div>
                            <div class="content">
                                <div class="h1">Welcome into the Inner Circle! 🚀</div>
                                <p class="intro">Hi there,</p>
                                <p class="intro">
                                    Thank you for subscribing to PG-Manager. You’ve just taken a step towards smarter living and effortless management. We are thrilled to have you with us!
                                </p>
                                
                                <div class="card">
                                    <div class="card-title">✨ Exclusive Updates</div>
                                    <p style="margin:0; font-size:15px;">Be the first to know about our latest features, smart tools for owners, and seamless experiences for tenants.</p>
                                </div>
                                
                                <div class="card">
                                    <div class="card-title">💡 Expert Insights</div>
                                    <p style="margin:0; font-size:15px;">Get curated tips on property management, co-living trends, and how to maximize your rental yield.</p>
                                </div>

                                <div class="card">
                                    <div class="card-title">🎁 Subscriber Perks</div>
                                    <p style="margin:0; font-size:15px;">Enjoy early access to premium tools and special offers reserved strictly for our community members.</p>
                                </div>
                                
                                <p style="margin-top: 30px;">
                                    We promise to keep our emails valuable, interesting, and fluff-free. Get ready for some amazing things landing in your inbox soon!
                                </p>
                                
                                <div style="text-align: center; margin-top: 40px;">
                                    <a href="{url_for('main.index', _external=True)}" class="btn">Explore Dashboard</a>
                                </div>
                            </div>
                            <div class="footer">
                                <p>&copy; 2026 PG-Manager. All rights reserved.</p>
                                <p>You received this email because you subscribed on our website. <br>
                                <a href="#" style="color: #64748b; text-decoration: underline;">Unsubscribe</a></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    msg.attach(MIMEText(html_content, 'html'))
                    
                    server = smtplib.SMTP(smtp_server, int(smtp_port) if smtp_port else 587)
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()
            except Exception as e:
                current_app.logger.error(f"Failed to send subscription email: {e}")
                # Don't fail the request, just log it. The user is subscribed.

            flash('Successfully subscribed to our newsletter!', 'success')
            
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Subscription error: {e}")
        flash('An error occurred. Please try again.', 'error')
    finally:
        cur.close()
        conn.close()
        
    return redirect(request.referrer or url_for('main.index'))

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
