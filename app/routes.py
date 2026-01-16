from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_required
from app import db, csrf
from app.models import Notification, StockItem, Project, Task, Personnel
from datetime import datetime
from app.decorators import admin_required, permission_required
import json
import platform
# On essaie d'importer psutil, mais on continue même s'il n'est pas installé
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Créer le blueprint principal
from flask import Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Page d'accueil"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirection vers le tableau de bord"""
    return redirect(url_for('dashboard.index'))

@main_bp.route('/profile')
@login_required
def profile():
    """Profil de l'utilisateur connecté"""
    return redirect(url_for('auth.profile'))

@main_bp.route('/notifications')
@login_required
def notifications():
    """Notifications de l'utilisateur"""
    return redirect(url_for('admin.notifications'))

@main_bp.route('/search')
@login_required
def search():
    """Recherche globale"""
    query = request.args.get('q', '')
    
    if not query or len(query.strip()) < 2:
        flash('Veuillez entrer au moins 2 caractères pour la recherche.', 'warning')
        return redirect(request.referrer or url_for('dashboard.index'))
    
    # Nettoyer la requête
    query = query.strip()
    
    # Initialiser les résultats
    results = {
        'stock': [],
        'projects': [],
        'tasks': [],
        'personnel': []
    }
    
    # Recherche dans le stock
    stock_results = StockItem.query.filter(
        db.or_(
            StockItem.reference.ilike(f'%{query}%'),
            StockItem.libelle.ilike(f'%{query}%')
        )
    ).limit(10).all()
    results['stock'] = stock_results
    
    # Recherche dans les projets
    project_results = Project.query.filter(
        db.or_(
            Project.name.ilike(f'%{query}%'),
            Project.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    results['projects'] = project_results
    
    # Recherche dans les tâches
    task_results = Task.query.filter(
        db.or_(
            Task.name.ilike(f'%{query}%'),
            Task.description.ilike(f'%{query}%')
        )
    ).limit(10).all()
    results['tasks'] = task_results
    
    # Recherche dans le personnel
    personnel_results = Personnel.query.filter(
        db.or_(
            Personnel.first_name.ilike(f'%{query}%'),
            Personnel.last_name.ilike(f'%{query}%'),
            Personnel.employee_id.ilike(f'%{query}%')
        )
    ).limit(10).all()
    results['personnel'] = personnel_results
    
    # Compter le total des résultats
    total_results = sum(len(v) for v in results.values())
    
    return render_template('search.html',
                         title='Résultats de recherche',
                         query=query,
                         results=results,
                         total_results=total_results)

@main_bp.route('/help')
@login_required
def help():
    """Page d'aide"""
    return render_template('help.html', title='Aide')

@main_bp.route('/about')
def about():
    """Page À propos"""
    return render_template('about.html', title='À propos')

@main_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Paramètres de l'application (admin seulement)"""
    return render_template('settings.html', title='Paramètres')

@main_bp.before_app_request
def before_request():
    """Exécuté avant chaque requête"""
    if current_user.is_authenticated:
        # Mettre à jour la dernière activité
        current_user.last_seen = datetime.utcnow()
        
        try:
            db.session.commit()
        except:
            db.session.rollback()

@main_bp.context_processor
def inject_global_vars():
    """Injecter des variables globales dans tous les templates"""
    data = {
        'current_year': datetime.now().year,
        'app_name': 'Invento',
        'app_version': '1.0.0',
        'current_path': request.path
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
    
    return data

# Gestion des erreurs
@main_bp.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@main_bp.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@main_bp.route('/api/health')
def health_check():
    """Endpoint de santé pour monitoring"""
    try:
        # Vérifier la connexion à la base de données
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500

@main_bp.route('/api/system-info')
@login_required
@admin_required
def system_info():
    """Informations système (admin seulement)"""
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'environment': 'development' if current_app.debug else 'production',
        'debug': current_app.debug,
    }
    
    # Ajouter les informations psutil si disponible
    if PSUTIL_AVAILABLE:
        info.update({
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': int(psutil.boot_time())
        })
    else:
        info.update({
            'cpu_usage': 'N/A (psutil non installé)',
            'memory_usage': 'N/A (psutil non installé)',
            'disk_usage': 'N/A (psutil non installé)',
            'uptime': 'N/A (psutil non installé)'
        })
    
    return jsonify(info)

@csrf.exempt
@main_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload de fichiers générique"""
    from app.utils import save_uploaded_file
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'})
    
    file = request.files['file']
    subfolder = request.form.get('subfolder', '')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'})
    
    file_info = save_uploaded_file(file, subfolder)
    
    if file_info:
        return jsonify({
            'success': True,
            'filename': file_info['filename'],
            'original_filename': file_info['original_filename'],
            'file_type': file_info['extension']
        })
    else:
        return jsonify({'success': False, 'error': 'Type de fichier non autorisé'})