from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField, BooleanField, \
    SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, Email
from datetime import date
from wtforms.widgets import ListWidget, CheckboxInput

class PersonnelForm(FlaskForm):
    """Formulaire pour le personnel"""
    employee_id = StringField('Matricule*', validators=[
        DataRequired(),
        Length(max=64, message='Le matricule ne peut pas dépasser 64 caractères')
    ])
    first_name = StringField('Prénom*', validators=[
        DataRequired(),
        Length(max=64)
    ])
    last_name = StringField('Nom*', validators=[
        DataRequired(),
        Length(max=64)
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(),
        Length(max=120)
    ])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    department = SelectField('Département', choices=[
        ('', '-- Sélectionner --'),
        ('production', 'Production'),
        ('maintenance', 'Maintenance'),
        ('qualite', 'Qualité'),
        ('logistique', 'Logistique'),
        ('achats', 'Achats'),
        ('rh', 'Ressources Humaines'),
        ('informatique', 'Informatique'),
        ('administration', 'Administration'),
        ('autre', 'Autre')
    ], validators=[Optional()])
    position = StringField('Poste', validators=[Optional(), Length(max=64)])
    hire_date = DateField('Date d\'embauche', validators=[Optional()], format='%Y-%m-%d')
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[Optional(), Length(max=64)])
    country = StringField('Pays', validators=[Optional(), Length(max=64)])
    emergency_contact = StringField('Contact d\'urgence', validators=[Optional(), Length(max=128)])
    emergency_phone = StringField('Téléphone d\'urgence', validators=[Optional(), Length(max=20)])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_active = BooleanField('Actif', default=True)
    submit = SubmitField('Enregistrer')

    def validate_employee_id(self, employee_id):
        """Valider l'unicité du matricule"""
        from app.models import Personnel
        from flask import request
        
        # Vérifier si c'est une mise à jour
        personnel_id = request.form.get('personnel_id')
        existing = Personnel.query.filter_by(employee_id=employee_id.data).first()
        
        if existing and (not personnel_id or existing.id != int(personnel_id)):
            raise ValidationError('Ce matricule existe déjà.')