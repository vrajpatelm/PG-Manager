import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app
from datetime import datetime

def send_email(to_email, subject, html_content, text_content=None, attachments=None):
    """
    Generic function to send emails via SMTP using Flask config.
    """
    user = current_app.config.get('MAIL_USERNAME')
    pwd = current_app.config.get('MAIL_PASSWORD')
    server_host = current_app.config.get('MAIL_SERVER')
    server_port = current_app.config.get('MAIL_PORT')

    if not user or not pwd:
        print(f"\n{'='*50}")
        print(f"[MOCK EMAIL] To: {to_email}")
        print(f"Subject: {subject}")
        print(f"{'='*50}\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = f"PG Manager <{user}>"
        msg['To'] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        
        if html_content:
            msg.attach(MIMEText(html_content, "html"))

        if attachments:
            for filename, data, mimetype in attachments:
                part = MIMEApplication(data, Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)

        with smtplib.SMTP(server_host, int(server_port)) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False

def send_otp_email(to_email, otp):
    subject = "Your Verification Code - PG Manager"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#F8FAFC; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; margin-top: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            <div style="background-color: #1E293B; padding: 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px;">PG Manager</h1>
            </div>
            <div style="padding: 40px 32px; text-align: center;">
                <h2 style="color: #0F172A; font-size: 20px; font-weight: 600; margin: 0 0 16px;">Verify your email address</h2>
                <div style="background-color: #F1F5F9; border-radius: 12px; padding: 24px; margin: 20px auto; width: fit-content; border: 1px solid #E2E8F0;">
                    <span style="font-family: monospace; color: #0F172A; font-size: 32px; font-weight: 700; letter-spacing: 8px; display: block;">{otp}</span>
                </div>
                <p style="color: #94A3B8; font-size: 14px; margin-top: 32px;">Expires in 10 minutes.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, f"Your OTP is: {otp}")

def send_reset_email(to_email, link):
    subject = "Reset Your Password - PG Manager"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#F8FAFC; font-family: sans-serif;">
        <div style="max-width: 600px; margin: 40px auto; background: #fff; padding: 40px; border-radius: 16px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h2 style="color: #1E293B;">Reset Password</h2>
            <p style="color: #64748B;">Click below to reset your password. Valid for 30 mins.</p>
            <a href="{link}" style="background: #2563EB; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; margin-top: 20px;">Reset Password</a>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, f"Reset Link: {link}")

def send_contact_admin_email(name, email, subject, message):
    admin_email = current_app.config.get('MAIL_USERNAME')
    body = f"""
    New Contact Inquiry
    -------------------
    Name: {name}
    Email: {email}
    Subject: {subject}
    
    Message:
    {message}
    """
    return send_email(admin_email, f"📩 Inquiry: {subject}", None, body)

def send_subscription_welcome_email(to_email):
    subject = "🌟 You're In! Welcome to the Future of Living"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#f3f4f6; font-family: sans-serif;">
        <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); overflow: hidden;">
            <div style="background: #1e293b; padding: 30px; text-align: center; color: white;">
                <h2>Welcome to PG Manager</h2>
            </div>
            <div style="padding: 40px;">
                <p>Hi there,</p>
                <p>Thanks for subscribing! You'll now receive exclusive updates and insights.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, "Welcome to PG Manager!")
