from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from app.equipments import bp
from app.equipments.forms import (
    EquipmentForm, EquipmentCategoryForm, EquipmentFileForm, 
    EquipmentMaintenanceForm, EquipmentStockAssociationForm
)
from app.models import (
    Equipment, EquipmentCategory, EquipmentFile, EquipmentMaintenance,
    StockItem, Supplier, equipment_stock_items
)
from app import db
from app.decorators import permission_required
from app.utils import save_uploaded_file, delete_uploaded_file, sanitize_input
import os
from datetime import datetime
from sqlalchemy import or_

@bp.route('/')
@login_required
@permission_required('equipments', 'read')
def index():
    """Liste des équipements"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', 0, type=int)
    status = request.args.get('status', '')
    
    # Construire la requête avec filtres
    query = Equipment.query
    
    if search:
        query = query.filter(
            or_(
                Equipment.reference.ilike(f'%{search}%'),
                Equipment.name.ilike(f'%{search}%'),
                Equipment.serial_number.ilike(f'%{search}%'),
                Equipment.model.ilike(f'%{search}%')
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Pagination
    equipments = query.order_by(Equipment.reference).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    # Données pour les filtres
    categories = EquipmentCategory.query.all()
    
    # Statistiques
    total_equipments = Equipment.query.count()
    available_equipments = Equipment.query.filter_by(status='available').count()
    maintenance_equipments = Equipment.query.filter_by(status='maintenance').count()
    
    return render_template('equipments/index.html',
                         title='Gestion des Équipements',
                         equipments=equipments,
                         categories=categories,
                         search=search,
                         selected_category=category_id,
                         selected_status=status,
                         total_equipments=total_equipments,
                         available_equipments=available_equipments,
                         maintenance_equipments=maintenance_equipments)

@bp.route('/view/<int:equipment_id>')
@login_required
@permission_required('equipments', 'read')
def view(equipment_id):
    """Voir les détails d'un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Récupérer les éléments de stock associés avec leurs quantités
    stock_items = db.session.query(
        StockItem,
        equipment_stock_items.c.quantity_used,
        equipment_stock_items.c.notes,
        equipment_stock_items.c.added_at
    ).join(
        equipment_stock_items,
        StockItem.id == equipment_stock_items.c.stock_item_id
    ).filter(
        equipment_stock_items.c.equipment_id == equipment_id
    ).all()
    
    # Calculer la valeur totale
    total_value = equipment.get_total_value()
    
    # Récupérer les maintenances triées
    maintenances = equipment.maintenance_logs.order_by(EquipmentMaintenance.maintenance_date.desc()).all()
    
    # Ajouter la date du jour pour les comparaisons
    today = datetime.now().date()
    
    return render_template('equipments/view.html',
                         title=f'Équipement - {equipment.reference}',
                         equipment=equipment,
                         stock_items=stock_items,
                         maintenances=maintenances,  # ← Ajouter cette ligne
                         total_value=total_value,
                         today=today)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'create')
def add():
    """Ajouter un nouvel équipement"""
    form = EquipmentForm()
    
    # Remplir les choix dynamiques
    form.category_id.choices = [(0, '-- Sélectionner --')] + [(c.id, c.name) for c in EquipmentCategory.query.all()]
    form.supplier_id.choices = [(0, '-- Sélectionner --')] + [(s.id, s.name) for s in Supplier.query.all()]
    form.stock_items.choices = [(s.id, f"{s.reference} - {s.libelle}") for s in StockItem.query.all()]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        reference = sanitize_input(form.reference.data)
        name = sanitize_input(form.name.data)
        
        # Vérifier l'unicité de la référence
        existing = Equipment.query.filter_by(reference=reference).first()
        if existing:
            flash('Cette référence existe déjà.', 'danger')
            return redirect(url_for('equipments.add'))
        
        # Vérifier l'unicité du numéro de série
        if form.serial_number.data:
            existing_serial = Equipment.query.filter_by(serial_number=form.serial_number.data).first()
            if existing_serial:
                flash('Ce numéro de série existe déjà.', 'danger')
                return redirect(url_for('equipments.add'))
        
        # Créer l'équipement
        equipment = Equipment(
            reference=reference,
            name=name,
            description=sanitize_input(form.description.data) if form.description.data else None,
            serial_number=sanitize_input(form.serial_number.data) if form.serial_number.data else None,
            model=sanitize_input(form.model.data) if form.model.data else None,
            brand=sanitize_input(form.brand.data) if form.brand.data else None,
            status=form.status.data,
            location=sanitize_input(form.location.data) if form.location.data else None,
            department=sanitize_input(form.department.data) if form.department.data else None,
            responsible_person=sanitize_input(form.responsible_person.data) if form.responsible_person.data else None,
            purchase_date=form.purchase_date.data,
            warranty_until=form.warranty_until.data,
            last_maintenance=form.last_maintenance.data,
            next_maintenance=form.next_maintenance.data,
            purchase_price=form.purchase_price.data,
            current_value=form.current_value.data,
            notes=sanitize_input(form.notes.data) if form.notes.data else None
        )
        
        if form.category_id.data and form.category_id.data > 0:
            equipment.category_id = form.category_id.data
        
        if form.supplier_id.data and form.supplier_id.data > 0:
            equipment.supplier_id = form.supplier_id.data
        
        db.session.add(equipment)
        db.session.commit()
        
        # Ajouter les éléments de stock associés
        if form.stock_items.data:
            for stock_item_id in form.stock_items.data:
                # Ajouter l'association avec quantité par défaut 1
                db.session.execute(
                    equipment_stock_items.insert().values(
                        equipment_id=equipment.id,
                        stock_item_id=stock_item_id,
                        quantity_used=1.0
                    )
                )
        
        db.session.commit()
        
        flash(f'Équipement {reference} ajouté avec succès!', 'success')
        return redirect(url_for('equipments.view', equipment_id=equipment.id))
    
    return render_template('equipments/add.html',
                         title='Ajouter un équipement',
                         form=form)

@bp.route('/edit/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'update')
def edit(equipment_id):
    """Modifier un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    form = EquipmentForm()
    
    # Remplir les choix dynamiques
    form.category_id.choices = [(0, '-- Sélectionner --')] + [(c.id, c.name) for c in EquipmentCategory.query.all()]
    form.supplier_id.choices = [(0, '-- Sélectionner --')] + [(s.id, s.name) for s in Supplier.query.all()]
    
    # Récupérer les éléments de stock actuellement associés
    current_stock_items = [item.id for item in equipment.stock_items]
    form.stock_items.choices = [(s.id, f"{s.reference} - {s.libelle}") for s in StockItem.query.all()]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        equipment.reference = sanitize_input(form.reference.data)
        equipment.name = sanitize_input(form.name.data)
        equipment.description = sanitize_input(form.description.data) if form.description.data else None
        equipment.serial_number = sanitize_input(form.serial_number.data) if form.serial_number.data else None
        equipment.model = sanitize_input(form.model.data) if form.model.data else None
        equipment.brand = sanitize_input(form.brand.data) if form.brand.data else None
        equipment.status = form.status.data
        equipment.location = sanitize_input(form.location.data) if form.location.data else None
        equipment.department = sanitize_input(form.department.data) if form.department.data else None
        equipment.responsible_person = sanitize_input(form.responsible_person.data) if form.responsible_person.data else None
        equipment.purchase_date = form.purchase_date.data
        equipment.warranty_until = form.warranty_until.data
        equipment.last_maintenance = form.last_maintenance.data
        equipment.next_maintenance = form.next_maintenance.data
        equipment.purchase_price = form.purchase_price.data
        equipment.current_value = form.current_value.data
        equipment.notes = sanitize_input(form.notes.data) if form.notes.data else None
        
        if form.category_id.data and form.category_id.data > 0:
            equipment.category_id = form.category_id.data
        else:
            equipment.category_id = None
        
        if form.supplier_id.data and form.supplier_id.data > 0:
            equipment.supplier_id = form.supplier_id.data
        else:
            equipment.supplier_id = None
        
        equipment.updated_at = datetime.utcnow()
        
        # Mettre à jour les éléments de stock associés
        # Supprimer toutes les associations existantes
        db.session.execute(
            equipment_stock_items.delete().where(
                equipment_stock_items.c.equipment_id == equipment.id
            )
        )
        
        # Ajouter les nouvelles associations
        if form.stock_items.data:
            for stock_item_id in form.stock_items.data:
                db.session.execute(
                    equipment_stock_items.insert().values(
                        equipment_id=equipment.id,
                        stock_item_id=stock_item_id,
                        quantity_used=1.0
                    )
                )
        
        db.session.commit()
        
        flash(f'Équipement {equipment.reference} mis à jour avec succès!', 'success')
        return redirect(url_for('equipments.view', equipment_id=equipment.id))
    
    # Pré-remplir le formulaire
    form.reference.data = equipment.reference
    form.name.data = equipment.name
    form.description.data = equipment.description
    form.serial_number.data = equipment.serial_number
    form.model.data = equipment.model
    form.brand.data = equipment.brand
    form.status.data = equipment.status
    form.location.data = equipment.location
    form.department.data = equipment.department
    form.responsible_person.data = equipment.responsible_person
    form.purchase_date.data = equipment.purchase_date
    form.warranty_until.data = equipment.warranty_until
    form.last_maintenance.data = equipment.last_maintenance
    form.next_maintenance.data = equipment.next_maintenance
    form.purchase_price.data = equipment.purchase_price
    form.current_value.data = equipment.current_value
    form.notes.data = equipment.notes
    form.category_id.data = equipment.category_id
    form.supplier_id.data = equipment.supplier_id
    form.stock_items.data = current_stock_items
    
    return render_template('equipments/edit.html',
                         title='Modifier un équipement',
                         form=form, equipment=equipment)

@bp.route('/delete/<int:equipment_id>', methods=['POST'])
@login_required
@permission_required('equipments', 'delete')
def delete(equipment_id):
    """Supprimer un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Vérifier si l'équipement est utilisé dans des interventions
    if equipment.interventions.count() > 0:
        flash('Impossible de supprimer cet équipement car il est utilisé dans des interventions.', 'danger')
        return redirect(url_for('equipments.view', equipment_id=equipment_id))
    
    # Supprimer les fichiers associés
    for file in equipment.files:
        delete_uploaded_file(file.filename, 'equipments')
        db.session.delete(file)
    
    # Supprimer les logs de maintenance
    for maintenance in equipment.maintenance_logs:
        db.session.delete(maintenance)
    
    # Supprimer l'équipement
    db.session.delete(equipment)
    db.session.commit()
    
    flash(f'Équipement {equipment.reference} supprimé avec succès.', 'success')
    return redirect(url_for('equipments.index'))

@bp.route('/<int:equipment_id>/add-stock', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'update')
def add_stock_item(equipment_id):
    """Ajouter un élément de stock à un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    form = EquipmentStockAssociationForm()
    
    # Remplir les choix dynamiques (exclure les éléments déjà associés)
    current_stock_ids = [item.id for item in equipment.stock_items]
    available_stock = StockItem.query.filter(~StockItem.id.in_(current_stock_ids)).all()
    form.stock_item_id.choices = [(s.id, f"{s.reference} - {s.libelle}") for s in available_stock]
    
    if form.validate_on_submit():
        stock_item_id = form.stock_item_id.data
        
        # Vérifier si l'élément n'est pas déjà associé
        existing = db.session.query(equipment_stock_items).filter_by(
            equipment_id=equipment_id,
            stock_item_id=stock_item_id
        ).first()
        
        if existing:
            flash('Cet élément de stock est déjà associé à cet équipement.', 'warning')
        else:
            # Ajouter l'association
            db.session.execute(
                equipment_stock_items.insert().values(
                    equipment_id=equipment_id,
                    stock_item_id=stock_item_id,
                    quantity_used=form.quantity_used.data,
                    notes=sanitize_input(form.notes.data) if form.notes.data else None,
                    added_at=datetime.utcnow()
                )
            )
            db.session.commit()
            
            flash('Élément de stock associé avec succès!', 'success')
        
        return redirect(url_for('equipments.view', equipment_id=equipment_id))
    
    return render_template('equipments/add_stock_item.html',
                         title='Ajouter un élément de stock',
                         form=form,
                         equipment=equipment)

@bp.route('/<int:equipment_id>/stock/<int:stock_item_id>/remove', methods=['POST'])
@login_required
@permission_required('equipments', 'update')
def remove_stock_item(equipment_id, stock_item_id):
    """Retirer un élément de stock d'un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Supprimer l'association
    db.session.execute(
        equipment_stock_items.delete().where(
            (equipment_stock_items.c.equipment_id == equipment_id) &
            (equipment_stock_items.c.stock_item_id == stock_item_id)
        )
    )
    db.session.commit()
    
    flash('Élément de stock retiré avec succès.', 'success')
    return redirect(url_for('equipments.view', equipment_id=equipment_id))

@bp.route('/<int:equipment_id>/update-stock-quantity', methods=['POST'])
@login_required
@permission_required('equipments', 'update')
def update_stock_quantity(equipment_id):
    """Mettre à jour la quantité d'un élément de stock utilisé"""
    equipment = Equipment.query.get_or_404(equipment_id)
    stock_item_id = request.form.get('stock_item_id', type=int)
    quantity = request.form.get('quantity', type=float)
    notes = sanitize_input(request.form.get('notes', ''))
    
    if not stock_item_id or not quantity:
        flash('Données invalides.', 'danger')
        return redirect(url_for('equipments.view', equipment_id=equipment_id))
    
    # Mettre à jour la quantité
    db.session.execute(
        equipment_stock_items.update().where(
            (equipment_stock_items.c.equipment_id == equipment_id) &
            (equipment_stock_items.c.stock_item_id == stock_item_id)
        ).values(
            quantity_used=quantity,
            notes=notes if notes else None
        )
    )
    db.session.commit()
    
    flash('Quantité mise à jour avec succès.', 'success')
    return redirect(url_for('equipments.view', equipment_id=equipment_id))

@bp.route('/<int:equipment_id>/maintenance/add', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'update')
def add_maintenance(equipment_id):
    """Ajouter une maintenance à un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    form = EquipmentMaintenanceForm()
    
    if form.validate_on_submit():
        maintenance = EquipmentMaintenance(
            equipment_id=equipment_id,
            maintenance_type=form.maintenance_type.data,
            maintenance_date=form.maintenance_date.data,
            next_maintenance_date=form.next_maintenance_date.data,
            performed_by=sanitize_input(form.performed_by.data) if form.performed_by.data else None,
            cost=form.cost.data,
            description=sanitize_input(form.description.data),
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            performed_by_user=current_user.id
        )
        
        # Mettre à jour les dates de maintenance de l'équipement
        equipment.last_maintenance = form.maintenance_date.data
        if form.next_maintenance_date.data:
            equipment.next_maintenance = form.next_maintenance_date.data
        
        db.session.add(maintenance)
        db.session.commit()
        
        flash('Maintenance enregistrée avec succès!', 'success')
        return redirect(url_for('equipments.view', equipment_id=equipment_id))
    
    return render_template('equipments/add_maintenance.html',
                         title='Ajouter une maintenance',
                         form=form,
                         equipment=equipment)

@bp.route('/<int:equipment_id>/upload', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'update')
def upload_file(equipment_id):
    """Uploader un fichier pour un équipement"""
    equipment = Equipment.query.get_or_404(equipment_id)
    form = EquipmentFileForm()
    
    if form.validate_on_submit():
        file_info = save_uploaded_file(form.file.data, 'equipments')
        
        if file_info:
            equipment_file = EquipmentFile(
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                file_type=file_info['extension'],
                description=sanitize_input(form.description.data) if form.description.data else None,
                equipment_id=equipment.id,
                uploaded_by=current_user.id
            )
            
            db.session.add(equipment_file)
            db.session.commit()
            
            flash('Fichier uploadé avec succès!', 'success')
        else:
            flash('Erreur lors de l\'upload du fichier.', 'danger')
        
        return redirect(url_for('equipments.view', equipment_id=equipment.id))
    
    return render_template('equipments/upload_file.html',
                         title=f'Uploader un fichier - {equipment.reference}',
                         form=form, equipment=equipment)

@bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
@permission_required('equipments', 'delete')
def delete_file(file_id):
    """Supprimer un fichier d'équipement"""
    equipment_file = EquipmentFile.query.get_or_404(file_id)
    equipment_id = equipment_file.equipment_id
    
    # Supprimer le fichier physique
    delete_uploaded_file(equipment_file.filename, 'equipments')
    
    # Supprimer l'entrée de la base de données
    db.session.delete(equipment_file)
    db.session.commit()
    
    flash('Fichier supprimé avec succès.', 'success')
    return redirect(url_for('equipments.view', equipment_id=equipment_id))

@bp.route('/file/<int:file_id>/download')
@login_required
@permission_required('equipments', 'read')
def download_file(file_id):
    """Télécharger un fichier d'équipement"""
    equipment_file = EquipmentFile.query.get_or_404(file_id)
    
    return send_from_directory(
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'equipments'),
        equipment_file.filename,
        as_attachment=True,
        download_name=equipment_file.original_filename
    )

@bp.route('/categories')
@login_required
@permission_required('equipments', 'read')
def categories():
    """Liste des catégories d'équipements"""
    categories = EquipmentCategory.query.all()
    return render_template('equipments/categories.html',
                         title='Catégories d\'équipements',
                         categories=categories)

@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'create')
def add_category():
    """Ajouter une catégorie d'équipements"""
    form = EquipmentCategoryForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        category = EquipmentCategory(
            name=sanitize_input(form.name.data),
            description=sanitize_input(form.description.data) if form.description.data else None
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Catégorie {category.name} ajoutée avec succès!', 'success')
        return redirect(url_for('equipments.categories'))
    
    return render_template('equipments/category_form.html',
                         title='Ajouter une catégorie',
                         form=form)

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('equipments', 'update')
def edit_category(category_id):
    """Modifier une catégorie d'équipements"""
    category = EquipmentCategory.query.get_or_404(category_id)
    form = EquipmentCategoryForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        category.name = sanitize_input(form.name.data)
        category.description = sanitize_input(form.description.data) if form.description.data else None
        
        db.session.commit()
        
        flash(f'Catégorie {category.name} mise à jour avec succès!', 'success')
        return redirect(url_for('equipments.categories'))
    
    # Pré-remplir le formulaire
    form.name.data = category.name
    form.description.data = category.description
    
    return render_template('equipments/category_form.html',
                         title='Modifier une catégorie',
                         form=form, category=category)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@permission_required('equipments', 'delete')
def delete_category(category_id):
    """Supprimer une catégorie d'équipements"""
    category = EquipmentCategory.query.get_or_404(category_id)
    
    # Vérifier si la catégorie est utilisée
    if category.equipments.count() > 0:
        flash('Impossible de supprimer cette catégorie car elle est utilisée par des équipements.', 'danger')
        return redirect(url_for('equipments.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Catégorie {category.name} supprimée avec succès.', 'success')
    return redirect(url_for('equipments.categories'))

@bp.route('/api/search-stock')
@login_required
def search_stock():
    """API pour rechercher des éléments de stock (AJAX)"""
    search_term = request.args.get('q', '')
    exclude_ids = request.args.getlist('exclude[]', type=int)
    
    query = StockItem.query
    
    if search_term:
        query = query.filter(
            or_(
                StockItem.reference.ilike(f'%{search_term}%'),
                StockItem.libelle.ilike(f'%{search_term}%')
            )
        )
    
    if exclude_ids:
        query = query.filter(~StockItem.id.in_(exclude_ids))
    
    items = query.limit(20).all()
    
    results = []
    for item in items:
        results.append({
            'id': item.id,
            'reference': item.reference,
            'libelle': item.libelle,
            'quantity': item.quantity,
            'price': item.price,
            'category': item.category.name if item.category else None
        })
    
    return jsonify(results)

@bp.route('/api/equipment-stats')
@login_required
def equipment_stats():
    """API pour les statistiques des équipements"""
    stats = {
        'total': Equipment.query.count(),
        'available': Equipment.query.filter_by(status='available').count(),
        'in_use': Equipment.query.filter_by(status='in_use').count(),
        'maintenance': Equipment.query.filter_by(status='maintenance').count(),
        'out_of_service': Equipment.query.filter_by(status='out_of_service').count(),
        'total_value': sum(e.get_total_value() for e in Equipment.query.all())
    }
    
    return jsonify(stats)

@bp.route('/api/status-distribution')
@login_required
def status_distribution():
    """API pour la distribution par statut (pour graphiques)"""
    from sqlalchemy import func
    
    status_counts = db.session.query(
        Equipment.status,
        func.count(Equipment.id).label('count')
    ).group_by(Equipment.status).all()
    
    status_labels = {
        'available': 'Disponible',
        'in_use': 'En utilisation',
        'maintenance': 'En maintenance',
        'out_of_service': 'Hors service',
        'reserved': 'Réservé',
        'disposed': 'Mis au rebut'
    }
    
    data = {
        'labels': [status_labels.get(s[0], s[0]) for s in status_counts],
        'datasets': [{
            'label': 'Nombre d\'équipements',
            'data': [s[1] for s in status_counts],
            'backgroundColor': [
                '#28a745',  # Disponible - vert
                '#007bff',  # En utilisation - bleu
                '#ffc107',  # En maintenance - jaune
                '#dc3545',  # Hors service - rouge
                '#17a2b8',  # Réservé - cyan
                '#6c757d'   # Mis au rebut - gris
            ]
        }]
    }
    
    return jsonify(data)

@bp.route('/api/equipment-maintenance/<int:maintenance_id>')
@login_required
def get_maintenance_details(maintenance_id):
    """API pour obtenir les détails d'une maintenance"""
    maintenance = EquipmentMaintenance.query.get_or_404(maintenance_id)
    
    # Labels pour les types de maintenance
    type_labels = {
        'preventive': 'Maintenance préventive',
        'corrective': 'Maintenance corrective',
        'calibration': 'Étalonnage',
        'inspection': 'Inspection',
        'repair': 'Réparation'
    }
    
    # Classes CSS pour les badges
    type_classes = {
        'preventive': 'bg-info',
        'corrective': 'bg-warning',
        'calibration': 'bg-success',
        'inspection': 'bg-primary',
        'repair': 'bg-danger'
    }
    
    return jsonify({
        'maintenance_date': maintenance.maintenance_date.strftime('%d/%m/%Y'),
        'maintenance_type': type_labels.get(maintenance.maintenance_type, maintenance.maintenance_type),
        'type_class': type_classes.get(maintenance.maintenance_type, 'bg-secondary'),
        'performed_by': maintenance.performed_by or 'Non spécifié',
        'cost': format_currency(maintenance.cost) if maintenance.cost else 'Non spécifié',
        'next_maintenance_date': maintenance.next_maintenance_date.strftime('%d/%m/%Y') if maintenance.next_maintenance_date else None,
        'description': maintenance.description,
        'notes': maintenance.notes
    })