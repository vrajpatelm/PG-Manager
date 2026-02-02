import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from datetime import datetime

def send_email(to_email, subject, template, attachments=None, **kwargs):
    """
    Sends a professional HTML email using a template
    attachments: list of dicts {'name': 'filename', 'mime': 'application/pdf', 'data': bytes}
    """
    user = current_app.config.get('MAIL_USERNAME')
    pwd = current_app.config.get('MAIL_PASSWORD')
    
    # Render HTML content
    try:
        html_content = render_template(template, current_year=datetime.now().year, **kwargs)
    except Exception as e:
        current_app.logger.error(f"Error rendering template {template}", exc_info=e)
        return False

    # Mock Mode if no credentials
    if not user or not pwd:
        current_app.logger.info(f"MOCK EMAIL to {to_email}", extra={'subject': subject, 'context': kwargs})
        return True

    try:
        msg = MIMEMultipart("mixed") if attachments else MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = f"PG Manager <{user}>"
        msg['To'] = to_email

        # Create message body
        body_part = MIMEMultipart("alternative")
        text_content = f"Subject: {subject}\n\nPlease view this email in an HTML compatible mail client."
        body_part.attach(MIMEText(text_content, "plain"))
        body_part.attach(MIMEText(html_content, "html"))
        
        msg.attach(body_part)
        
        if attachments:
            for attachment in attachments:
                part = MIMEApplication(attachment['data'], Name=attachment['name'])
                part['Content-Disposition'] = f'attachment; filename="{attachment["name"]}"'
                msg.attach(part)

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        
        current_app.logger.info(f"Email sent to {to_email}", extra={'subject': subject})
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email to {to_email}", exc_info=e)
        return False
