import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

from datetime import datetime
from flask import current_app

def inject_today():
    """Injection de la date du jour dans tous les templates"""
    return {
        'today': datetime.now().date(),  # <-- C'est une variable, pas un filtre
        'current_year': datetime.now().year,
        'app_name': current_app.config.get('APP_NAME', 'Invento'),
        'app_version': current_app.config.get('APP_VERSION', '1.0.0')
    }

def create_app(config_name='default'):
    """Factory function pour créer l'application Flask"""
    
    # Chemin absolu du répertoire racine du projet (là où se trouvent templates et static)
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, 'templates'),
        static_folder=os.path.join(basedir, 'static')
    )
    
    # Configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # FORCER le rechargement des templates
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.jinja_env.cache = None
    
    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configuration de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    # Création des dossiers nécessaires
    create_folders(app)
    
    # Enregistrement des blueprints
    register_blueprints(app)
    
    # Configuration des filtres de template
    register_template_filters(app)
    
    # Configuration des context processors
    register_context_processors(app)
    
    # Configuration des error handlers
    register_error_handlers(app)
    
    return app

def create_folders(app):
    """Crée les dossiers nécessaires s'ils n'existent pas"""
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)

def register_blueprints(app):
    """Enregistre tous les blueprints"""
    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    from app.stock import bp as stock_bp
    from app.personnel import bp as personnel_bp
    from app.projects import bp as projects_bp
    from app.groups import bp as groups_bp
    from app.dashboard import bp as dashboard_bp
    from app.calendar import bp as calendar_bp
    from app.main import bp as main_bp
    from app.clients import bp as clients_bp
    from app.interventions import bp as interventions_bp
    from app.equipments import bp as equipments_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(personnel_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(interventions_bp)
    app.register_blueprint(equipments_bp)

def register_template_filters(app):
    """Enregistre les filtres de template personnalisés"""
    try:
        from app.utils import (
            format_date, 
            format_datetime, 
            format_currency, 
            nl2br
        )
        
        # Enregistrer uniquement les filtres personnalisés essentiels
        app.jinja_env.filters['format_date'] = format_date
        app.jinja_env.filters['format_datetime'] = format_datetime
        app.jinja_env.filters['format_currency'] = format_currency
        app.jinja_env.filters['nl2br'] = nl2br
        
        # Ne PAS écraser les filtres built-in de Jinja2 (selectattr, sum)
        
    except Exception as e:
        import traceback
        print(f"ERREUR lors de l'enregistrement des filtres: {e}")
        traceback.print_exc()
        raise

def register_context_processors(app):
    """Enregistre les context processors"""
    app.context_processor(inject_today)
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_globals():
        """Injecte des variables globales dans tous les templates"""
        from flask_login import current_user
        from datetime import datetime
        from app.models import Notification, StockItem
        
        data = {
            'current_year': datetime.now().year,
            'app_name': 'Invento',
            'app_version': '1.0.0'
        }
        
        if current_user.is_authenticated:
            data['current_user'] = current_user
            
            # Compter les notifications non lues
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False
            ).count()
            data['unread_notifications'] = unread_count
            
            # Compter les alertes de stock
            stock_alerts = StockItem.query.filter(
                StockItem.quantity <= StockItem.min_quantity,
                StockItem.min_quantity > 0
            ).count()
            data['stock_alerts_count'] = stock_alerts
            
            # Déterminer les permissions
            # Créer un objet simple pour les permissions
            class Permissions:
                def __init__(self, user):
                    self.user = user
                
                def __getattr__(self, module):
                    # Retourne un objet qui peut être utilisé comme current_permissions.stock.read
                    return PermissionModule(self.user, module)
            
            class PermissionModule:
                def __init__(self, user, module):
                    self.user = user
                    self.module = module
                
                def __getattr__(self, action):
                    # Vérifie si l'utilisateur a la permission
                    if hasattr(self.user, 'has_permission'):
                        return self.user.has_permission(self.module, action)
                    # Si pas de méthode has_permission, donner tous les droits à l'admin
                    if hasattr(self.user, 'role') and self.user.role and self.user.role.name == 'admin':
                        return True
                    return False
            
            data['current_permissions'] = Permissions(current_user)
        else:
            # Pour les utilisateurs non connectés
            data['current_user'] = None
            data['unread_notifications'] = 0
            data['stock_alerts_count'] = 0
            
            # Créer un objet permissions qui retourne False pour tout
            class NoPermissions:
                def __getattr__(self, module):
                    return NoPermissionModule()
            
            class NoPermissionModule:
                def __getattr__(self, action):
                    return False
            
            data['current_permissions'] = NoPermissions()
        
        return data

def register_error_handlers(app):
    """Enregistre les error handlers"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
