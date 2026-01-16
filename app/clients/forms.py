from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional

class ClientForm(FlaskForm):
    """Formulaire pour les clients"""
    name = StringField('Nom du client*', validators=[
        DataRequired(message='Le nom est requis'),
        Length(max=128, message='Le nom ne peut pas dépasser 128 caractères')
    ])
    company = StringField('Société', validators=[
        Optional(),
        Length(max=128, message='Le nom de la société ne peut pas dépasser 128 caractères')
    ])
    contact_person = StringField('Personne de contact', validators=[
        Optional(),
        Length(max=128, message='Le nom de contact ne peut pas dépasser 128 caractères')
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(message='Email invalide'),
        Length(max=128, message='L\'email ne peut pas dépasser 128 caractères')
    ])
    phone = StringField('Téléphone', validators=[
        Optional(),
        Length(max=20, message='Le téléphone ne peut pas dépasser 20 caractères')
    ])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[
        Optional(),
        Length(max=64, message='La ville ne peut pas dépasser 64 caractères')
    ])
    postal_code = StringField('Code postal', validators=[
        Optional(),
        Length(max=20, message='Le code postal ne peut pas dépasser 20 caractères')
    ])
    country = StringField('Pays', validators=[
        Optional(),
        Length(max=64, message='Le pays ne peut pas dépasser 64 caractères')
    ])
    website = StringField('Site web', validators=[
        Optional(),
        Length(max=128, message='Le site web ne peut pas dépasser 128 caractères')
    ])
    siret = StringField('SIRET', validators=[
        Optional(),
        Length(max=64, message='Le SIRET ne peut pas dépasser 64 caractères')
    ])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_active = BooleanField('Client actif', default=True)
    submit = SubmitField('Enregistrer')