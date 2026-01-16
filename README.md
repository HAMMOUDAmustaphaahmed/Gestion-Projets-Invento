# Invento - Système de Gestion de Maintenance Assistée par Ordinateur (GMAO)

## 📋 Description

Invento est une application web complète de Gestion de Maintenance Assistée par Ordinateur (GMAO) développée avec Flask. Cette solution permet aux entreprises de gérer efficacement leurs activités de maintenance, leur stock, leurs projets et leur personnel via une interface intuitive et moderne.

## ✨ Fonctionnalités Principales

### 🔐 Authentification & Sécurité
- Système d'authentification multi-utilisateurs
- Rôles et permissions (Admin, Gestionnaire, Technicien, Consultant)
- Gestion de sessions sécurisée
- Protection CSRF intégrée

### 📦 Gestion du Stock
- Suivi des articles en stock avec références uniques
- Gestion des quantités minimales et alertes automatiques
- Catégories et attributs personnalisables
- Suivi des fournisseurs et prix unitaires
- Mouvements de stock (entrées/sorties/transferts)

### 👥 Gestion du Personnel
- Fiches employés avec informations complètes
- Groupes de travail et équipes
- Assignation du personnel aux tâches
- Gestion des compétences et disponibilités

### 🏗️ Gestion de Projets
- Création et suivi de projets clients
- Tâches avec dates, priorités et statuts
- Association de matériaux aux tâches
- Calcul des coûts et budgets
- Suivi de la progression

### 📊 Tableau de Bord
- Vue d'ensemble en temps réel
- Graphiques et statistiques configurables
- Alertes de stock et notifications
- Indicateurs de performance clés

### 📅 Calendrier
- Vue calendrier des tâches et projets
- Planification des interventions
- Gestion des disponibilités

## 🛠️ Stack Technologique

### Backend
- **Framework** : Flask 2.x
- **Base de données** : SQLite (développement) / PostgreSQL/MySQL (production)
- **ORM** : SQLAlchemy avec Flask-Migrate
- **Authentification** : Flask-Login, Flask-WTF
- **Sécurité** : CSRF protection, hachage de mots de passe

### Frontend
- **Templates** : Jinja2
- **Styling** : CSS personnalisé
- **JavaScript** : Vanilla JS + Chart.js pour les graphiques
- **Responsive Design** : Compatible mobile et desktop

## 🚀 Installation et Configuration

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git (pour cloner le dépôt)

### Étapes d'installation

1. **Cloner le dépôt**
```bash
git clone <repository-url>
cd invento
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. **Initialiser la base de données**
```bash
# En mode développement
flask init-db

# En production (avec PostgreSQL)
# Modifier DATABASE_URL dans .env puis:
flask db upgrade
```

6. **Lancer l'application**
```bash
# Mode développement
flask run --host=0.0.0.0 --port=5000

# Ou exécuter directement
python app.py
```

## 👥 Guide d'Utilisation

### Premier Accès
1. Accédez à l'application via `http://localhost:5000`
2. Connectez-vous avec les identifiants par défaut:
   - **Nom d'utilisateur** : `admin`
   - **Mot de passe** : `Admin123!`
3. **Important** : Changez le mot de passe après la première connexion

### Rôles et Permissions

#### 👑 Administrateur
- Accès complet à toutes les fonctionnalités
- Gestion des utilisateurs et rôles
- Configuration système
- Export de données

#### 📋 Gestionnaire
- Gestion du stock, projets, tâches et personnel
- Pas de suppression de données
- Génération de rapports

#### 🔧 Technicien
- Visualisation des tâches assignées
- Mise à jour du statut des tâches
- Consultation du stock

#### 👁️ Consultant
- Lecture seule de toutes les données
- Accès aux tableaux de bord
- Pas de modifications autorisées

### 📦 Gestion du Stock

#### Ajouter un article
1. Naviguez vers **Stock > Nouvel article**
2. Remplissez les informations:
   - Référence (unique)
   - Libellé
   - Catégorie
   - Quantité et quantité minimale
   - Prix unitaire
   - Fournisseur
3. Ajoutez des attributs personnalisés si nécessaire

#### Alertes de stock
- Les alertes sont générées automatiquement
- Notification dans le tableau de bord
- Email d'alerte (si configuré)

### 🏗️ Gestion de Projets

#### Créer un projet
1. **Projets > Nouveau projet**
2. Sélectionnez un client
3. Définissez les dates et le budget
4. Ajoutez des tâches associées

#### Gestion des tâches
1. Dans un projet, cliquez sur "Ajouter une tâche"
2. Assignez du personnel ou des groupes
3. Associez des matériaux du stock
4. Suivez la progression via le tableau de bord

### 📊 Tableau de Bord Personnalisé

#### Ajouter un graphique
1. Dans le tableau de bord, cliquez sur "Personnaliser"
2. Choisissez le type de graphique
3. Sélectionnez la source de données
4. Configurez les filtres

#### Widgets disponibles
- Stock par catégorie
- Projets par statut
- Tâches en cours
- Alertes de stock
- Coûts par projet

## 🔧 Commandes CLI Utiles

```bash
# Initialiser la base de données (développement)
flask init-db

# Créer un nouvel administrateur
flask create-admin --email admin@votreentreprise.com

# Vérifier les alertes de stock
flask check-alerts

# Sauvegarder la base de données
flask backup-database

# Migrations de base de données
flask db migrate -m "Description des changements"
flask db upgrade
```

## 🧪 Tests

```bash
# Exécuter les tests unitaires
pytest

# Tests avec couverture
pytest --cov=app tests/

# Tests spécifiques
pytest tests/test_stock.py -v
```

## 📁 Structure du Projet

```
Invento/
├── app.py                    # Point d'entrée principal
├── config.py                # Configuration de l'application
├── requirements.txt         # Dépendances Python
├── .env                     # Variables d'environnement
├── .gitignore              # Fichiers ignorés par Git
│
├── instance/               # Données d'instance
│   └── gmao.db            # Base de données SQLite
│
├── migrations/             # Migrations de base de données
│
├── static/                 # Fichiers statiques
│   ├── css/               # Feuilles de style
│   ├── js/                # JavaScript
│   ├── img/               # Images
│   └── uploads/           # Fichiers uploadés
│       ├── stock/         # Fichiers stock
│       └── projects/      # Fichiers projets
│
├── templates/             # Templates Jinja2
│   ├── base.html         # Template de base
│   ├── index.html        # Page d'accueil
│   ├── auth/             # Authentification
│   ├── admin/            # Administration
│   ├── stock/            # Gestion du stock
│   ├── clients/          # Gestion clients
│   ├── personnel/        # Gestion personnel
│   ├── projects/         # Gestion projets
│   ├── dashboard/        # Tableau de bord
│   ├── calendar/         # Calendrier
│   └── errors/           # Pages d'erreur
│
└── app/                  # Package principal
    ├── __init__.py      # Factory d'application
    ├── models.py        # Modèles de données
    ├── forms.py         # Formulaires
    ├── routes.py        # Routes principales
    ├── utils.py         # Utilitaires
    ├── decorators.py    # Décorateurs
    │
    ├── auth/            # Authentification
    ├── admin/           # Administration
    ├── clients/         # Clients
    ├── stock/           # Stock
    ├── personnel/       # Personnel
    ├── projects/        # Projets
    ├── dashboard/       # Tableau de bord
    └── calendar/        # Calendrier
```

## ⚙️ Configuration Avancée

### Variables d'Environnement

```env
# Application
FLASK_CONFIG=development
SECRET_KEY=votre_clé_secrète_ici

# Base de données
DATABASE_URL=sqlite:///instance/gmao.db
# Pour PostgreSQL: postgresql://user:password@localhost/dbname

# Email (optionnel)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe
```

### Déploiement en Production

1. **Utiliser une base de données robuste**
   ```bash
   # PostgreSQL recommandé
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **Configurer Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **Configurer Nginx**
   ```nginx
   server {
       listen 80;
       server_name votre-domaine.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static {
           alias /chemin/vers/invento/static;
       }
   }
   ```

4. **Sécuriser avec SSL**
   ```bash
   # Utiliser Let's Encrypt
   sudo certbot --nginx -d votre-domaine.com
   ```

## 🚨 Dépannage

### Problèmes Courants

**Base de données non trouvée**
```bash
# Solution:
flask init-db
flask db upgrade
```

**Erreur CSRF**
- Vérifier que `WTF_CSRF_ENABLED = True` en production
- Ajouter le token CSRF dans les formulaires

**Upload de fichiers échoue**
- Vérifier les permissions du dossier `uploads/`
- Vérifier la taille maximale dans `config.py`

**Email non envoyé**
- Vérifier les paramètres SMTP dans `.env`
- Tester la connexion SMTP avec un script séparé

## 📈 Maintenance

### Sauvegarde
```bash
# Sauvegarde manuelle
flask backup-database

# Sauvegarde automatique (crontab)
0 2 * * * cd /chemin/vers/invento && flask backup-database
```

### Nettoyage
- Supprimer les fichiers temporaires
- Archiver les anciens projets
- Nettoyer le cache des uploads

### Mise à jour
1. Sauvegarder la base de données
2. Mettre à jour le code
3. Exécuter les migrations
4. Tester les fonctionnalités principales

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit vos changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- Flask et sa communauté
- Tous les contributeurs open-source
- Les testeurs et utilisateurs d'Invento

## 📞 Support

Pour le support technique :
- 📧 Email : support@votreentreprise.com
- 🐛 Issues : [GitHub Issues](lien-vers-issues)
- 📖 Documentation : [Wiki du projet](lien-vers-wiki)

---

**Invento** - Simplifiez votre gestion de maintenance depuis 2024