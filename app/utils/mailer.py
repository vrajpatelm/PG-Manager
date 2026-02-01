import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from datetime import datetime

def send_email(to_email, subject, template, **kwargs):
    """Sends a professional HTML email using a template"""
    user = current_app.config.get('MAIL_USERNAME')
    pwd = current_app.config.get('MAIL_PASSWORD')
    
    # Render HTML content
    try:
        html_content = render_template(template, current_year=datetime.now().year, **kwargs)
    except Exception as e:
        print(f"Error rendering template {template}: {e}")
        return False

    # Mock Mode if no credentials
    if not user or not pwd:
        print(f"\n{'='*50}")
        print(f"[MOCK EMAIL] To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Template: {template}")
        print(f"Context: {kwargs}")
        print(f"{'='*50}\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = f"PG Manager <{user}>"
        msg['To'] = to_email

        # Create plain text version (simplified)
        text_content = f"Subject: {subject}\n\nPlease view this email in an HTML compatible mail client."
        
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
