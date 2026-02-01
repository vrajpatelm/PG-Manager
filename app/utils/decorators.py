from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """
    Decorator to ensure user is logged in.
    Redirects to login page if session is missing user_id.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            # Store the page they wanted to go to (next parameter)? 
            # For now, just simple redirect.
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Decorator to ensure user has specific role (OWNER or TENANT).
    Must be placed AFTER @login_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role_name:
                flash(f'Access denied. You must be signed in as a {role_name.title()}.', 'error')
                # Redirect to their appropriate dashboard instead of just failing?
                if session.get('role') == 'OWNER':
                    return redirect(url_for('main.owner_dashboard'))
                elif session.get('role') == 'TENANT':
                    return redirect(url_for('main.tenant_dashboard'))
                else:
                    return redirect(url_for('main.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def prevent_authenticated(f):
    """
    Decorator for public pages (Login/Signup).
    If user is already logged in, redirect them to their dashboard.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            if session.get('role') == 'OWNER':
                return redirect(url_for('main.owner_dashboard'))
            elif session.get('role') == 'TENANT':
                 return redirect(url_for('main.tenant_dashboard'))
        return f(*args, **kwargs)
    return decorated_function
