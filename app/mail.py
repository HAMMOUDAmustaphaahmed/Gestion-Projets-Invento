"""
Gestion des envois d'emails
"""
from flask import render_template, current_app
from flask_mail import Mail, Message

mail = Mail()

def send_password_reset_email(user):
    """
    Envoie un email de réinitialisation de mot de passe
    """
    token = user.get_reset_password_token()
    
    # Construire le lien de réinitialisation
    reset_url = current_app.config. get('SERVER_NAME')
    if not reset_url:
        reset_url = 'http://localhost:5000'  # À modifier en production
    
    reset_link = f"{reset_url}/auth/reset-password/{token}"
    
    msg = Message(
        'Réinitialisation de votre mot de passe',
        recipients=[user.email],
        html=render_template(
            'auth/email/reset_password.html',
            user=user,
            reset_link=reset_link
        ),
        sender=current_app.config['MAIL_USERNAME']
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi du mail: {e}")
        return False

def send_welcome_email(user):
    """Envoie un email de bienvenue à un nouvel utilisateur"""
    msg = Message(
        'Bienvenue sur Invento GMAO',
        recipients=[user.email],
        html=render_template(
            'auth/email/welcome.html',
            user=user
        ),
        sender=current_app.config['MAIL_USERNAME']
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi du mail:  {e}")
        return False