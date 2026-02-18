from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField,DateField, TextAreaField, SubmitField, IntegerField, \
    FloatField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models import StockItem
from datetime import date

class SupplierForm(FlaskForm):
    """Formulaire pour les fournisseurs"""
    name = StringField('Nom du fournisseur*', validators=[
        DataRequired(),
        Length(max=128, message='Le nom ne peut pas dépasser 128 caractères')
    ])
    contact_person = StringField('Personne de contact', validators=[
        Optional(),
        Length(max=128)
    ])
    email = StringField('Email', validators=[
        Optional(),
        Length(max=128)
    ])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[Optional(), Length(max=64)])
    country = StringField('Pays', validators=[Optional(), Length(max=64)])
    website = StringField('Site web', validators=[Optional(), Length(max=128)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')


class StockMovementForm(FlaskForm):
    """Formulaire pour les mouvements de stock"""
    movement_type = SelectField('Type de mouvement*', choices=[
        ('purchase', 'Achat/Réception'),
        ('sale', 'Vente/Sortie'),
        ('transfer', 'Transfert'),
        ('adjustment', 'Ajustement'),
        ('waste', 'Perte/Déchet'),
        ('return', 'Retour')
    ], validators=[DataRequired()])
    
    quantity = FloatField('Quantité*', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='La quantité doit être positive')
    ])
    
    unit_price = FloatField('Prix unitaire', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    
    reference = StringField('Référence', validators=[
        Optional(),
        Length(max=64)
    ])  # N° facture, bon de livraison, etc.
    
    supplier_id = SelectField('Fournisseur', coerce=int, validators=[Optional()])
    task_id = SelectField('Tâche', coerce=int, validators=[Optional()])
    project_id = SelectField('Projet', coerce=int, validators=[Optional()])
    
    justification = TextAreaField('Justification/Motif', validators=[
        Optional(),
        Length(max=500)
    ])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer le mouvement')


class PurchaseOrderForm(FlaskForm):
    """Formulaire pour les commandes d'achat"""
    order_number = StringField('Numéro de commande*', validators=[
        DataRequired(),
        Length(max=64)
    ])
    
    supplier_id = SelectField('Fournisseur*', coerce=int, validators=[DataRequired()])
    
    order_date = DateField('Date de commande*', validators=[
        DataRequired()
    ], default=date.today, format='%Y-%m-%d')
    
    delivery_date = DateField('Date de livraison prévue', validators=[
        Optional()
    ], format='%Y-%m-%d')
    
    status = SelectField('Statut', choices=[
        ('pending', 'En attente'),
        ('ordered', 'Commandée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée')
    ], default='pending')
    
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Créer la commande')


class PurchaseOrderItemForm(FlaskForm):
    """Formulaire pour les éléments d'une commande"""
    stock_item_id = SelectField('Article*', coerce=int, validators=[DataRequired()])
    quantity_ordered = FloatField('Quantité commandée*', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    unit_price = FloatField('Prix unitaire*', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Ajouter à la commande')



class StockCategoryForm(FlaskForm):
    """Formulaire pour les catégories de stock"""
    name = StringField('Nom de la catégorie*', validators=[
        DataRequired(),
        Length(max=64, message='Le nom ne peut pas dépasser 64 caractères')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class StockItemForm(FlaskForm):
    """Formulaire de base pour les éléments du stock"""
    reference = StringField('Référence*', validators=[
        DataRequired(),
        Length(max=64, message='La référence ne peut pas dépasser 64 caractères')
    ])
    libelle = StringField('Libellé*', validators=[
        DataRequired(),
        Length(max=255, message='Le libellé ne peut pas dépasser 255 caractères')
    ])
    item_type = SelectField('Type d\'élément*', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantité', validators=[
        Optional(),
        NumberRange(min=0, message='La quantité ne peut pas être négative')
    ], default=0)
    min_quantity = IntegerField('Quantité minimale', validators=[
        Optional(),
        NumberRange(min=0, message='La quantité minimale ne peut pas être négative')
    ], default=0)
    price = FloatField('Prix unitaire (€)', validators=[
        Optional(),
        NumberRange(min=0, message='Le prix ne peut pas être négatif')
    ], default=0.0)
    location = StringField('Emplacement', validators=[Optional(), Length(max=128)])
    supplier_id = SelectField('Fournisseur', coerce=int, validators=[Optional()])
    category_id = SelectField('Catégorie', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')

    def validate_reference(self, reference):
        """Valider l'unicité de la référence"""
        from flask import request
        
        # Vérifier si c'est une mise à jour
        item_id = request.form.get('item_id')
        existing = StockItem.query.filter_by(reference=reference.data).first()
        
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
    ], default='string')

class StockFileForm(FlaskForm):
    """Formulaire pour uploader des fichiers de stock"""
    file = FileField('Fichier', validators=[
        FileRequired(message='Veuillez sélectionner un fichier'),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Formats autorisés: PDF, PNG, JPG')
    ])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Uploader')