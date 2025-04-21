from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Decorator to restrict access to admin users only.
    
    This decorator checks if the current user is both authenticated
    and has the admin role. If not, it returns a 403 Forbidden response.
    
    Args:
        f: The view function to decorate
    
    Returns:
        decorated_function: The decorated view function
        
    Raises:
        403: If user is not authenticated or not an admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            abort(403)  # Forbidden
            
        return f(*args, **kwargs)
    return decorated_function


def editor_required(f):
    """Decorator to restrict access to editor and admin users.
    
    This decorator checks if the current user is authenticated
    and has either editor or admin role. If not, it returns
    a 403 Forbidden response.
    
    Args:
        f: The view function to decorate
    
    Returns:
        decorated_function: The decorated view function
        
    Raises:
        403: If user is not authenticated or not an editor/admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_editor():
            abort(403)  # Forbidden
            
        return f(*args, **kwargs)
    return decorated_function