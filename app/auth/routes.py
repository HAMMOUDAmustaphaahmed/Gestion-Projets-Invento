from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.auth.forms import (
    LoginForm, RegistrationForm, PasswordResetForm, 
    PasswordResetRequestForm, ProfileForm
)
from app.models import User, Role
from app import db, login_manager
from app.decorators import admin_required
from app.utils import sanitize_input
from app.mail import send_password_reset_email  # Si tu utilises Flask-Mail
from datetime import datetime
import json

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Gestion de la connexion utilisateur"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = sanitize_input(form.username.data)
        
        # Retry logic for database connection issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Rechercher l'utilisateur
                user = User.query.filter_by(username=username).first()
                
                if user is None or not user.verify_password(form.password.data):
                    flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
                    return redirect(url_for('auth.login'))
                
                if hasattr(user, 'is_active') and not user.is_active:
                    flash('Votre compte est désactivé. Contactez l\'administrateur.', 'warning')
                    return redirect(url_for('auth.login'))
                
                # Connexion réussie
                login_user(user, remember=form.remember_me.data)
                
                # Mettre à jour la date de dernière connexion
                if hasattr(user, 'last_login'):
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                
                flash(f'Bienvenue {user.username}!', 'success')
                
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard.index')
                return redirect(next_page)
                
            except Exception as e:
                # If it's the last attempt, show error
                if attempt == max_retries - 1:
                    flash('Erreur de connexion à la base de données. Veuillez réessayer dans quelques instants.', 'danger')
                    app.logger.error(f'Database error during login: {str(e)}')
                    return redirect(url_for('auth.login'))
                # Otherwise, wait and retry
                time.sleep(1)
                continue
    
    # Afficher les erreurs de validation
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    
    return render_template('auth/login.html', title='Connexion', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Permet à l'utilisateur de demander la réinitialisation de son mot de passe. 
    Un email avec un lien de réinitialisation sera envoyé. 
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Envoyer l'email de réinitialisation
            if send_password_reset_email(user):
                flash('Un email de réinitialisation a été envoyé à votre adresse.  '
                      'Veuillez vérifier votre boîte de réception.', 'info')
            else:
                flash('Erreur lors de l\'envoi de l\'email.  Veuillez réessayer plus tard.', 'danger')
        else:
            # Ne pas révéler si l'email existe ou non (sécurité)
            flash('Si un compte est associé à cet email, vous recevrez un lien de réinitialisation. ', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', 
                         title='Réinitialiser le mot de passe', 
                         form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Permet à l'utilisateur de réinitialiser son mot de passe avec un token valide.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Le lien de réinitialisation est invalide ou expiré.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        user.password = form.new_password.data
        db.session.commit()
        
        flash('Votre mot de passe a été réinitialisé avec succès!  '
              'Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth. login'))
    
    return render_template('auth/reset_password.html', 
                         title='Réinitialiser le mot de passe',
                         form=form)

@bp.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    """Création d'un nouvel utilisateur (admin seulement)"""
    form = RegistrationForm()
    
    # Remplir les choix de rôles
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        username = sanitize_input(form. username.data)
        email = sanitize_input(form.email.data)
        first_name = sanitize_input(form. first_name.data)
        last_name = sanitize_input(form.last_name.data)
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                flash('Ce nom d\'utilisateur existe déjà. ', 'danger')
            else:
                flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Créer le nouvel utilisateur
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.password = form.password.data
        user.role_id = form.role_id.data
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Utilisateur {username} créé avec succès! ', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('auth/register.html', title='Créer un utilisateur', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Profil de l'utilisateur connecté"""
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        current_user.first_name = sanitize_input(form.first_name.data)
        current_user.last_name = sanitize_input(form.last_name.data)
        current_user.email = sanitize_input(form.email.data)
        
        # Vérifier si l'email est déjà utilisé
        if current_user.email != form.email.data:
            existing = User.query.filter_by(email=form.email.data).first()
            if existing and existing.id != current_user.id:
                flash('Cet email est déjà utilisé.', 'danger')
                return redirect(url_for('auth.profile'))
        
        # Changer le mot de passe si fourni
        if form.current_password.data and form.new_password.data:
            if current_user.verify_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                flash('Mot de passe mis à jour.', 'success')
            else:
                flash('Mot de passe actuel incorrect.', 'danger')
                return redirect(url_for('auth.profile'))
        
        db.session.commit()
        flash('Profil mis à jour avec succès!', 'success')
        return redirect(url_for('auth.profile'))
    
    # Pré-remplir le formulaire
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.email.data = current_user.email
    
    # Calculer les statistiques de l'utilisateur
    from app.models import Project, Task, Notification
    
    user_stats = {
        'projects': Project.query.filter(
            Project.tasks.any(Task.assigned_personnel.any(id=current_user.id))
        ).count(),
        'tasks': Task.query.filter(
            Task.assigned_personnel.any(id=current_user.id)
        ).count(),
        'notifications': Notification.query.filter_by(
            user_id=current_user.id
        ).count(),
        'activity_days': 0  # À implémenter si vous avez un suivi d'activité
    }
    
    return render_template('auth/profile.html', 
                         title='Mon Profil',
                         form=form,
                         user_stats=user_stats)

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Mettre à jour les informations du profil (sans mot de passe)"""
    current_user.first_name = sanitize_input(request.form.get('first_name', '')) or None
    current_user.last_name = sanitize_input(request.form.get('last_name', '')) or None
    current_user.email = sanitize_input(request.form.get('email', ''))
    current_user.phone = sanitize_input(request.form.get('phone', '')) or None
    
    # Vérifier l'email unique
    existing = User.query.filter_by(email=current_user.email).first()
    if existing and existing.id != current_user.id:
        flash('Cet email est déjà utilisé.', 'danger')
        return redirect(url_for('auth.profile'))
    
    db.session.commit()
    flash('Profil mis à jour avec succès!', 'success')
    return redirect(url_for('auth.profile'))

@bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Changer le mot de passe"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Vérifier le mot de passe actuel
    if not current_user.verify_password(current_password):
        flash('Mot de passe actuel incorrect.', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Vérifier que les nouveaux mots de passe correspondent
    if new_password != confirm_password:
        flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Vérifier la longueur du mot de passe
    if len(new_password) < 8:
        flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Changer le mot de passe
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Mot de passe changé avec succès!', 'success')
    return redirect(url_for('auth.profile'))

@login_manager.unauthorized_handler
def unauthorized():
    """Gestion des accès non autorisés"""
    flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
    return redirect(url_for('auth.login', next=request.url))
