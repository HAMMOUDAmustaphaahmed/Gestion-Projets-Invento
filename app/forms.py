from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, IntegerField, FloatField, DateField, SelectField, \
    SelectMultipleField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    Optional, NumberRange, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput
from datetime import date
import re

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

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

class RegistrationForm(FlaskForm):
    """Formulaire d'inscription (admin seulement)"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=64)
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
    role_id = SelectField('Rôle', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Créer l\'utilisateur')

class PasswordResetForm(FlaskForm):
    """Formulaire de réinitialisation de mot de passe"""
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('new_password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Réinitialiser le mot de passe')

class RoleForm(FlaskForm):
    """Formulaire pour créer/modifier un rôle"""
    name = StringField('Nom du rôle', validators=[
        DataRequired(),
        Length(max=64)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class SupplierForm(FlaskForm):
    """Formulaire pour les fournisseurs"""
    name = StringField('Nom du fournisseur*', validators=[
        DataRequired(),
        Length(max=128)
    ])
    contact_person = StringField('Personne de contact', validators=[
        Optional(),
        Length(max=128)
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(),
        Length(max=128)
    ])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[Optional(), Length(max=64)])
    country = StringField('Pays', validators=[Optional(), Length(max=64)])
    website = StringField('Site web', validators=[Optional(), Length(max=128)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class StockCategoryForm(FlaskForm):
    """Formulaire pour les catégories de stock"""
    name = StringField('Nom de la catégorie*', validators=[
        DataRequired(),
        Length(max=64)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class StockItemForm(FlaskForm):
    """Formulaire de base pour les éléments du stock"""
    reference = StringField('Référence*', validators=[
        DataRequired(),
        Length(max=64)
    ])
    libelle = StringField('Libellé*', validators=[
        DataRequired(),
        Length(max=255)
    ])
    item_type = SelectField('Type d\'élément*', validators=[DataRequired()])
    quantity = IntegerField('Quantité', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0)
    min_quantity = IntegerField('Quantité minimale', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0)
    price = FloatField('Prix unitaire', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0.0)
    location = StringField('Emplacement', validators=[Optional(), Length(max=128)])
    supplier_id = SelectField('Fournisseur', coerce=int, validators=[Optional()])
    category_id = SelectField('Catégorie', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')
    
    def validate_reference(self, field):
        """Valide l'unicité de la référence"""
        from app.models import StockItem
        from flask import request
        
        # Vérifier si c'est une mise à jour
        item_id = request.form.get('item_id')
        existing = StockItem.query.filter_by(reference=field.data).first()
        
        if existing and (not item_id or existing.id != int(item_id)):
            raise ValidationError('Cette référence existe déjà.')

class DynamicAttributeForm(FlaskForm):
    """Formulaire pour les attributs dynamiques"""
    name = StringField('Nom de l\'attribut', validators=[DataRequired()])
    value = StringField('Valeur', validators=[DataRequired()])
    data_type = SelectField('Type de données', choices=[
        ('string', 'Texte'),
        ('number', 'Nombre'),
        ('decimal', 'Décimal'),
        ('date', 'Date'),
        ('boolean', 'Oui/Non')
    ])

class StockFileForm(FlaskForm):
    """Formulaire pour uploader des fichiers de stock"""
    file = FileField('Fichier', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Formats autorisés: PDF, PNG, JPG')
    ])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Uploader')

class PersonnelForm(FlaskForm):
    """Formulaire pour le personnel"""
    employee_id = StringField('Matricule*', validators=[
        DataRequired(),
        Length(max=64)
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
    department = StringField('Département', validators=[Optional(), Length(max=64)])
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

class GroupForm(FlaskForm):
    """Formulaire pour les groupes"""
    name = StringField('Nom du groupe*', validators=[
        DataRequired(),
        Length(max=128)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    members = SelectMultipleField('Membres', coerce=int, validators=[Optional()])
    submit = SubmitField('Enregistrer')

class ProjectForm(FlaskForm):
    """Formulaire pour les projets"""
    name = StringField('Nom du projet*', validators=[
        DataRequired(),
        Length(max=255)
    ])
    client_id = SelectField('Client*', coerce=int, validators=[DataRequired(message='Veuillez sélectionner un client')])
    description = TextAreaField('Description', validators=[Optional()])
    start_date = DateField('Date de début*', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('Date de fin prévue*', validators=[DataRequired()], format='%Y-%m-%d')
    estimated_budget = FloatField('Budget estimé', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0.0)
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
    
    def validate_end_date(self, field):
        """Valide que la date de fin est après la date de début"""
        if self.start_date.data and field.data:
            if field.data < self.start_date.data:
                raise ValidationError('La date de fin doit être après la date de début.')

class TaskTypeForm(FlaskForm):
    """Formulaire pour les types de tâches"""
    name = StringField('Nom du type*', validators=[
        DataRequired(),
        Length(max=64)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    default_duration = IntegerField('Durée par défaut (jours)', validators=[
        Optional(),
        NumberRange(min=1)
    ])
    submit = SubmitField('Enregistrer')

class TaskForm(FlaskForm):
    """Formulaire pour les tâches"""
    name = StringField('Nom de la tâche*', validators=[
        DataRequired(),
        Length(max=255)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    start_date = DateField('Date de début*', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('Date de fin prévue*', validators=[DataRequired()], format='%Y-%m-%d')
    task_type_id = SelectField('Type de tâche', coerce=int, validators=[Optional()])
    status = SelectField('Statut', choices=[
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], default='pending')
    priority = SelectField('Priorité', choices=[
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute')
    ], default='medium')
    use_stock = BooleanField('Utiliser le stock', default=True)
    justification = TextAreaField('Justification', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    assigned_personnel = SelectMultipleField('Personnel assigné', coerce=int, validators=[Optional()])
    assigned_groups = SelectMultipleField('Groupes assignés', coerce=int, validators=[Optional()])
    submit = SubmitField('Enregistrer')

class TaskStockItemForm(FlaskForm):
    """Formulaire pour les éléments de stock d'une tâche"""
    stock_item_id = SelectField('Élément de stock', coerce=int, validators=[DataRequired()])
    estimated_quantity = IntegerField('Quantité estimée', validators=[
        DataRequired(),
        NumberRange(min=1)
    ])
    notes = TextAreaField('Notes', validators=[Optional()])
    return_to_stock = BooleanField('Retourner au stock', default=False)






class AdditionalCostForm(FlaskForm):
    """Formulaire pour les frais supplémentaires"""
    name = StringField('Nom du frais*', validators=[
        DataRequired(),
        Length(max=255)
    ])
    amount = FloatField('Montant*', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    justification = TextAreaField('Justification', validators=[Optional()])
    date = DateField('Date', validators=[Optional()], format='%Y-%m-%d', default=date.today)

class ProjectFileForm(FlaskForm):
    """Formulaire pour uploader des fichiers de projet"""
    file = FileField('Fichier', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Formats autorisés: PDF, PNG, JPG')
    ])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Uploader')

class DashboardChartForm(FlaskForm):
    """Formulaire pour créer/modifier un graphique de dashboard"""
    title = StringField('Titre du graphique*', validators=[
        DataRequired(),
        Length(max=255)
    ])
    chart_type = SelectField('Type de graphique*', choices=[
        ('bar', 'Barres'),
        ('line', 'Lignes'),
        ('pie', 'Camembert'),
        ('doughnut', 'Anneau'),
        ('radar', 'Radar')
    ], validators=[DataRequired()])
    data_source = SelectField('Source de données*', choices=[
        ('stock', 'Stock'),
        ('projects', 'Projets'),
        ('tasks', 'Tâches'),
        ('personnel', 'Personnel')
    ], validators=[DataRequired()])
    submit = SubmitField('Enregistrer')