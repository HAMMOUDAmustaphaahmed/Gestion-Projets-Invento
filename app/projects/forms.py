from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import DecimalField,HiddenField,StringField, TextAreaField, SubmitField, DateField, FloatField, \
    IntegerField, SelectField, SelectMultipleField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from datetime import date
from wtforms.widgets import ListWidget, CheckboxInput

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ProjectForm(FlaskForm):
    """Formulaire pour les projets"""
    name = StringField('Nom du projet*', validators=[
        DataRequired(),
        Length(max=255, message='Le nom ne peut pas dépasser 255 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    start_date = DateField('Date de début*', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('Date de fin prévue*', validators=[DataRequired()], format='%Y-%m-%d')
    estimated_budget = FloatField('Budget estimé (TND)', validators=[Optional(),NumberRange(min=0, message='Le budget doit être positif')], default=0.0)
    budget_reel = FloatField('Budget réel (TND)', validators=[Optional(),NumberRange(min=0, message='Le budget réel doit être positif')], default=0.0)
    prix_vente = FloatField('Prix de vente (TND)', validators=[Optional(),NumberRange(min=0, message='Le prix de vente doit être positif')], default=0.0)
    marge = FloatField('Marge (TND)', validators=[Optional()], default=0.0)
    status = SelectField('Statut', choices=[
        ('planning', 'Planification'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé')
    ], default='planning')
    priority = SelectField('Priorité', choices=[
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute')
    ], default='medium')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')

    def validate_end_date(self, end_date):
        """Valider que la date de fin est après la date de début"""
        if self.start_date.data and end_date.data:
            if end_date.data < self.start_date.data:
                raise ValidationError('La date de fin doit être après la date de début.')

class TaskTypeForm(FlaskForm):
    """Formulaire pour les types de tâches"""
    name = StringField('Nom du type*', validators=[
        DataRequired(),
        Length(max=64, message='Le nom ne peut pas dépasser 64 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    default_duration = IntegerField('Durée par défaut (jours)', validators=[
        Optional(),
        NumberRange(min=1, message='La durée doit être d\'au moins 1 jour')
    ])
    submit = SubmitField('Enregistrer')

class TaskForm(FlaskForm):
    """Formulaire pour les tâches"""
    name = StringField('Nom de la tâche*', validators=[
        DataRequired(),
        Length(max=255, message='Le nom ne peut pas dépasser 255 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    start_date = DateField('Date de début*', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('Date de fin prévue*', validators=[DataRequired()], format='%Y-%m-%d')
    task_type_id = SelectField('Type de tâche', coerce=int, validators=[Optional()])
    status = SelectField('Statut', choices=[
        ('pending', 'En attente'),
        ('planning', 'Planification'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('validated', 'Validée'),
        ('cancelled', 'Annulée')
    ], default='planning')
    priority = SelectField('Priorité', choices=[
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute')
    ], default='medium')
    use_stock = BooleanField('Utiliser le stock', default=True)
    justification = TextAreaField('Justification globale', validators=[Optional()])
    notes = TextAreaField('Notes générales', validators=[Optional()])
    
    # Assignation (personnel OU groupes)
    assigned_personnel = SelectMultipleField('Personnel assigné', coerce=int, validators=[Optional()])
    assigned_groups = SelectMultipleField('Groupes assignés', coerce=int, validators=[Optional()])
    # Pour l'assignation exclusive (soit personnel, soit groupes)
    assignment_type = SelectField('Type d\'assignation', choices=[
        ('personnel', 'Personnel individuel'),
        ('groups', 'Groupes')
    ], default='personnel')
    
    submit = SubmitField('Enregistrer')

    def validate_end_date(self, end_date):
        """Valider que la date de fin est après la date de début"""
        if self.start_date.data and end_date.data:
            if end_date.data < self.start_date.data:
                raise ValidationError('La date de fin doit être après la date de début.')

class TaskStockItemForm(FlaskForm):
    """Formulaire pour les éléments de stock d'une tâche"""
    stock_item_id = SelectField('Élément de stock*', coerce=int, validators=[DataRequired()])
    estimated_quantity = DecimalField('Quantité estimée*', places=2, validators=[
        DataRequired(),
        NumberRange(min=0.01, message='La quantité doit être supérieure à 0')
    ])
    unit_type = SelectField('Unité', choices=[
        ('piece', 'Pièce'),
        ('lot', 'Lot'),
        ('meter', 'Mètre'),
        ('kilogram', 'Kilogramme'),
        ('liter', 'Litre'),
        ('box', 'Carton'),
        ('palette', 'Palette')
    ], default='piece')
    actual_quantity_used = DecimalField('Quantité réellement utilisée', places=2, validators=[
        Optional(),
        NumberRange(min=0)
    ])
    remaining_quantity = DecimalField('Quantité restante après tâche', places=2, validators=[
        Optional(),
        NumberRange(min=0)
    ])
    return_to_stock = BooleanField('Retourner les restes au stock', default=True)
    justification_shortage = TextAreaField('Justificatif pour quantité insuffisante')
    notes = TextAreaField('Notes spécifiques')
    submit_item = SubmitField('Ajouter l\'élément')

class StockShortageForm(FlaskForm):
    """Formulaire pour justifier les quantités insuffisantes"""
    stock_item_id = HiddenField()
    shortage_quantity = DecimalField('Quantité supplémentaire nécessaire', places=2, validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    justification = TextAreaField('Justification*', validators=[DataRequired()])
    urgent = BooleanField('Besoin urgent')
    submit_shortage = SubmitField('Valider le justificatif')

class AdditionalCostForm(FlaskForm):
    """Formulaire pour les frais supplémentaires"""
    name = StringField('Nom du frais*', validators=[
        DataRequired(),
        Length(max=255)
    ])
    amount = FloatField('Montant* (€)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Le montant doit être positif')
    ])
    justification = TextAreaField('Justification', validators=[Optional()])
    date = DateField('Date', validators=[Optional()], format='%Y-%m-%d', default=date.today)
    submit = SubmitField('Ajouter le frais')

class ProjectFileForm(FlaskForm):
    """Formulaire pour uploader des fichiers de projet"""
    file = FileField('Fichier', validators=[
        FileRequired(message='Veuillez sélectionner un fichier'),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Formats autorisés: PDF, PNG, JPG')
    ])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Uploader')
