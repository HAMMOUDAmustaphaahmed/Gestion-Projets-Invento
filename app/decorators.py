from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def permission_required(module, action):
    """
    Décorateur pour vérifier les permissions d'un utilisateur
    
    Args:
        module: Module de l'application (ex: 'stock', 'projects')
        action: Action spécifique (ex: 'create', 'read', 'update', 'delete')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(module, action):
                flash('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.', 'danger')
                return abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Décorateur pour les routes réservées aux administrateurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.role or current_user.role.name != 'admin':
            flash('Accès réservé aux administrateurs.', 'danger')
            return abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*role_names):
    """Décorateur pour vérifier si l'utilisateur a un des rôles spécifiés"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.role or current_user.role.name not in role_names:
                flash('Vous n\'avez pas le rôle nécessaire pour accéder à cette page.', 'danger')
                return abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator