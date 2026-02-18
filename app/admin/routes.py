from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.admin import bp
from app.admin.forms import RoleForm
from app.auth.forms import RegistrationForm, PasswordResetForm
from app.models import User, Role, Notification
from app import db
from app.decorators import admin_required
from app.utils import sanitize_input
import json

@bp.route('/')
@admin_required
def index():
    """Tableau de bord administrateur"""
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_roles': Role.query.count(),
        'unread_notifications': Notification.query.filter_by(is_read=False).count()
    }
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         title='Administration',
                         stats=stats,
                         recent_users=recent_users)

@bp.route('/users')
@admin_required
def users():
    """Gestion des utilisateurs"""
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html',
                         title='Gestion des utilisateurs',
                         users=users)

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    """Activer/désactiver un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    # Ne pas permettre de désactiver soi-même
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas désactiver votre propre compte.'})
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activé' if user.is_active else 'désactivé'
    flash(f'Utilisateur {user.username} {status} avec succès.', 'success')
    
    return jsonify({'success': True, 'is_active': user.is_active})

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    # Ne pas permettre de supprimer soi-même
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Ne pas permettre de supprimer le dernier admin
    if user.role and user.role.name == 'admin':
        admin_count = User.query.join(User.role).filter_by(name='admin').count()
        if admin_count <= 1:
            flash('Impossible de supprimer le dernier administrateur.', 'danger')
            return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilisateur {user.username} supprimé avec succès.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/roles')
@admin_required
def roles():
    """Gestion des rôles"""
    roles = Role.query.all()
    return render_template('admin/roles.html',
                         title='Gestion des rôles',
                         roles=roles)

@bp.route('/roles/create', methods=['GET', 'POST'])
@admin_required
def create_role():
    """Créer un nouveau rôle"""
    form = RoleForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        name = sanitize_input(form.name.data)
        description = sanitize_input(form.description.data) if form.description.data else None
        
        # Vérifier si le rôle existe déjà
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            flash('Ce nom de rôle existe déjà.', 'danger')
            return redirect(url_for('admin.create_role'))
        
        # Créer le rôle avec des permissions par défaut
        role = Role(name=name, description=description)
        
        # Permissions par défaut (toutes à False)
        default_permissions = {
            'stock': {'read': False, 'create': False, 'update': False, 'delete': False},
            'projects': {'read': False, 'create': False, 'update': False, 'delete': False},
            'tasks': {'read': False, 'create': False, 'update': False, 'delete': False},
            'personnel': {'read': False, 'create': False, 'update': False, 'delete': False},
            'calendar': {'read': False},
            'dashboard': {'read': False}
        }
        role.set_permissions(default_permissions)
        
        db.session.add(role)
        db.session.commit()
        
        flash(f'Rôle {name} créé avec succès.', 'success')
        return redirect(url_for('admin.edit_role', role_id=role.id))
    
    return render_template('admin/role_form.html',
                         title='Créer un rôle',
                         form=form)

@bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_role(role_id):
    """Modifier un rôle existant"""
    role = Role.query.get_or_404(role_id)
    form = RoleForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        role.name = sanitize_input(form.name.data)
        role.description = sanitize_input(form.description.data) if form.description.data else None
        
        db.session.commit()
        
        flash(f'Rôle {role.name} mis à jour avec succès.', 'success')
        return redirect(url_for('admin.roles'))
    
    # Pré-remplir le formulaire
    form.name.data = role.name
    form.description.data = role.description
    
    return render_template('admin/role_form.html',
                         title='Modifier le rôle',
                         form=form, role=role)

@bp.route('/roles/<int:role_id>/permissions', methods=['GET', 'POST'])
@admin_required
def role_permissions(role_id):
    """Gérer les permissions d'un rôle"""
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'POST':
        try:
            permissions = json.loads(request.form.get('permissions', '{}'))
            role.set_permissions(permissions)
            db.session.commit()
            
            flash(f'Permissions du rôle {role.name} mises à jour avec succès.', 'success')
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    # Structure des permissions
    modules = [
        {
            'name': 'stock',
            'label': 'Stock',
            'actions': [
                {'name': 'read', 'label': 'Voir'},
                {'name': 'create', 'label': 'Créer'},
                {'name': 'update', 'label': 'Modifier'},
                {'name': 'delete', 'label': 'Supprimer'}
            ]
        },
        {
            'name': 'projects',
            'label': 'Projets',
            'actions': [
                {'name': 'read', 'label': 'Voir'},
                {'name': 'create', 'label': 'Créer'},
                {'name': 'update', 'label': 'Modifier'},
                {'name': 'delete', 'label': 'Supprimer'}
            ]
        },
        {
            'name': 'tasks',
            'label': 'Tâches',
            'actions': [
                {'name': 'read', 'label': 'Voir'},
                {'name': 'create', 'label': 'Créer'},
                {'name': 'update', 'label': 'Modifier'},
                {'name': 'delete', 'label': 'Supprimer'}
            ]
        },
        {
            'name': 'personnel',
            'label': 'Personnel',
            'actions': [
                {'name': 'read', 'label': 'Voir'},
                {'name': 'create', 'label': 'Créer'},
                {'name': 'update', 'label': 'Modifier'},
                {'name': 'delete', 'label': 'Supprimer'}
            ]
        },
        {
            'name': 'calendar',
            'label': 'Calendrier',
            'actions': [
                {'name': 'read', 'label': 'Voir'}
            ]
        },
        {
            'name': 'dashboard',
            'label': 'Tableau de bord',
            'actions': [
                {'name': 'read', 'label': 'Voir'}
            ]
        }
    ]
    
    current_permissions = role.get_permissions()
    
    return render_template('admin/role_permissions.html',
                         title=f'Permissions - {role.name}',
                         role=role,
                         modules=modules,
                         current_permissions=current_permissions)

@bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@admin_required
def delete_role(role_id):
    """Supprimer un rôle"""
    role = Role.query.get_or_404(role_id)
    
    # Ne pas permettre de supprimer le rôle admin
    if role.name == 'admin':
        flash('Impossible de supprimer le rôle administrateur.', 'danger')
        return redirect(url_for('admin.roles'))
    
    # Vérifier si des utilisateurs utilisent ce rôle
    user_count = User.query.filter_by(role_id=role_id).count()
    if user_count > 0:
        flash(f'Impossible de supprimer ce rôle car {user_count} utilisateur(s) l\'utilisent.', 'danger')
        return redirect(url_for('admin.roles'))
    
    db.session.delete(role)
    db.session.commit()
    
    flash(f'Rôle {role.name} supprimé avec succès.', 'success')
    return redirect(url_for('admin.roles'))

@bp.route('/notifications')
@admin_required
def notifications():
    """Gestion des notifications"""
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html',
                         title='Notifications',
                         notifications=notifications)

@bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marquer une notification comme lue"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Vérifier que la notification appartient à l'utilisateur
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Accès non autorisé.'})
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marquer toutes les notifications comme lues"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {'is_read': True}
    )
    db.session.commit()
    
    flash('Toutes les notifications ont été marquées comme lues.', 'success')
    return redirect(url_for('admin.notifications'))

@bp.route('/notifications/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Supprimer une notification"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Vérifier que la notification appartient à l'utilisateur
    if notification.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('admin.notifications'))
    
    db.session.delete(notification)
    db.session.commit()
    
    flash('Notification supprimée avec succès.', 'success')
    return redirect(url_for('admin.notifications'))