#!/usr/bin/env python3
"""
Script pour initialiser la base de données avec tous les modèles et données par défaut
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au chemin
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import (
    Role, User, Supplier, StockCategory, StockItem, Personnel, 
    Group, Project, TaskType, Task, Notification, DashboardChart
)
from datetime import datetime, date

def init_database():
    """Initialise la base de données complètement"""
    
    app = create_app(os.getenv('FLASK_CONFIG') or 'development')
    
    with app.app_context():
        print("\n" + "="*70)
        print("🔄 INITIALISATION DE LA BASE DE DONNÉES")
        print("="*70 + "\n")
        
        # 1. Créer les tables
        print("📊 Création des tables...")
        db.create_all()
        print("✅ Tables créées avec succès\n")
        
        # 2. Créer les rôles
        print("🔐 Création des rôles...")
        create_roles(app)
        
        # 3. Créer l'utilisateur admin
        print("👤 Création de l'utilisateur admin...")
        create_admin_user()
        
        # 4. Créer les catégories de stock
        print("📦 Création des catégories de stock...")
        create_stock_categories()
        
        # 5. Créer les types de tâches
        print("📋 Création des types de tâches...")
        create_task_types()
        
        # 6. Créer des fournisseurs exemple
        print("🏭 Création de fournisseurs exemples...")
        create_sample_suppliers()
        
        # 7. Créer du personnel exemple
        print("👥 Création de personnel exemple...")
        create_sample_personnel()
        
        # 8. Créer un groupe exemple
        print("👫 Création de groupes de personnel...")
        create_sample_groups()
        
        print("\n" + "="*70)
        print("✅ INITIALISATION COMPLÈTE!")
        print("="*70)
        print("\n📝 INFORMATIONS DE CONNEXION:")
        print("-" * 70)
        print("  Username:  admin")
        print("  Password: Admin123!")
        print("  Email:     admin@gmao.com")
        print("-" * 70)
        print("⚠️  N'OUBLIE PAS DE CHANGER LE MOT DE PASSE!")
        print("="*70 + "\n")

def create_roles(app):
    """Crée les rôles par défaut"""
    
    roles_data = [
        {
            'name': 'admin',
            'description': 'Administrateur système avec tous les droits',
            'permissions': {
                'admin': {'all': True},
                'stock': {'read': True, 'create': True, 'update': True, 'delete': True, 'export': True},
                'projects': {'read': True, 'create': True, 'update':  True, 'delete': True, 'export': True},
                'tasks': {'read': True, 'create': True, 'update': True, 'delete':  True, 'export': True},
                'personnel': {'read':  True, 'create': True, 'update': True, 'delete': True, 'export':  True},
                'calendar': {'read': True, 'create':  True, 'update': True, 'export': True},
                'dashboard': {'read': True, 'create': True, 'update': True, 'export':  True},
                'settings': {'all': True}
            }
        },
        {
            'name': 'gestionnaire',
            'description': 'Gestionnaire avec droits étendus',
            'permissions':  {
                'stock': {'read': True, 'create': True, 'update':  True, 'delete': False, 'export': True},
                'projects': {'read': True, 'create': True, 'update': True, 'delete': False, 'export': True},
                'tasks': {'read': True, 'create': True, 'update': True, 'delete': False, 'export': True},
                'personnel':  {'read': True, 'create': True, 'update': True, 'delete': False},
                'calendar': {'read':  True, 'create': True, 'update': True},
                'dashboard': {'read':  True, 'create': True, 'update': True, 'export': True}
            }
        },
        {
            'name': 'technicien',
            'description':  'Technicien avec droits limités',
            'permissions': {
                'stock': {'read': True, 'create': False, 'update': False, 'delete': False},
                'projects': {'read':  True, 'create': False, 'update': False, 'delete': False},
                'tasks': {'read': True, 'create': False, 'update':  True, 'delete': False},
                'personnel': {'read': False, 'create': False, 'update': False, 'delete': False},
                'calendar': {'read': True, 'create': False, 'update': False},
                'dashboard': {'read': True, 'create': False, 'update': False}
            }
        },
        {
            'name': 'consultant',
            'description': 'Consultant en lecture seule',
            'permissions':  {
                'stock': {'read': True, 'create': False, 'update': False, 'delete': False},
                'projects':  {'read': True, 'create': False, 'update': False, 'delete': False},
                'tasks': {'read': True, 'create': False, 'update': False, 'delete': False},
                'personnel':  {'read': False, 'create': False, 'update': False, 'delete': False},
                'calendar': {'read': True, 'create': False, 'update': False},
                'dashboard': {'read': True, 'create': False, 'update': False}
            }
        }
    ]
    
    for role_data in roles_data:
        role = Role. query.filter_by(name=role_data['name']).first()
        if not role: 
            role = Role(
                name=role_data['name'],
                description=role_data['description']
            )
            role.set_permissions(role_data['permissions'])
            db.session.add(role)
            print(f"  ✅ Rôle créé:  {role. name}")
        else:
            print(f"  ℹ️  Rôle existant: {role.name}")
    
    db.session.commit()

def create_admin_user():
    """Crée l'utilisateur administrateur"""
    
    # Vérifier si l'admin existe déjà
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"  ℹ️  Admin existant: {admin.username} ({admin.email})")
        return
    
    # Récupérer le rôle admin
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("  ❌ Le rôle admin n'existe pas!")
        return
    
    # Créer l'utilisateur admin
    admin = User(
        username='admin',
        email='admin@gmao.com',
        first_name='Administrateur',
        last_name='Système',
        role=admin_role,
        is_active=True
    )
    admin.password = 'Admin123!'  # Le setter hash automatiquement
    
    db.session.add(admin)
    db.session.commit()
    print(f"  ✅ Utilisateur admin créé: {admin.username}")

def create_stock_categories():
    """Crée les catégories de stock"""
    
    categories_data = [
        {
            'name': 'Pièces détachées',
            'description':  'Pièces de rechange pour équipements'
        },
        {
            'name': 'Outillage',
            'description':  'Outils manuels et électriques'
        },
        {
            'name': 'Consommables',
            'description':  'Matériaux consommables'
        },
        {
            'name': 'Équipement de sécurité',
            'description':  'Équipements de protection individuelle'
        },
        {
            'name': 'Matériel informatique',
            'description': 'Ordinateurs, périphériques et composants'
        }
    ]
    
    for cat_data in categories_data: 
        category = StockCategory. query.filter_by(name=cat_data['name']).first()
        if not category: 
            category = StockCategory(**cat_data)
            db.session.add(category)
            print(f"  ✅ Catégorie créée:  {category.name}")
        else:
            print(f"  ℹ️  Catégorie existante: {category. name}")
    
    db.session.commit()

def create_task_types():
    """Crée les types de tâches"""
    
    task_types_data = [
        {
            'name': 'Maintenance préventive',
            'description':  'Maintenance planifiée',
            'default_duration': 2
        },
        {
            'name': 'Maintenance corrective',
            'description': 'Réparation suite à panne',
            'default_duration': 4
        },
        {
            'name': 'Installation',
            'description': 'Installation d\'équipement',
            'default_duration':  8
        },
        {
            'name': 'Inspection',
            'description': 'Contrôle et vérification',
            'default_duration': 1
        },
        {
            'name': 'Calibration',
            'description': 'Étalonnage d\'équipement',
            'default_duration': 3
        }
    ]
    
    for type_data in task_types_data:
        task_type = TaskType.query.filter_by(name=type_data['name']).first()
        if not task_type:
            task_type = TaskType(**type_data)
            db.session.add(task_type)
            print(f"  ✅ Type de tâche créé: {task_type.name}")
        else:
            print(f"  ℹ️  Type existant: {task_type.name}")
    
    db.session.commit()

def create_sample_suppliers():
    """Crée quelques fournisseurs exemples"""
    
    suppliers_data = [
        {
            'name': 'Fournitures Industrielles SA',
            'contact_person': 'Jean Dupont',
            'email': 'contact@fournitures-ind.com',
            'phone':  '+33 1 23 45 67 89',
            'city': 'Paris',
            'country': 'France',
            'website': 'www.fournitures-ind.com'
        },
        {
            'name': 'ElectroTech Solutions',
            'contact_person': 'Marie Martin',
            'email': 'ventes@electrotech.fr',
            'phone': '+33 2 34 56 78 90',
            'city': 'Lyon',
            'country': 'France',
            'website': 'www.electrotech.fr'
        }
    ]
    
    for sup_data in suppliers_data: 
        supplier = Supplier.query. filter_by(name=sup_data['name']).first()
        if not supplier:
            supplier = Supplier(**sup_data)
            db.session.add(supplier)
            print(f"  ✅ Fournisseur créé: {supplier. name}")
        else:
            print(f"  ℹ️  Fournisseur existant: {supplier.name}")
    
    db.session. commit()

def create_sample_personnel():
    """Crée du personnel exemple"""
    
    personnel_data = [
        {
            'employee_id': 'EMP001',
            'first_name': 'Mohamed',
            'last_name':  'Ahmed',
            'email': 'm.ahmed@invento.com',
            'phone':  '+33 6 12 34 56 78',
            'department': 'Maintenance',
            'position': 'Technicien Senior',
            'hire_date': date(2020, 1, 15),
            'city': 'Paris',
            'country': 'France'
        },
        {
            'employee_id': 'EMP002',
            'first_name':  'Sophie',
            'last_name':  'Leclerc',
            'email':  's.leclerc@invento. com',
            'phone': '+33 6 23 45 67 89',
            'department': 'Gestion de Stock',
            'position': 'Responsable Stock',
            'hire_date':  date(2019, 6, 1),
            'city': 'Paris',
            'country': 'France'
        },
        {
            'employee_id': 'EMP003',
            'first_name': 'Pierre',
            'last_name':  'Moreau',
            'email': 'p.moreau@invento.com',
            'phone':  '+33 6 34 56 78 90',
            'department': 'Maintenance',
            'position': 'Technicien',
            'hire_date': date(2021, 3, 10),
            'city': 'Lyon',
            'country': 'France'
        }
    ]
    
    for pers_data in personnel_data: 
        personnel = Personnel. query.filter_by(employee_id=pers_data['employee_id']).first()
        if not personnel:
            personnel = Personnel(**pers_data)
            db.session.add(personnel)
            print(f"  ✅ Personnel créé:  {personnel.get_full_name()}")
        else:
            print(f"  ℹ️  Personnel existant: {personnel.get_full_name()}")
    
    db.session.commit()

def create_sample_groups():
    """Crée des groupes de personnel exemple"""
    
    groups_data = [
        {
            'name': 'Équipe Maintenance',
            'description': 'Équipe responsable de la maintenance préventive et corrective'
        },
        {
            'name': 'Équipe Stock',
            'description': 'Équipe de gestion des stocks'
        }
    ]
    
    for group_data in groups_data: 
        group = Group.query. filter_by(name=group_data['name']).first()
        if not group:
            group = Group(**group_data)
            
            # Ajouter du personnel au groupe
            if 'Maintenance' in group. name:
                personnel = Personnel. query.filter_by(department='Maintenance').all()
                group.members.extend(personnel)
            elif 'Stock' in group.name:
                personnel = Personnel.query.filter_by(department='Gestion de Stock').all()
                group. members.extend(personnel)
            
            db.session.add(group)
            print(f"  ✅ Groupe créé: {group.name}")
        else:
            print(f"  ℹ️  Groupe existant: {group. name}")
    
    db.session.commit()

if __name__ == '__main__': 
    try:
        init_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)