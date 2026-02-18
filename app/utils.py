import os
import uuid
from datetime import datetime, date
from functools import wraps
from flask import current_app, request, flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
import json
from PIL import Image
import io

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Remplacer ces lignes dans utils.py (environ lignes 175-195)
def selectattr_filter(sequence, attribute, test='equalto', value=True):
    """Filtre Jinja pour sélectionner des éléments par attribut"""
    if test == 'equalto':
        return [item for item in sequence if getattr(item, attribute, None) == value]
    elif test == 'true':
        return [item for item in sequence if bool(getattr(item, attribute, False))]
    elif test == 'false':
        return [item for item in sequence if not bool(getattr(item, attribute, True))]
    return sequence

import builtins

def sum_filter(sequence, attribute=None):
    """Calcule la somme d'un attribut sur une séquence"""
    try:
        if attribute:
            return builtins.sum(
                float(getattr(item, attribute, 0)) 
                for item in sequence 
                if getattr(item, attribute, 0) is not None
            )
        else:
            return builtins.sum(
                float(item) for item in sequence if item is not None
            )
    except:
        return 0

def save_uploaded_file(file, subfolder='', optimize_images=True):
    """
    Sauvegarde un fichier uploadé de manière optimisée
    
    Args:
        file: Fichier uploadé depuis request.files
        subfolder: Sous-dossier dans le dossier d'uploads
        optimize_images: Optimiser les images (compression)
    
    Returns:
        dict: Informations du fichier ou None en cas d'erreur
    """
    if file and allowed_file(file.filename):
        # Générer un nom de fichier unique
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        
        # Créer le chemin complet
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        
        # Optimiser les images pour réduire la taille
        if optimize_images and extension in ['jpg', 'jpeg', 'png']:
            try:
                # Lire l'image
                img = Image.open(file.stream)
                
                # Conserver le mode de couleur original
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Pour les images avec transparence
                    if extension in ['jpg', 'jpeg']:
                        # Convertir en RGB pour JPEG (pas de transparence)
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    else:
                        # Garder RGBA pour PNG
                        img = img.convert('RGBA')
                else:
                    # Convertir en RGB pour les autres modes
                    img = img.convert('RGB')
                
                # Redimensionner si trop grand (max 2000px)
                max_dimension = 2000
                if max(img.size) > max_dimension:
                    ratio = max_dimension / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Sauvegarder avec compression
                if extension in ['jpg', 'jpeg']:
                    img.save(filepath, 'JPEG', quality=85, optimize=True)
                elif extension == 'png':
                    img.save(filepath, 'PNG', optimize=True, compress_level=6)
                else:
                    img.save(filepath)
                
            except Exception as e:
                # Si l'optimisation échoue, sauvegarder normalement
                print(f"Erreur lors de l'optimisation de l'image: {e}")
                file.seek(0)  # Revenir au début du fichier
                file.save(filepath)
        else:
            # Sauvegarder directement pour les non-images
            file.save(filepath)
        
        # Obtenir la taille du fichier
        file_size = os.path.getsize(filepath)
        
        return {
            'filename': unique_filename,
            'original_filename': original_filename,
            'extension': extension,
            'size': file_size
        }
    
    return None

def delete_uploaded_file(filename, subfolder=''):
    """Supprime un fichier uploadé"""
    if filename:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier: {e}")
                return False
    return False


def get_file_size_mb(filepath):
    """Retourne la taille d'un fichier en MB"""
    if os.path.exists(filepath):
        size_bytes = os.path.getsize(filepath)
        return round(size_bytes / (1024 * 1024), 2)
    return 0

def compress_pdf(input_path, output_path, quality=85):
    """
    Compresse un PDF (nécessite ghostscript installé)
    Cette fonction est optionnelle et nécessite des dépendances supplémentaires
    """
    try:
        import subprocess
        
        gs_command = [
            'gs',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS=/ebook',  # /screen, /ebook, /printer, /prepress
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        subprocess.run(gs_command, check=True)
        return True
    except Exception as e:
        print(f"Erreur lors de la compression du PDF: {e}")
        return False

def format_date(value, format='%d/%m/%Y'):
    """Formate une date pour l'affichage"""
    if value is None:
        return ''
    
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    
    return value.strftime(format)

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Formate un datetime pour l'affichage"""
    if value is None:
        return ''
    return value.strftime(format)

def format_currency(value, currency='€'):
    """Formate un montant monétaire"""
    if value is None:
        return f'0.00 {currency}'
    
    try:
        value = float(value)
        return f"{value:,.2f} {currency}".replace(',', ' ').replace('.', ',')
    except (ValueError, TypeError):
        return f'0.00 {currency}'

def get_notifications_count():
    """Retourne le nombre de notifications non lues pour l'utilisateur courant"""
    from app.models import Notification
    if current_user.is_authenticated:
        return Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return 0

def generate_stock_alerts():
    """Génère des alertes pour le stock bas"""
    from app.models import StockItem, Notification, User
    from app import db
    
    alert_items = StockItem.query.filter(
        StockItem.quantity <= StockItem.min_quantity,
        StockItem.min_quantity > 0
    ).all()
    
    # Trouver les administrateurs
    admins = User.query.join(User.role).filter_by(name='admin').all()
    
    alerts_created = 0
    for item in alert_items:
        for admin in admins:
            # Vérifier si une notification existe déjà
            existing = Notification.query.filter_by(
                user_id=admin.id,
                stock_item_id=item.id,
                is_read=False
            ).first()
            
            if not existing:
                notification = Notification(
                    user_id=admin.id,
                    stock_item_id=item.id,
                    title='Alerte Stock Bas',
                    message=f'La quantité de {item.libelle} ({item.reference}) est basse: {item.quantity}/{item.min_quantity}',
                    notification_type='stock_alert'
                )
                db.session.add(notification)
                alerts_created += 1
    
    if alerts_created > 0:
        db.session.commit()
    
    return alerts_created

def check_stock_availability(task_items):
    """
    Vérifie la disponibilité des items de stock pour une tâche
    
    Args:
        task_items: Liste de TaskStockItem
    
    Returns:
        dict: Résultats de la vérification
    """
    availability = {
        'all_available': True,
        'items': []
    }
    
    for task_item in task_items:
        if task_item.stock_item:
            available = task_item.stock_item.quantity
            required = task_item.estimated_quantity
            is_available = available >= required
            
            availability['items'].append({
                'item': task_item.stock_item,
                'required': required,
                'available': available,
                'is_available': is_available
            })
            
            if not is_available:
                availability['all_available'] = False
    
    return availability

def create_dashboard_chart_config(chart_type, data_source, filters=None, options=None):
    """
    Crée une configuration de graphique pour le dashboard
    
    Args:
        chart_type: Type de graphique (bar, line, pie, etc.)
        data_source: Source de données (stock, projects, tasks)
        filters: Filtres à appliquer
        options: Options supplémentaires
    
    Returns:
        dict: Configuration du graphique
    """
    config = {
        'type': chart_type,
        'data': {
            'labels': [],
            'datasets': [{
                'label': '',
                'data': [],
                'backgroundColor': [],
                'borderColor': [],
                'borderWidth': 1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'top',
                },
                'title': {
                    'display': True,
                    'text': ''
                }
            }
        }
    }
    
    # Appliquer les options personnalisées
    if options:
        config['options'].update(options)
    
    return config

def sanitize_input(data):
    """
    Nettoie les données d'entrée pour prévenir les attaques XSS
    
    Args:
        data: Données à nettoyer (str, dict, list)
    
    Returns:
        Données nettoyées
    """
    if isinstance(data, str):
        # Échapper les caractères HTML dangereux
        import html
        return html.escape(data.strip())
    
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data

def validate_date_range(start_date, end_date):
    """Valide qu'une plage de dates est correcte"""
    if not start_date or not end_date:
        return False, "Les dates de début et de fin sont requises"
    
    if start_date > end_date:
        return False, "La date de début doit être antérieure à la date de fin"
    
    return True, ""

def selectattr(sequence, attribute, test='equalto', value=True):
    """Filtre Jinja pour sélectionner des éléments par attribut"""
    if test == 'equalto':
        return [item for item in sequence if getattr(item, attribute, None) == value]
    elif test == 'true':
        return [item for item in sequence if bool(getattr(item, attribute, False))]
    elif test == 'false':
        return [item for item in sequence if not bool(getattr(item, attribute, True))]
    return sequence

def sum(sequence, attribute=None):
    """Calcule la somme d'un attribut sur une séquence"""
    import builtins
    try:
        if attribute:
            return builtins.sum(float(getattr(item, attribute, 0)) for item in sequence if getattr(item, attribute, 0) is not None)
        else:
            return builtins.sum(float(item) for item in sequence if item is not None)
    except:
        return 0

def nl2br(value):
    """Convertit les sauts de ligne en balises <br> pour HTML"""
    if value is None:
        return ''
    return str(value).replace('\n', '<br>')

# Ajouter également cette fonction pour le contexte global
def get_today():
    """Retourne la date d'aujourd'hui"""
    return datetime.now().date()
