from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, DateField, TextAreaField, SubmitField, IntegerField, \
    FloatField, SelectField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models import Equipment, EquipmentCategory
from datetime import date

class EquipmentCategoryForm(FlaskForm):
    """Formulaire pour les catégories d'équipements"""
    name = StringField('Nom de la catégorie*', validators=[
        DataRequired(),
        Length(max=64, message='Le nom ne peut pas dépasser 64 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class EquipmentForm(FlaskForm):
    """Formulaire de base pour les équipements"""
    reference = StringField('Référence*', validators=[
        DataRequired(),
        Length(max=64, message='La référence ne peut pas dépasser 64 caractères')
    ])
    name = StringField('Nom*', validators=[
        DataRequired(),
        Length(max=255, message='Le nom ne peut pas dépasser 255 caractères')
    ])
    
    category_id = SelectField('Catégorie', coerce=int, validators=[Optional()])
    supplier_id = SelectField('Fournisseur', coerce=int, validators=[Optional()])
    
    # Informations techniques
    serial_number = StringField('Numéro de série', validators=[
        Optional(),
        Length(max=128)
    ])
    model = StringField('Modèle', validators=[Optional(), Length(max=128)])
    brand = StringField('Marque', validators=[Optional(), Length(max=128)])
    
    # Statut et localisation
    status = SelectField('Statut', choices=[
        ('available', 'Disponible'),
        ('in_use', 'En utilisation'),
        ('maintenance', 'En maintenance'),
        ('out_of_service', 'Hors service'),
        ('reserved', 'Réservé'),
        ('disposed', 'Mis au rebut')
    ], default='available')
    
    location = StringField('Emplacement', validators=[Optional(), Length(max=128)])
    department = StringField('Département/Service', validators=[Optional(), Length(max=64)])
    responsible_person = StringField('Personne responsable', validators=[Optional(), Length(max=128)])
    
    # Dates
    purchase_date = DateField('Date d\'achat', validators=[Optional()], format='%Y-%m-%d')
    warranty_until = DateField('Garantie jusqu\'au', validators=[Optional()], format='%Y-%m-%d')
    last_maintenance = DateField('Dernière maintenance', validators=[Optional()], format='%Y-%m-%d')
    next_maintenance = DateField('Prochaine maintenance', validators=[Optional()], format='%Y-%m-%d')
    
    # Coûts
    purchase_price = FloatField('Prix d\'achat (€)', validators=[
        Optional(),
        NumberRange(min=0, message='Le prix ne peut pas être négatif')
    ], default=0.0)
    
    current_value = FloatField('Valeur actuelle (€)', validators=[
        Optional(),
        NumberRange(min=0, message='La valeur ne peut pas être négative')
    ], default=0.0)
    
    # Éléments de stock attachés
    stock_items = SelectMultipleField('Éléments de stock associés', coerce=int, validators=[Optional()])
    
    # Notes
    description = TextAreaField('Description', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Enregistrer')
    
    def validate_reference(self, reference):
        """Valider l'unicité de la référence"""
        from flask import request
        
        # Vérifier si c'est une mise à jour
        equipment_id = request.form.get('equipment_id')
        existing = Equipment.query.filter_by(reference=reference.data).first()
        
        if existing and (not equipment_id or existing.id != int(equipment_id)):
            raise ValidationError('Cette référence existe déjà.')

class EquipmentFileForm(FlaskForm):
    """Formulaire pour uploader des fichiers d'équipements"""
    file = FileField('Fichier', validators=[
        FileRequired(message='Veuillez sélectionner un fichier'),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'], 
                   'Formats autorisés: PDF, images, documents Office')
    ])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Uploader')

class EquipmentMaintenanceForm(FlaskForm):
    """Formulaire pour les maintenances d'équipements"""
    maintenance_type = SelectField('Type de maintenance*', choices=[
        ('preventive', 'Maintenance préventive'),
        ('corrective', 'Maintenance corrective'),
        ('calibration', 'Étalonnage'),
        ('inspection', 'Inspection'),
        ('repair', 'Réparation')
    ], validators=[DataRequired()])
    
    maintenance_date = DateField('Date de maintenance*', validators=[
        DataRequired()
    ], default=date.today, format='%Y-%m-%d')
    
    next_maintenance_date = DateField('Prochaine maintenance', validators=[
        Optional()
    ], format='%Y-%m-%d')
    
    performed_by = StringField('Effectué par', validators=[Optional(), Length(max=128)])
    cost = FloatField('Coût (€)', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    
    description = TextAreaField('Description*', validators=[
        DataRequired(),
        Length(max=1000)
    ])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer la maintenance')

class EquipmentStockAssociationForm(FlaskForm):
    """Formulaire pour associer un élément de stock à un équipement"""
    stock_item_id = SelectField('Élément de stock*', coerce=int, validators=[DataRequired()])
    quantity_used = FloatField('Quantité utilisée*', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='La quantité doit être positive')
    ], default=1.0)
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Associer')