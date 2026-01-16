from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Optional
from app.models import Role

class RoleForm(FlaskForm):
    """Formulaire pour créer/modifier un rôle"""
    name = StringField('Nom du rôle', validators=[
        DataRequired(),
        Length(max=64, message='Le nom ne peut pas dépasser 64 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

    def __init__(self, original_name=None, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        """Valider l'unicité du nom du rôle"""
        if self.original_name != name.data:
            role = Role.query.filter_by(name=name.data).first()
            if role is not None:
                raise ValidationError('Ce nom de rôle est déjà utilisé.')

class PermissionForm(FlaskForm):
    """Formulaire pour les permissions (utilisé pour le formulaire dynamique)"""
    # Ce formulaire est généré dynamiquement
    submit = SubmitField('Enregistrer les permissions')

class NotificationSettingsForm(FlaskForm):
    """Formulaire pour les paramètres de notifications"""
    email_notifications = BooleanField('Notifications par email', default=True)
    stock_alerts = BooleanField('Alertes de stock', default=True)
    task_assignments = BooleanField('Assignations de tâches', default=True)
    project_updates = BooleanField('Mises à jour de projet', default=True)
    daily_digest = BooleanField('Résumé quotidien', default=False)
    submit = SubmitField('Enregistrer les paramètres')