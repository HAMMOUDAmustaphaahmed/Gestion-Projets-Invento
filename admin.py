#!/usr/bin/env python3
"""
Script pour créer l'utilisateur Hammouda avec mot de passe Hammouda.123!
Utilise le même hachage scrypt que l'application Flask
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au chemin
sys.path.insert(0, str(Path(__file__).parent))

from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Role

def create_hammouda_user():
    """Crée l'utilisateur Hammouda avec mot de passe Hammouda.123!"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("🔐 CRÉATION UTILISATEUR HAMMOUDA")
        print("=" * 60)
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter(
            (User.username == 'Hammouda') | 
            (User.email == 'hammouda@gmao.com')
        ).first()
        
        if existing_user:
            print(f"⚠️  Utilisateur existe déjà: {existing_user.username}")
            print(f"   Email: {existing_user.email}")
            print(f"   Rôle: {existing_user.role.name if existing_user.role else 'Aucun'}")
            
            # Demander confirmation pour réinitialiser
            response = input("\nVoulez-vous réinitialiser le mot de passe? (o/n): ")
            if response.lower() != 'o':
                print("❌ Opération annulée.")
                return
            
            # Réinitialiser le mot de passe
            new_password = 'Hammouda.123!'
            existing_user.password = new_password
            db.session.commit()
            print(f"✅ Mot de passe réinitialisé pour {existing_user.username}")
            print(f"   Nouveau mot de passe: {new_password}")
            return
        
        # Récupérer le rôle admin (ou créer si nécessaire)
        admin_role = Role.query.filter_by(name='admin').first()
        
        if not admin_role:
            print("⚠️  Rôle 'admin' non trouvé. Création...")
            admin_role = Role(
                name='admin',
                description='Administrateur système avec tous les droits'
            )
            # Permissions par défaut pour admin
            import json
            admin_role.set_permissions({
                "admin": {"all": True},
                "stock": {"read": True, "create": True, "update": True, "delete": True, "export": True},
                "projects": {"read": True, "create": True, "update": True, "delete": True, "export": True},
                "tasks": {"read": True, "create": True, "update": True, "delete": True, "export": True},
                "personnel": {"read": True, "create": True, "update": True, "delete": True, "export": True},
                "calendar": {"read": True, "create": True, "update": True, "export": True},
                "dashboard": {"read": True, "create": True, "update": True, "export": True},
                "settings": {"all": True}
            })
            db.session.add(admin_role)
            db.session.commit()
            print("✅ Rôle 'admin' créé")
        
        # Créer l'utilisateur Hammouda
        username = 'Hammouda'
        email = 'hammouda@gmao.com'
        password = 'Hammouda.123!'
        
        # Générer le hash du mot de passe (méthode scrypt par défaut)
        password_hash = generate_password_hash(password)
        
        print(f"\n📝 Informations de l'utilisateur:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Mot de passe: {password}")
        print(f"\n🔑 Hash généré:")
        print(f"   {password_hash}")
        
        # Créer l'objet User
        new_user = User(
            username=username,
            email=email,
            first_name='Hammouda',
            last_name='Utilisateur',
            role=admin_role,
            is_active=True
        )
        
        # Définir le mot de passe (utilise le setter qui hash automatiquement)
        new_user.password = password
        
        # Sauvegarder en base
        db.session.add(new_user)
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("✅ UTILISATEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"\n📋 Récapitulatif:")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Rôle: {new_user.role.name}")
        print(f"   Mot de passe (clair): {password}")
        print(f"\n🔐 Hash stocké en base:")
        print(f"   {new_user.password_hash}")
        print("\n" + "=" * 60)
        print("⚠️  CONSERVEZ CES INFORMATIONS EN LIEU SÛR!")
        print("=" * 60)

if __name__ == '__main__':
    try:
        create_hammouda_user()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)