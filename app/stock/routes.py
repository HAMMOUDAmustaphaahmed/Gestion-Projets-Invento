from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from app.stock import bp
from app.stock.forms import StockItemForm, SupplierForm, StockCategoryForm, StockFileForm, DynamicAttributeForm
from app.models import StockItem, Supplier, StockCategory, StockAttribute, StockFile, Notification
from app import db
from app.decorators import permission_required
from app.utils import save_uploaded_file, delete_uploaded_file, generate_stock_alerts, sanitize_input
import os
from datetime import datetime
import json




@bp.route('/')
@login_required
@permission_required('stock', 'read')
def index():
    """Liste des éléments du stock"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', 0, type=int)
    supplier_id = request.args.get('supplier', 0, type=int)
    
    # Construire la requête avec filtres
    query = StockItem.query
    
    if search:
        query = query.filter(
            db.or_(
                StockItem.reference.ilike(f'%{search}%'),
                StockItem.libelle.ilike(f'%{search}%')
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    # Pagination
    items = query.order_by(StockItem.reference).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    # Données pour les filtres
    categories = StockCategory.query.all()
    suppliers = Supplier.query.all()
    
    # Vérifier les alertes de stock
    generate_stock_alerts()
    
    # Calculer la valeur totale du stock
    total_stock_value = sum(item.value or 0 for item in StockItem.query.all())
    
    return render_template('stock/index.html',
                         title='Gestion du Stock',
                         items=items,
                         categories=categories,
                         suppliers=suppliers,
                         search=search,
                         selected_category=category_id,
                         selected_supplier=supplier_id,
                         total_stock_value=total_stock_value)

@bp.route('/view/<int:item_id>')
@login_required
@permission_required('stock', 'read')
def view(item_id):
    """Voir les détails d'un élément du stock"""
    item = StockItem.query.get_or_404(item_id)
    return render_template('stock/view.html',
                         title=f'Stock - {item.reference}',
                         item=item)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'create')
def add():
    """Ajouter un nouvel élément au stock"""
    form = StockItemForm()
    
    # Remplir les choix dynamiques
    form.item_type.choices = [(c.id, c.name) for c in StockCategory.query.all()]
    form.supplier_id.choices = [(0, '-- Sélectionner --')] + [(s.id, s.name) for s in Supplier.query.all()]
    form.category_id.choices = [(0, '-- Sélectionner --')] + [(c.id, c.name) for c in StockCategory.query.all()]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        reference = sanitize_input(form.reference.data)
        libelle = sanitize_input(form.libelle.data)
        
        # Vérifier l'unicité de la référence
        existing = StockItem.query.filter_by(reference=reference).first()
        if existing:
            flash('Cette référence existe déjà.', 'danger')
            return redirect(url_for('stock.add'))
        
        # Créer l'élément de stock
        item = StockItem(
            reference=reference,
            libelle=libelle,
            item_type=form.item_type.data,
            quantity=form.quantity.data,
            min_quantity=form.min_quantity.data,
            price=form.price.data,
            location=sanitize_input(form.location.data) if form.location.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None
        )
        
        if form.supplier_id.data and form.supplier_id.data > 0:
            item.supplier_id = form.supplier_id.data
        
        if form.category_id.data and form.category_id.data > 0:
            item.category_id = form.category_id.data
        
        # Calculer la valeur
        item.calculate_value()
        
        db.session.add(item)
        db.session.commit()
        
        flash(f'Élément {reference} ajouté avec succès!', 'success')
        return redirect(url_for('stock.view', item_id=item.id))
    
    return render_template('stock/add.html',
                         title='Ajouter un élément',
                         form=form)

@bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'update')
def edit(item_id):
    """Modifier un élément du stock"""
    item = StockItem.query.get_or_404(item_id)
    form = StockItemForm()
    
    # Remplir les choix dynamiques
    form.item_type.choices = [(c.id, c.name) for c in StockCategory.query.all()]
    form.supplier_id.choices = [(0, '-- Sélectionner --')] + [(s.id, s.name) for s in Supplier.query.all()]
    form.category_id.choices = [(0, '-- Sélectionner --')] + [(c.id, c.name) for c in StockCategory.query.all()]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        item.reference = sanitize_input(form.reference.data)
        item.libelle = sanitize_input(form.libelle.data)
        item.item_type = form.item_type.data
        item.quantity = form.quantity.data
        item.min_quantity = form.min_quantity.data
        item.price = form.price.data
        item.location = sanitize_input(form.location.data) if form.location.data else None
        item.notes = sanitize_input(form.notes.data) if form.notes.data else None
        
        if form.supplier_id.data and form.supplier_id.data > 0:
            item.supplier_id = form.supplier_id.data
        else:
            item.supplier_id = None
        
        if form.category_id.data and form.category_id.data > 0:
            item.category_id = form.category_id.data
        else:
            item.category_id = None
        
        # Recalculer la valeur
        item.calculate_value()
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Élément {item.reference} mis à jour avec succès!', 'success')
        return redirect(url_for('stock.view', item_id=item.id))
    
    # Pré-remplir le formulaire
    form.reference.data = item.reference
    form.libelle.data = item.libelle
    form.item_type.data = item.item_type
    form.quantity.data = item.quantity
    form.min_quantity.data = item.min_quantity
    form.price.data = item.price
    form.location.data = item.location
    form.notes.data = item.notes
    form.supplier_id.data = item.supplier_id
    form.category_id.data = item.category_id
    
    return render_template('stock/edit.html',
                         title='Modifier un élément',
                         form=form, item=item)

@bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
@permission_required('stock', 'delete')
def delete(item_id):
    """Supprimer un élément du stock"""
    item = StockItem.query.get_or_404(item_id)
    
    # Vérifier si l'élément est utilisé dans des tâches
    if item.task_items.count() > 0:
        flash('Impossible de supprimer cet élément car il est utilisé dans des tâches.', 'danger')
        return redirect(url_for('stock.view', item_id=item_id))
    
    # Supprimer les fichiers associés
    for file in item.files:
        delete_uploaded_file(file.filename, 'stock')
        db.session.delete(file)
    
    db.session.delete(item)
    db.session.commit()
    
    flash(f'Élément {item.reference} supprimé avec succès.', 'success')
    return redirect(url_for('stock.index'))

@bp.route('/suppliers')
@login_required
@permission_required('stock', 'read')
def suppliers():
    """Liste des fournisseurs"""
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('stock/suppliers.html',
                         title='Fournisseurs',
                         suppliers=suppliers)

@bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'create')
def add_supplier():
    """Ajouter un fournisseur"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        supplier = Supplier(
            name=sanitize_input(form.name.data),
            contact_person=sanitize_input(form.contact_person.data) if form.contact_person.data else None,
            email=sanitize_input(form.email.data) if form.email.data else None,
            phone=sanitize_input(form.phone.data) if form.phone.data else None,
            address=sanitize_input(form.address.data) if form.address.data else None,
            city=sanitize_input(form.city.data) if form.city.data else None,
            country=sanitize_input(form.country.data) if form.country.data else None,
            website=sanitize_input(form.website.data) if form.website.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash(f'Fournisseur {supplier.name} ajouté avec succès!', 'success')
        return redirect(url_for('stock.suppliers'))
    
    return render_template('stock/supplier_form.html',
                         title='Ajouter un fournisseur',
                         form=form)

@bp.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'update')
def edit_supplier(supplier_id):
    """Modifier un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        supplier.name = sanitize_input(form.name.data)
        supplier.contact_person = sanitize_input(form.contact_person.data) if form.contact_person.data else None
        supplier.email = sanitize_input(form.email.data) if form.email.data else None
        supplier.phone = sanitize_input(form.phone.data) if form.phone.data else None
        supplier.address = sanitize_input(form.address.data) if form.address.data else None
        supplier.city = sanitize_input(form.city.data) if form.city.data else None
        supplier.country = sanitize_input(form.country.data) if form.country.data else None
        supplier.website = sanitize_input(form.website.data) if form.website.data else None
        supplier.notes = sanitize_input(form.notes.data) if form.notes.data else None
        
        db.session.commit()
        
        flash(f'Fournisseur {supplier.name} mis à jour avec succès!', 'success')
        return redirect(url_for('stock.suppliers'))
    
    # Pré-remplir le formulaire
    form.name.data = supplier.name
    form.contact_person.data = supplier.contact_person
    form.email.data = supplier.email
    form.phone.data = supplier.phone
    form.address.data = supplier.address
    form.city.data = supplier.city
    form.country.data = supplier.country
    form.website.data = supplier.website
    form.notes.data = supplier.notes
    
    return render_template('stock/supplier_form.html',
                         title='Modifier un fournisseur',
                         form=form, supplier=supplier)

@bp.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
@permission_required('stock', 'delete')
def delete_supplier(supplier_id):
    """Supprimer un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Vérifier si le fournisseur est utilisé
    if supplier.stock_items.count() > 0:
        flash('Impossible de supprimer ce fournisseur car il est utilisé par des éléments du stock.', 'danger')
        return redirect(url_for('stock.suppliers'))
    
    db.session.delete(supplier)
    db.session.commit()
    
    flash(f'Fournisseur {supplier.name} supprimé avec succès.', 'success')
    return redirect(url_for('stock.suppliers'))


@bp.route('/<int:item_id>/movements')
@login_required
@permission_required('stock', 'read')
def item_movements(item_id):
    """Historique des mouvements d'un élément"""
    item = StockItem.query.get_or_404(item_id)
    
    # Pagination des mouvements
    page = request.args.get('page', 1, type=int)
    movements = StockMovement.query.filter_by(stock_item_id=item_id)\
        .order_by(StockMovement.movement_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('stock/movements.html',
                         title=f'Mouvements - {item.reference}',
                         item=item,
                         movements=movements)


@bp.route('/<int:item_id>/add-movement', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'update')
def add_movement(item_id):
    """Ajouter un mouvement de stock"""
    item = StockItem.query.get_or_404(item_id)
    form = StockMovementForm()
    
    # Remplir les choix dynamiques
    form.supplier_id.choices = [(0, '-- Aucun --')] + [(s.id, s.name) for s in Supplier.query.all()]
    form.task_id.choices = [(0, '-- Aucun --')] + [(t.id, f"{t.name} (Projet: {t.project.name})") 
                                                   for t in Task.query.all()]
    form.project_id.choices = [(0, '-- Aucun --')] + [(p.id, p.name) for p in Project.query.all()]
    
    if form.validate_on_submit():
        movement = StockMovement(
            stock_item_id=item_id,
            movement_type=form.movement_type.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data or item.price,
            total_price=(form.quantity.data * (form.unit_price.data or item.price)),
            reference=sanitize_input(form.reference.data) if form.reference.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            recorded_by=current_user.id,
            movement_date=datetime.utcnow()
        )
        
        if form.supplier_id.data and form.supplier_id.data > 0:
            movement.supplier_id = form.supplier_id.data
        
        if form.task_id.data and form.task_id.data > 0:
            movement.task_id = form.task_id.data
        
        if form.project_id.data and form.project_id.data > 0:
            movement.project_id = form.project_id.data
        
        # Mettre à jour la quantité du stock
        if form.movement_type.data in ['purchase', 'return']:
            item.quantity += form.quantity.data
        elif form.movement_type.data in ['sale', 'waste']:
            if item.quantity >= form.quantity.data:
                item.quantity -= form.quantity.data
            else:
                flash('Quantité insuffisante en stock!', 'danger')
                return redirect(url_for('stock.add_movement', item_id=item_id))
        
        item.calculate_value()
        item.updated_at = datetime.utcnow()
        
        db.session.add(movement)
        db.session.commit()
        
        # Générer une notification si le stock est bas
        if item.check_alert():
            generate_stock_alerts()
        
        flash(f'Mouvement enregistré! Nouvelle quantité: {item.quantity}', 'success')
        return redirect(url_for('stock.view', item_id=item_id))
    
    return render_template('stock/add_movement.html',
                         title=f'Ajouter un mouvement - {item.reference}',
                         form=form,
                         item=item)


@bp.route('/purchase-orders')
@login_required
@permission_required('stock', 'read')
def purchase_orders():
    """Liste des commandes d'achat"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = PurchaseOrder.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(PurchaseOrder.order_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('stock/purchase_orders.html',
                         title='Commandes d\'achat',
                         orders=orders,
                         status=status)


@bp.route('/purchase-orders/add', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'create')
def add_purchase_order():
    """Créer une commande d'achat"""
    form = PurchaseOrderForm()
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.all()]
    
    if form.validate_on_submit():
        order = PurchaseOrder(
            order_number=sanitize_input(form.order_number.data),
            supplier_id=form.supplier_id.data,
            order_date=form.order_date.data,
            delivery_date=form.delivery_date.data,
            status=form.status.data,
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            created_by=current_user.id
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash(f'Commande {order.order_number} créée avec succès!', 'success')
        return redirect(url_for('stock.view_purchase_order', order_id=order.id))
    
    return render_template('stock/add_purchase_order.html',
                         title='Nouvelle commande d\'achat',
                         form=form)


@bp.route('/purchase-orders/<int:order_id>')
@login_required
@permission_required('stock', 'read')
def view_purchase_order(order_id):
    """Voir une commande d'achat"""
    order = PurchaseOrder.query.get_or_404(order_id)
    return render_template('stock/view_purchase_order.html',
                         title=f'Commande {order.order_number}',
                         order=order)


@bp.route('/purchase-orders/<int:order_id>/receive', methods=['POST'])
@login_required
@permission_required('stock', 'update')
def receive_purchase_order(order_id):
    """Réceptionner une commande d'achat"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    for item in order.items:
        if item.quantity_received < item.quantity_ordered:
            # Créer un mouvement de stock pour chaque article
            movement = StockMovement(
                stock_item_id=item.stock_item_id,
                movement_type='purchase',
                quantity=item.quantity_ordered - item.quantity_received,
                unit_price=item.unit_price,
                total_price=item.total_price,
                reference=order.order_number,
                notes=f'Réception commande {order.order_number}',
                recorded_by=current_user.id,
                supplier_id=order.supplier_id
            )
            
            # Mettre à jour le stock
            stock_item = item.stock_item
            stock_item.quantity += (item.quantity_ordered - item.quantity_received)
            stock_item.calculate_value()
            
            # Marquer comme reçu
            item.quantity_received = item.quantity_ordered
            
            db.session.add(movement)
    
    order.status = 'delivered'
    order.delivery_date = datetime.utcnow().date()
    db.session.commit()
    
    flash(f'Commande {order.order_number} marquée comme livrée!', 'success')
    return redirect(url_for('stock.view_purchase_order', order_id=order_id))


@bp.route('/api/quick-movement', methods=['POST'])
@login_required
@permission_required('stock', 'update')
def quick_movement():
    """API pour les mouvements rapides (AJAX)"""
    data = request.get_json()
    
    item = StockItem.query.get(data['item_id'])
    if not item:
        return jsonify({'success': False, 'message': 'Article non trouvé'})
    
    try:
        quantity = float(data['quantity'])
        movement_type = data.get('type', 'purchase')
        
        movement = StockMovement(
            stock_item_id=item.id,
            movement_type=movement_type,
            quantity=quantity,
            unit_price=item.price,
            total_price=quantity * item.price,
            notes=data.get('reason', 'Mouvement rapide'),
            recorded_by=current_user.id
        )
        
        # Mettre à jour le stock
        if movement_type in ['purchase', 'return']:
            item.quantity += quantity
        elif movement_type in ['sale', 'waste']:
            if item.quantity >= quantity:
                item.quantity -= quantity
            else:
                return jsonify({'success': False, 'message': 'Quantité insuffisante'})
        
        item.calculate_value()
        
        db.session.add(movement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_quantity': item.quantity,
            'message': f'Stock mis à jour: {item.quantity}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})



@bp.route('/categories')
@login_required
@permission_required('stock', 'read')
def categories():
    """Liste des catégories de stock"""
    categories = StockCategory.query.all()
    return render_template('stock/categories.html',
                         title='Catégories de stock',
                         categories=categories)

@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'create')
def add_category():
    """Ajouter une catégorie de stock"""
    form = StockCategoryForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        category = StockCategory(
            name=sanitize_input(form.name.data),
            description=sanitize_input(form.description.data) if form.description.data else None
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Catégorie {category.name} ajoutée avec succès!', 'success')
        return redirect(url_for('stock.categories'))
    
    return render_template('stock/category_form.html',
                         title='Ajouter une catégorie',
                         form=form)

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'update')
def edit_category(category_id):
    """Modifier une catégorie de stock"""
    category = StockCategory.query.get_or_404(category_id)
    form = StockCategoryForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        category.name = sanitize_input(form.name.data)
        category.description = sanitize_input(form.description.data) if form.description.data else None
        
        db.session.commit()
        
        flash(f'Catégorie {category.name} mise à jour avec succès!', 'success')
        return redirect(url_for('stock.categories'))
    
    # Pré-remplir le formulaire
    form.name.data = category.name
    form.description.data = category.description
    
    return render_template('stock/category_form.html',
                         title='Modifier une catégorie',
                         form=form, category=category)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@permission_required('stock', 'delete')
def delete_category(category_id):
    """Supprimer une catégorie de stock"""
    category = StockCategory.query.get_or_404(category_id)
    
    # Vérifier si la catégorie est utilisée
    if category.items.count() > 0:
        flash('Impossible de supprimer cette catégorie car elle est utilisée par des éléments du stock.', 'danger')
        return redirect(url_for('stock.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Catégorie {category.name} supprimée avec succès.', 'success')
    return redirect(url_for('stock.categories'))

@bp.route('/<int:item_id>/upload', methods=['GET', 'POST'])
@login_required
@permission_required('stock', 'update')
def upload_file(item_id):
    """Uploader un fichier pour un élément de stock"""
    item = StockItem.query.get_or_404(item_id)
    form = StockFileForm()
    
    if form.validate_on_submit():
        file_info = save_uploaded_file(form.file.data, 'stock')
        
        if file_info:
            stock_file = StockFile(
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                file_type=file_info['extension'],
                description=sanitize_input(form.description.data) if form.description.data else None,
                stock_item_id=item.id
            )
            
            db.session.add(stock_file)
            db.session.commit()
            
            flash('Fichier uploadé avec succès!', 'success')
        else:
            flash('Erreur lors de l\'upload du fichier.', 'danger')
        
        return redirect(url_for('stock.view', item_id=item.id))
    
    return render_template('stock/upload_file.html',
                         title=f'Uploader un fichier - {item.reference}',
                         form=form, item=item)

@bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
@permission_required('stock', 'delete')
def delete_file(file_id):
    """Supprimer un fichier de stock"""
    stock_file = StockFile.query.get_or_404(file_id)
    item_id = stock_file.stock_item_id
    
    # Supprimer le fichier physique
    delete_uploaded_file(stock_file.filename, 'stock')
    
    # Supprimer l'entrée de la base de données
    db.session.delete(stock_file)
    db.session.commit()
    
    flash('Fichier supprimé avec succès.', 'success')
    return redirect(url_for('stock.view', item_id=item_id))

@bp.route('/file/<int:file_id>/download')
@login_required
@permission_required('stock', 'read')
def download_file(file_id):
    """Télécharger un fichier de stock"""
    stock_file = StockFile.query.get_or_404(file_id)
    
    return send_from_directory(
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'stock'),
        stock_file.filename,
        as_attachment=True,
        download_name=stock_file.original_filename
    )

@bp.route('/alerts')
@login_required
@permission_required('stock', 'read')
def alerts():
    """Alertes de stock bas"""
    # Générer les alertes
    generate_stock_alerts()
    
    # Récupérer les éléments avec stock bas
    alert_items = StockItem.query.filter(
        StockItem.quantity <= StockItem.min_quantity,
        StockItem.min_quantity > 0
    ).order_by(StockItem.quantity.asc()).all()
    
    return render_template('stock/alerts.html',
                         title='Alertes Stock',
                         alert_items=alert_items)

@bp.route('/api/check-alerts', methods=['GET'])
@login_required
def check_alerts():
    """API pour vérifier les alertes de stock (AJAX)"""
    alert_items = StockItem.query.filter(
        StockItem.quantity <= StockItem.min_quantity,
        StockItem.min_quantity > 0
    ).all()
    
    alerts = []
    for item in alert_items:
        alerts.append({
            'id': item.id,
            'reference': item.reference,
            'libelle': item.libelle,
            'quantity': item.quantity,
            'min_quantity': item.min_quantity,
            'url': url_for('stock.view', item_id=item.id)
        })
    
    return jsonify({'alerts': alerts, 'count': len(alerts)})

@bp.route('/api/stock-levels', methods=['GET'])
@login_required
def stock_levels():
    """API pour les niveaux de stock (pour graphiques)"""
    items = StockItem.query.order_by(StockItem.quantity).limit(20).all()
    
    data = {
        'labels': [item.reference for item in items],
        'datasets': [{
            'label': 'Quantité en stock',
            'data': [item.quantity for item in items],
            'backgroundColor': [
                '#dc3545' if item.check_alert() else '#28a745'
                for item in items
            ]
        }]
    }
    
    return jsonify(data)

@bp.route('/api/category-distribution', methods=['GET'])
@login_required
def category_distribution():
    """API pour la distribution par catégorie (pour graphiques)"""
    from sqlalchemy import func
    
    # Récupérer le nombre d'éléments par catégorie
    categories = db.session.query(
        StockCategory.name,
        func.count(StockItem.id).label('count')
    ).join(StockItem, StockItem.category_id == StockCategory.id, isouter=True) \
     .group_by(StockCategory.id).all()
    
    data = {
        'labels': [cat[0] for cat in categories],
        'datasets': [{
            'label': 'Nombre d\'éléments',
            'data': [cat[1] for cat in categories],
            'backgroundColor': [
                '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
                '#6c757d', '#343a40', '#fd7e14', '#e83e8c', '#20c997'
            ]
        }]
    }
    
    return jsonify(data)

@bp.route('/api/item-info/<int:stock_item_id>')
@login_required
def get_stock_item_info(stock_item_id):
    """API pour obtenir les informations d'un élément de stock"""
    stock_item = StockItem.query.get_or_404(stock_item_id)
    
    return jsonify({
        'reference': stock_item.reference,
        'libelle': stock_item.libelle,
        'quantity': float(stock_item.quantity),
        'unit': stock_item.unit,
        'price': float(stock_item.price) if stock_item.price else 0,
        'value': float(stock_item.value) if stock_item.value else 0,
        'category': stock_item.category.name if stock_item.category else None,
        'location': stock_item.location,
        'supplier': stock_item.supplier.name if stock_item.supplier else None
    })