from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import ListWidget, CheckboxInput

class GroupForm(FlaskForm):
    """Formulaire pour les groupes"""
    name = StringField('Nom du groupe*', validators=[
        DataRequired(),
        Length(max=128, message='Le nom ne peut pas dépasser 128 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class GroupMembersForm(FlaskForm):
    """Formulaire pour gérer les membres d'un groupe"""
    members = SelectMultipleField('Membres', coerce=int, validators=[Optional()])
    submit = SubmitField('Mettre à jour les membres')

class GroupTaskAssignmentForm(FlaskForm):
    """Formulaire pour assigner des tâches à un groupe"""
    tasks = SelectMultipleField('Tâches', coerce=int, validators=[Optional()])
    submit = SubmitField('Assigner les tâches')