from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class DashboardChartForm(FlaskForm):
    """Formulaire pour créer/modifier un graphique de dashboard"""
    title = StringField('Titre du graphique*', validators=[
        DataRequired(),
        Length(max=255, message='Le titre ne peut pas dépasser 255 caractères')
    ])
    
    chart_type = SelectField('Type de graphique*', choices=[
        ('bar', 'Barres'),
        ('line', 'Lignes'),
        ('pie', 'Camembert'),
        ('doughnut', 'Anneau'),
        ('radar', 'Radar'),
        ('polarArea', 'Zone polaire')
    ], validators=[DataRequired()])
    
    data_source = SelectField('Source de données*', choices=[
        ('stock', 'Stock - Quantité'),
        ('stock_value', 'Stock - Valeur'),
        ('stock_by_category', 'Stock par catégorie'),
        ('projects', 'Projets - Budget'),
        ('project_status', 'Statut des projets'),
        ('tasks', 'Tâches - Progression'),
        ('task_status', 'Statut des tâches'),
        ('personnel', 'Personnel par département'),
        ('monthly_costs', 'Coûts mensuels'),
        ('suppliers', 'Fournisseurs'),
        ('clients', 'Clients')
    ], validators=[DataRequired()])
    
    width = IntegerField('Largeur (colonnes)', validators=[
        Optional(),
        NumberRange(min=1, max=12, message='La largeur doit être entre 1 et 12 colonnes')
    ], default=6)
    
    height = IntegerField('Hauteur (px)', validators=[
        Optional(),
        NumberRange(min=100, max=800, message='La hauteur doit être entre 100 et 800 px')
    ], default=300)
    
    submit = SubmitField('Enregistrer')

class DashboardLayoutForm(FlaskForm):
    """Formulaire pour sauvegarder la disposition du dashboard"""
    layout = TextAreaField('Disposition', validators=[DataRequired()])
    submit = SubmitField('Sauvegarder la disposition')