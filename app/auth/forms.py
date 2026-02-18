from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models import User
from flask_login import current_user

class LoginForm(FlaskForm):
    """Formulaire de connexion"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message='Le nom d\'utilisateur est requis')
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis')
    ])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class PasswordResetRequestForm(FlaskForm):
    """Formulaire pour demander la réinitialisation du mot de passe"""
    email = StringField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='L\'email doit être valide')
    ])
    submit = SubmitField('Envoyer la demande')

    def validate_email(self, email):
        """Vérifier que l'email existe dans la base de données"""
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Aucun compte n\'est associé à cet email.')

class PasswordResetForm(FlaskForm):
    """Formulaire de réinitialisation de mot de passe"""
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[
        DataRequired(),
        EqualTo('new_password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Réinitialiser le mot de passe')

class RegistrationForm(FlaskForm):
    """Formulaire d'inscription (admin seulement)"""
    role_id = SelectField('Rôle', coerce=int, validators=[DataRequired()])
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Le nom d\'utilisateur doit contenir entre 3 et 64 caractères')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    first_name = StringField('Prénom', validators=[
        DataRequired(),
        Length(max=64)
    ])
    last_name = StringField('Nom', validators=[
        DataRequired(),
        Length(max=64)
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Créer l\'utilisateur')

    def validate_username(self, username):
        """Valider l'unicité du nom d'utilisateur"""
        user = User.query. filter_by(username=username. data).first()
        if user is not None:
            raise ValidationError('Ce nom d\'utilisateur est déjà utilisé.')

    def validate_email(self, email):
        """Valider l'unicité de l'email"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None: 
            raise ValidationError('Cet email est déjà utilisé.')

class ProfileForm(FlaskForm):
    """Formulaire pour mettre à jour le profil"""
    first_name = StringField('Prénom', validators=[
        DataRequired(),
        Length(max=64)
    ])
    last_name = StringField('Nom', validators=[
        DataRequired(),
        Length(max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    current_password = PasswordField('Mot de passe actuel', validators=[
        Optional(),
        Length(min=8)
    ])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        Optional(),
        Length(min=8)
    ])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[
        Optional(),
        EqualTo('new_password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Mettre à jour')

    def validate_email(self, email):
        """Valider l'unicité de l'email"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.id != current_user.id:
            raise ValidationError('Cet email est déjà utilisé.')

    def validate_current_password(self, current_password):
        """Valider le mot de passe actuel si un nouveau mot de passe est fourni"""
        if self.new_password. data and not current_user.verify_password(current_password. data):
            raise ValidationError('Le mot de passe actuel est incorrect.')