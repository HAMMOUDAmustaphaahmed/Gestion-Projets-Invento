from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, TextAreaField, SelectField, DateField, \
    FloatField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from datetime import datetime

from flask_wtf.file import FileField, FileAllowed, FileRequired

class InterventionFileForm(FlaskForm):
    """Formulaire pour uploader des fichiers d'intervention"""
    file = FileField('Fichier', validators=[
        FileRequired(message="Veuillez sélectionner un fichier"),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'], 
                   'Formats autorisés: PDF, PNG, JPG, DOC, DOCX, XLS, XLSX')
    ])
    file_name = StringField('Nom du fichier*', validators=[
        DataRequired(message="Le nom du fichier est requis"),
        Length(max=255)
    ])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Uploader')
    
class InterventionTypeForm(FlaskForm):
    """Formulaire pour les types d'interventions"""
    name = StringField('Nom du type*', validators=[
        DataRequired(message="Le nom est requis"),
        Length(max=100)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class InterventionClassForm(FlaskForm):
    """Formulaire pour les classes d'interventions"""
    name = StringField('Nom de la classe*', validators=[
        DataRequired(message="Le nom est requis"),
        Length(max=100)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class InterventionEntityForm(FlaskForm):
    """Formulaire pour les entités d'interventions"""
    name = StringField('Nom de l\'entité*', validators=[
        DataRequired(message="Le nom est requis"),
        Length(max=100)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class InterventionStockForm(FlaskForm):
    """Formulaire pour les articles de stock d'une intervention"""
    stock_item_id = SelectField('Article', coerce=int, validators=[DataRequired()])
    estimated_quantity = FloatField('Quantité prévue', validators=[
        DataRequired(),
        NumberRange(min=0)
    ], default=0)
    actual_quantity = FloatField('Quantité utilisée', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    remaining_quantity = FloatField('Quantité restante', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    additional_quantity = FloatField('Quantité à ajouter', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    justification = TextAreaField('Justificatif', validators=[Optional()])
    validated = BooleanField('Validé', default=False)
    submit = SubmitField('Ajouter')

class AdditionalCostForm(FlaskForm):
    """Formulaire pour les coûts supplémentaires"""
    cost_name = StringField('Nom du coût*', validators=[
        DataRequired(message="Le nom est requis"),
        Length(max=100)
    ])
    amount = FloatField('Montant*', validators=[
        DataRequired(message="Le montant est requis"),
        NumberRange(min=0, message="Le montant doit être positif")
    ])
    submit = SubmitField('Ajouter')

def coerce_int_or_none(value):
    """Convertit en int ou None si vide"""
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class InterventionForm(FlaskForm):
    """Formulaire principal pour les interventions"""
    # Informations de base
    intervention_number = StringField('N° d\'intervention*', validators=[
        DataRequired(message="Le numéro d'intervention est requis"),
        Length(max=50)
    ])
    client_name = StringField('Nom du client*', validators=[
        DataRequired(message="Le nom du client est requis"),
        Length(max=200)
    ])
    location = StringField('Emplacement', validators=[
        Optional(),
        Length(max=200)
    ])
    
    # Sélections
    type_id = SelectField('Type d\'intervention*', coerce=int, validators=[
        DataRequired(message="Le type est requis")
    ])
    class_id = SelectField('Classe d\'intervention*', coerce=int, validators=[
        DataRequired(message="La classe est requise")
    ])
    entity_id = SelectField('Entité*', coerce=int, validators=[
        DataRequired(message="L'entité est requise")
    ])
    
    # Dates
    client_contact_date = DateField('Date de contact client*', 
                                   validators=[DataRequired(message="La date de contact est requise")], 
                                   format='%Y-%m-%d')
    intervention_date = DateField('Date de l\'intervention*', 
                                 validators=[DataRequired(message="La date d'intervention est requise")], 
                                 format='%Y-%m-%d')
    planned_end_date = DateField('Date de fin prévue*', 
                                validators=[DataRequired(message="La date de fin prévue est requise")], 
                                format='%Y-%m-%d')
    actual_end_date = DateField('Date de fin réelle', 
                               validators=[Optional()], 
                               format='%Y-%m-%d')
    
    # Statut
    status = SelectField('État', choices=[
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], default='planned')
    
    # Personnel
    personnel_ids = SelectMultipleField('Personnel', coerce=int, validators=[Optional()])
    
    # Descriptions
    anomaly_description = TextAreaField('Description de l\'anomalie', validators=[Optional()])
    tasks_description = TextAreaField('Description des tâches', validators=[Optional()])
    
    # Projet lié - CORRECTION ICI
    linked_to_project = BooleanField('Liée à un projet terminé', default=False)
    project_id = SelectField('Projet lié', coerce=coerce_int_or_none, validators=[Optional()])
    
    # Justificatifs
    justification_delay = TextAreaField('Justificatif de retard', validators=[Optional()])
    
    submit = SubmitField('Enregistrer')
    
    def validate_planned_end_date(self, field):
        """Valide que la date de fin prévue est après la date d'intervention"""
        if self.intervention_date.data and field.data:
            if field.data < self.intervention_date.data:
                raise ValidationError('La date de fin prévue doit être après la date d\'intervention')
    
    def validate_actual_end_date(self, field):
        """Valide que la date de fin réelle est cohérente"""
        if field.data:
            if self.intervention_date.data and field.data < self.intervention_date.data:
                raise ValidationError('La date de fin réelle doit être après la date d\'intervention')
    
    def validate_project_id(self, field):
        """Valide que le projet est sélectionné si linked_to_project est coché"""
        if self.linked_to_project.data and not field.data:
            raise ValidationError('Veuillez sélectionner un projet')