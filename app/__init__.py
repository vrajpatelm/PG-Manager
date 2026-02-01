from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Application factory"""
    app = Flask(__name__)
    import os
    app.secret_key = os.environ.get('SECRET_KEY') or 'dev_secret_key_change_in_production'

    # Register blueprints
    from .blueprints import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Mail Config (Optimistic Gmail or Console)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    # Initialize extensions if needed (using a simple helper for now or actual Flask-Mail)
    # For now, we will use a helper function in auth.py to send emails, 
    # but we can store the config here.

    @app.template_filter('time_ago')
    def time_ago(dt):
        from datetime import datetime, date
        if not dt:
            return ""
        
        # Handle string dates
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except:
                return dt 

        # Handle date objects (convert to datetime at midnight)
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time())

        # Fix: datetime.now() is naive, so if dt is aware, strip timezone
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)

        now = datetime.now()
        
        # Simple naive check. If timezone issues arise, we can improve.
        if dt > now:
            return "Just now"

        diff = now - dt
        seconds = diff.total_seconds()

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} min{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hr{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime('%Y-%m-%d')

    return app
