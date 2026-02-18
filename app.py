#!/usr/bin/env python3
"""
Application GMAO - Gestion de Maintenance Assistée par Ordinateur
Point d'entrée principal
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au chemin
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import User, Role, StockItem, Project, Task, Personnel, Notification, \
    Supplier, StockCategory, TaskType, Group, DashboardChart, InterventionType, \
    InterventionClass, InterventionEntity, Intervention, InterventionFile, Equipment
from flask_migrate import Migrate
import click

# Créer l'application
app = create_app(os.getenv('FLASK_CONFIG') or 'default')


migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """Crée un contexte shell pour Flask shell"""
    return dict(
        app=app, 
        db=db, 
        User=User, 
        Role=Role, 
        StockItem=StockItem,
        Project=Project,
        Task=Task,
        Personnel=Personnel,
        Notification=Notification,
        Supplier=Supplier,
        StockCategory=StockCategory,
        TaskType=TaskType,
        Group=Group,
        DashboardChart=DashboardChart,
        InterventionType=InterventionType,
        InterventionClass=InterventionClass,
        InterventionEntity=InterventionEntity,
        InterventionFile=InterventionFile,
        Intervention=Intervention,
        Equipments=Equipments
    )

@app.cli.command()
@click.option('--drop', is_flag=True, help='Supprimer la base de données avant création')
def init_db(drop):
    """Initialise la base de données avec des données par défaut"""
    if drop:
        click.confirm('Cette opération va supprimer toutes les données. Continuer ?', abort=True)
        db.drop_all()
        click.echo('Base de données supprimée.')
    
    db.create_all()
    
    # Créer les rôles par défaut
    roles = [
        {
            'name': 'admin',
            'description': 'Administrateur système avec tous les droits',
            'permissions': {
                'admin': {'all': True},
                'stock': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'equipments': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'projects': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'tasks': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'personnel': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'interventions': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'calendar': {'read': True, 'create': True, 'update': True, 'export': True},
                'dashboard': {'read': True, 'create': True, 'update': True, 'export': True},
                'settings': {'all': True}
            }
        },
        {
            'name': 'gestionnaire',
            'description': 'Gestionnaire avec droits étendus',
            'permissions': {
                'stock': {'read': True, 'create': True, 'update': True, 'delete': False},
                'projects': {'read': True, 'create': True, 'update': True, 'delete': False},
                'tasks': {'read': True, 'create': True, 'update': True, 'delete': False},
                'personnel': {'read': True, 'create': True, 'update': True, 'delete': False},
                'interventions': {'read': True, 'create': True, 'update': True, 'delete': False},
                'calendar': {'read': True, 'create': True, 'update': True},
                'dashboard': {'read': True, 'create': True, 'update': True}
            }
        },
        {
            'name': 'technicien',
            'description': 'Technicien avec droits limités',
            'permissions': {
                'stock': {'read': True, 'create': False, 'update': False, 'delete': False},
                'projects': {'read': True, 'create': False, 'update': False, 'delete': False},
                'tasks': {'read': True, 'create': False, 'update': True, 'delete': False},
                'personnel': {'read': False, 'create': False, 'update': False, 'delete': False},
                'interventions': {'read': True, 'create': False, 'update': True, 'delete': False},
                'calendar': {'read': True, 'create': False, 'update': False},
                'dashboard': {'read': True, 'create': False, 'update': False}
            }
        },
        {
            'name': 'consultant',
            'description': 'Consultant en lecture seule',
            'permissions': {
                'stock': {'read': True, 'create': False, 'update': False, 'delete': False},
                'projects': {'read': True, 'create': False, 'update': False, 'delete': False},
                'tasks': {'read': True, 'create': False, 'update': False, 'delete': False},
                'personnel': {'read': False, 'create': False, 'update': False, 'delete': False},
                'interventions': {'read': True, 'create': False, 'update': False, 'delete': False},
                'calendar': {'read': True, 'create': False, 'update': False},
                'dashboard': {'read': True, 'create': False, 'update': False}
            }
        }
    ]
    
    for role_data in roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(name=role_data['name'], description=role_data['description'])
            role.set_permissions(role_data['permissions'])
            db.session.add(role)
            click.echo(f'Rôle créé: {role.name}')
    
    db.session.commit()
    
    # Créer un utilisateur admin s'il n'existe pas
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@gmao.com',
            first_name='Administrateur',
            last_name='Système'
        )
        admin_user.password = 'Admin123!'  # À changer après la première connexion
        admin_role = Role.query.filter_by(name='admin').first()
        admin_user.role = admin_role
        db.session.add(admin_user)
        click.echo(f'Utilisateur admin créé: {admin_user.username}')
    
    # Créer quelques catégories de stock
    categories = [
        {'name': 'Pièces détachées', 'description': 'Pièces de rechange pour équipements'},
        {'name': 'Outillage', 'description': 'Outils manuels et électriques'},
        {'name': 'Consommables', 'description': 'Matériaux consommables'},
        {'name': 'Équipement de sécurité', 'description': 'Équipements de protection individuelle'},
        {'name': 'Matériel informatique', 'description': 'Ordinateurs, périphériques et composants'}
    ]
    
    for cat_data in categories:
        category = StockCategory.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = StockCategory(**cat_data)
            db.session.add(category)
            click.echo(f'Catégorie créée: {category.name}')
    
    # Créer quelques types de tâches
    task_types = [
        {'name': 'Maintenance préventive', 'description': 'Maintenance planifiée', 'default_duration': 2},
        {'name': 'Maintenance corrective', 'description': 'Réparation suite à panne', 'default_duration': 4},
        {'name': 'Installation', 'description': 'Installation d\'équipement', 'default_duration': 8},
        {'name': 'Inspection', 'description': 'Contrôle et vérification', 'default_duration': 1},
        {'name': 'Calibration', 'description': 'Étalonnage d\'équipement', 'default_duration': 3}
    ]
    
    for type_data in task_types:
        task_type = TaskType.query.filter_by(name=type_data['name']).first()
        if not task_type:
            task_type = TaskType(**type_data)
            db.session.add(task_type)
            click.echo(f'Type de tâche créé: {task_type.name}')
    
    # Créer quelques types d'interventions
    intervention_types = [
        {'name': 'Maintenance préventive', 'description': 'Intervention de maintenance préventive programmée'},
        {'name': 'Maintenance corrective', 'description': 'Intervention suite à une panne ou dysfonctionnement'},
        {'name': 'Installation', 'description': 'Installation de nouveaux équipements'},
        {'name': 'Contrôle qualité', 'description': 'Contrôle et vérification qualité'},
        {'name': 'Audit', 'description': 'Audit de conformité et sécurité'}
    ]
    
    for type_data in intervention_types:
        intervention_type = InterventionType.query.filter_by(name=type_data['name']).first()
        if not intervention_type:
            intervention_type = InterventionType(**type_data)
            db.session.add(intervention_type)
            click.echo(f'Type d\'intervention créé: {intervention_type.name}')
    
    # Créer quelques classes d'interventions
    intervention_classes = [
        {'name': 'Urgente', 'description': 'Intervention à réaliser dans les 24h'},
        {'name': 'Prioritaire', 'description': 'Intervention à réaliser dans les 48h'},
        {'name': 'Normale', 'description': 'Intervention à planifier'},
        {'name': 'Planifiée', 'description': 'Intervention programmée'}
    ]
    
    for class_data in intervention_classes:
        intervention_class = InterventionClass.query.filter_by(name=class_data['name']).first()
        if not intervention_class:
            intervention_class = InterventionClass(**class_data)
            db.session.add(intervention_class)
            click.echo(f'Classe d\'intervention créée: {intervention_class.name}')
    
    # Créer quelques entités d'interventions
    intervention_entities = [
        {'name': 'Production', 'description': 'Entité production'},
        {'name': 'Maintenance', 'description': 'Entité maintenance'},
        {'name': 'Qualité', 'description': 'Entité qualité'},
        {'name': 'Sécurité', 'description': 'Entité sécurité'},
        {'name': 'Informatique', 'description': 'Entité informatique'}
    ]
    
    for entity_data in intervention_entities:
        intervention_entity = InterventionEntity.query.filter_by(name=entity_data['name']).first()
        if not intervention_entity:
            intervention_entity = InterventionEntity(**entity_data)
            db.session.add(intervention_entity)
            click.echo(f'Entité d\'intervention créée: {intervention_entity.name}')
    
    db.session.commit()
    
    click.echo('\n' + '='*50)
    click.echo('Base de données initialisée avec succès!')
    click.echo('='*50)
    click.echo(f'Utilisateur admin créé: {admin_user.username}')
    click.echo('Mot de passe par défaut: Admin123!')
    click.echo('⚠️  PENSEZ À CHANGER LE MOT DE PASSE APRÈS LA PREMIÈRE CONNEXION!')
    click.echo('='*50)

@app.cli.command()
def check_alerts():
    """Vérifie et génère les alertes de stock"""
    from app.utils import generate_stock_alerts
    alerts = generate_stock_alerts()
    click.echo(f'{alerts} alertes générées.')

@app.cli.command()
@click.option('--email', prompt=True, help='Email de l\'administrateur')
@click.password_option(help='Mot de passe de l\'administrateur')
def create_admin(email, password):
    """Créer un nouvel administrateur"""
    from app.models import User, Role
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter(
        (User.email == email) | (User.username == email.split('@')[0])
    ).first()
    
    if existing_user:
        click.echo(f'Un utilisateur avec cet email existe déjà: {existing_user.username}')
        return
    
    # Récupérer le rôle admin
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        click.echo('Le rôle admin n\'existe pas. Exécutez d\'abord "flask init-db".')
        return
    
    # Créer l'utilisateur
    username = email.split('@')[0]
    user = User(
        username=username,
        email=email,
        first_name='Admin',
        last_name='Utilisateur',
        role=admin_role
    )
    user.password = password
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'Administrateur créé avec succès: {username}')

@app.cli.command()
def backup_database():
    """Sauvegarder la base de données"""
    import subprocess
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup_gmao_{timestamp}.sql'
    
    # Cette commande dépend de votre configuration de base de données
    # Adaptez-la à votre SGBD (MySQL, PostgreSQL, SQLite)
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    
    if db_url.startswith('sqlite:///'):
        # Pour SQLite, copier le fichier
        import shutil
        db_path = db_url.replace('sqlite:///', '')
        shutil.copy2(db_path, backup_file)
        click.echo(f'Sauvegarde SQLite créée: {backup_file}')
    
    elif db_url.startswith('mysql://'):
        # Pour MySQL, utiliser mysqldump
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        cmd = [
            'mysqldump',
            f'--host={parsed.hostname}',
            f'--port={parsed.port or 3306}',
            f'--user={parsed.username}',
            f'--password={parsed.password}',
            parsed.path[1:],  # Retirer le / initial
            '--result-file', backup_file
        ]
        
        try:
            subprocess.run(cmd, check=True)
            click.echo(f'Sauvegarde MySQL créée: {backup_file}')
        except subprocess.CalledProcessError as e:
            click.echo(f'Erreur lors de la sauvegarde: {e}')
    
    else:
        click.echo(f'Type de base de données non supporté pour la sauvegarde automatique: {db_url}')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)