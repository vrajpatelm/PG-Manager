from flask import render_template, session, redirect, url_for
from . import bp

@bp.route("/")
def index():
    if 'user_id' in session:
        if session.get('role') == 'OWNER':
            return redirect(url_for('main.owner_dashboard'))
        elif session.get('role') == 'TENANT':
             return redirect(url_for('main.tenant_dashboard'))
            
    return render_template("index.html")

@bp.app_template_filter('time_ago')
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
