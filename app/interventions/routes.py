from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.decorators import permission_required
from app.interventions.forms import (
    InterventionForm, InterventionTypeForm, InterventionClassForm, 
    InterventionEntityForm, InterventionStockForm, AdditionalCostForm, InterventionFileForm
)
from app.models import (
    Intervention, InterventionType, InterventionClass, InterventionEntity,
    InterventionStock, InterventionCost, Personnel, Project, StockItem, InterventionFile
)
from app.utils import save_uploaded_file, delete_uploaded_file, format_date, format_currency, format_datetime
from datetime import datetime
import json
import os

from . import bp

# ==================== TYPES D'INTERVENTIONS ====================
@bp.route('/types')
@login_required
@permission_required('interventions', 'read')
def types():
    """Liste des types d'interventions"""
    types = InterventionType.query.order_by(InterventionType.name).all()
    return render_template('interventions/types.html', 
                         title='Types d\'interventions',
                         types=types)

@bp.route('/types/add', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'create')
def add_type():
    """Ajouter un type d'intervention"""
    form = InterventionTypeForm()
    
    if form.validate_on_submit():
        intervention_type = InterventionType(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(intervention_type)
        db.session.commit()
        
        flash('Type d\'intervention ajouté avec succès!', 'success')
        return redirect(url_for('interventions.types'))
    
    return render_template('interventions/type_form.html',
                         title='Ajouter un type d\'intervention',
                         form=form)

@bp.route('/types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def edit_type(id):
    """Modifier un type d'intervention"""
    intervention_type = InterventionType.query.get_or_404(id)
    form = InterventionTypeForm(obj=intervention_type)
    
    if form.validate_on_submit():
        intervention_type.name = form.name.data
        intervention_type.description = form.description.data
        intervention_type.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Type d\'intervention modifié avec succès!', 'success')
        return redirect(url_for('interventions.types'))
    
    return render_template('interventions/type_form.html',
                         title='Modifier un type d\'intervention',
                         form=form,
                         intervention_type=intervention_type)

@bp.route('/types/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete_type(id):
    """Supprimer un type d'intervention"""
    intervention_type = InterventionType.query.get_or_404(id)
    
    if intervention_type.interventions.count() > 0:
        flash('Impossible de supprimer ce type car il est utilisé dans des interventions!', 'danger')
        return redirect(url_for('interventions.types'))
    
    db.session.delete(intervention_type)
    db.session.commit()
    
    flash('Type d\'intervention supprimé avec succès!', 'success')
    return redirect(url_for('interventions.types'))

# ==================== CLASSES D'INTERVENTIONS ====================
@bp.route('/classes')
@login_required
@permission_required('interventions', 'read')
def classes():
    """Liste des classes d'interventions"""
    classes = InterventionClass.query.order_by(InterventionClass.name).all()
    return render_template('interventions/classes.html', 
                         title='Classes d\'interventions',
                         classes=classes)

@bp.route('/classes/add', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'create')
def add_class():
    """Ajouter une classe d'intervention"""
    form = InterventionClassForm()
    
    if form.validate_on_submit():
        intervention_class = InterventionClass(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(intervention_class)
        db.session.commit()
        
        flash('Classe d\'intervention ajoutée avec succès!', 'success')
        return redirect(url_for('interventions.classes'))
    
    return render_template('interventions/class_form.html',
                         title='Ajouter une classe d\'intervention',
                         form=form)

@bp.route('/classes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def edit_class(id):
    """Modifier une classe d'intervention"""
    intervention_class = InterventionClass.query.get_or_404(id)
    form = InterventionClassForm(obj=intervention_class)
    
    if form.validate_on_submit():
        intervention_class.name = form.name.data
        intervention_class.description = form.description.data
        intervention_class.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Classe d\'intervention modifiée avec succès!', 'success')
        return redirect(url_for('interventions.classes'))
    
    return render_template('interventions/class_form.html',
                         title='Modifier une classe d\'intervention',
                         form=form,
                         intervention_class=intervention_class)

@bp.route('/classes/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete_class(id):
    """Supprimer une classe d'intervention"""
    intervention_class = InterventionClass.query.get_or_404(id)
    
    if intervention_class.interventions.count() > 0:
        flash('Impossible de supprimer cette classe car elle est utilisée dans des interventions!', 'danger')
        return redirect(url_for('interventions.classes'))
    
    db.session.delete(intervention_class)
    db.session.commit()
    
    flash('Classe d\'intervention supprimée avec succès!', 'success')
    return redirect(url_for('interventions.classes'))

# ==================== ENTITÉS D'INTERVENTIONS ====================
@bp.route('/entities')
@login_required
@permission_required('interventions', 'read')
def entities():
    """Liste des entités d'interventions"""
    entities = InterventionEntity.query.order_by(InterventionEntity.name).all()
    return render_template('interventions/entities.html', 
                         title='Entités d\'interventions',
                         entities=entities)

@bp.route('/entities/add', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'create')
def add_entity():
    """Ajouter une entité d'intervention"""
    form = InterventionEntityForm()
    
    if form.validate_on_submit():
        intervention_entity = InterventionEntity(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(intervention_entity)
        db.session.commit()
        
        flash('Entité d\'intervention ajoutée avec succès!', 'success')
        return redirect(url_for('interventions.entities'))
    
    return render_template('interventions/entity_form.html',
                         title='Ajouter une entité d\'intervention',
                         form=form)

@bp.route('/entities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def edit_entity(id):
    """Modifier une entité d'intervention"""
    intervention_entity = InterventionEntity.query.get_or_404(id)
    form = InterventionEntityForm(obj=intervention_entity)
    
    if form.validate_on_submit():
        intervention_entity.name = form.name.data
        intervention_entity.description = form.description.data
        intervention_entity.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Entité d\'intervention modifiée avec succès!', 'success')
        return redirect(url_for('interventions.entities'))
    
    return render_template('interventions/entity_form.html',
                         title='Modifier une entité d\'intervention',
                         form=form,
                         intervention_entity=intervention_entity)

@bp.route('/entities/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete_entity(id):
    """Supprimer une entité d'intervention"""
    intervention_entity = InterventionEntity.query.get_or_404(id)
    
    if intervention_entity.interventions.count() > 0:
        flash('Impossible de supprimer cette entité car elle est utilisée dans des interventions!', 'danger')
        return redirect(url_for('interventions.entities'))
    
    db.session.delete(intervention_entity)
    db.session.commit()
    
    flash('Entité d\'intervention supprimée avec succès!', 'success')
    return redirect(url_for('interventions.entities'))

# ==================== INTERVENTIONS ====================
@bp.route('/')
@bp.route('/index')
@login_required
@permission_required('interventions', 'read')
def index():
    """Liste des interventions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'intervention_number')
    sort_order = request.args.get('sort_order', 'asc')
    
    query = Intervention.query
    
    if search:
        query = query.filter(
            db.or_(
                Intervention.intervention_number.ilike(f'%{search}%'),
                Intervention.client_name.ilike(f'%{search}%'),
                Intervention.location.ilike(f'%{search}%')
            )
        )
    
    # Tri
    if sort_by == 'client_name':
        order_field = Intervention.client_name
    elif sort_by == 'intervention_date':
        order_field = Intervention.intervention_date
    elif sort_by == 'client_contact_date':
        order_field = Intervention.client_contact_date
    elif sort_by == 'status':
        order_field = Intervention.status
    else:
        order_field = Intervention.intervention_number
    
    if sort_order == 'desc':
        query = query.order_by(order_field.desc())
    else:
        query = query.order_by(order_field.asc())
    
    interventions = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('interventions/index.html',
                         title='Liste des interventions',
                         interventions=interventions,
                         search=search,
                         sort_by=sort_by,
                         sort_order=sort_order)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'create')
def add():
    """Ajouter une intervention"""
    form = InterventionForm()
    
    # CORRECTION: Utiliser None au lieu de '' pour la première option
    form.type_id.choices = [(t.id, t.name) for t in InterventionType.query.order_by('name').all()]
    form.class_id.choices = [(c.id, c.name) for c in InterventionClass.query.order_by('name').all()]
    form.entity_id.choices = [(e.id, e.name) for e in InterventionEntity.query.order_by('name').all()]
    form.personnel_ids.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Personnel.query.filter_by(is_active=True).order_by('first_name').all()]
    # CORRECTION ICI - Utiliser None au lieu de ''
    form.project_id.choices = [(None, 'Sélectionner un projet')] + [(p.id, p.name) for p in Project.query.filter_by(status='completed').order_by('name').all()]
    
    if form.validate_on_submit():
        intervention = Intervention(
            intervention_number=form.intervention_number.data,
            client_name=form.client_name.data,
            location=form.location.data,
            type_id=form.type_id.data,
            class_id=form.class_id.data,
            entity_id=form.entity_id.data,
            client_contact_date=form.client_contact_date.data,
            intervention_date=form.intervention_date.data,
            planned_end_date=form.planned_end_date.data,
            actual_end_date=form.actual_end_date.data,
            status=form.status.data,
            anomaly_description=form.anomaly_description.data,
            tasks_description=form.tasks_description.data,
            linked_to_project=form.linked_to_project.data,
            project_id=form.project_id.data if form.linked_to_project.data and form.project_id.data else None,
            justification_delay=form.justification_delay.data,
            created_by=current_user.id
        )
        
        db.session.add(intervention)
        db.session.flush()
        
        if form.personnel_ids.data:
            for personnel_id in form.personnel_ids.data:
                intervention.personnel.append(Personnel.query.get(personnel_id))
        
        db.session.commit()
        
        flash('Intervention ajoutée avec succès!', 'success')
        return redirect(url_for('interventions.view', id=intervention.id))
    
    return render_template('interventions/add.html',
                         title='Ajouter une intervention',
                         form=form)

@bp.route('/<int:id>')
@login_required
@permission_required('interventions', 'read')
def view(id):
    """Voir une intervention"""
    intervention = Intervention.query.get_or_404(id)
    
    return render_template('interventions/view.html',
                         title=f'Intervention #{intervention.intervention_number}',
                         intervention=intervention)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def edit(id):
    """Modifier une intervention"""
    intervention = Intervention.query.get_or_404(id)
    
    form = InterventionForm(obj=intervention)
    
    # Remplir les listes déroulantes
    form.type_id.choices = [(t.id, t.name) for t in InterventionType.query.order_by('name').all()]
    form.class_id.choices = [(c.id, c.name) for c in InterventionClass.query.order_by('name').all()]
    form.entity_id.choices = [(e.id, e.name) for e in InterventionEntity.query.order_by('name').all()]
    form.personnel_ids.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Personnel.query.filter_by(is_active=True).order_by('first_name').all()]
    # CORRECTION ICI
    form.project_id.choices = [(None, 'Sélectionner un projet')] + [(p.id, p.name) for p in Project.query.filter_by(status='completed').order_by('name').all()]
    
    # Pré-sélectionner le personnel
    if request.method == 'GET':
        form.personnel_ids.data = [p.id for p in intervention.personnel]
    
    if form.validate_on_submit():
        intervention.intervention_number = form.intervention_number.data
        intervention.client_name = form.client_name.data
        intervention.location = form.location.data
        intervention.type_id = form.type_id.data
        intervention.class_id = form.class_id.data
        intervention.entity_id = form.entity_id.data
        intervention.client_contact_date = form.client_contact_date.data
        intervention.intervention_date = form.intervention_date.data
        intervention.planned_end_date = form.planned_end_date.data
        intervention.actual_end_date = form.actual_end_date.data
        intervention.status = form.status.data
        intervention.anomaly_description = form.anomaly_description.data
        intervention.tasks_description = form.tasks_description.data
        intervention.linked_to_project = form.linked_to_project.data
        intervention.project_id = form.project_id.data if form.linked_to_project.data and form.project_id.data else None
        intervention.justification_delay = form.justification_delay.data
        intervention.updated_at = datetime.utcnow()
        intervention.updated_by = current_user.id
        
        # Mettre à jour le personnel
        intervention.personnel = []
        if form.personnel_ids.data:
            for personnel_id in form.personnel_ids.data:
                intervention.personnel.append(Personnel.query.get(personnel_id))
        
        db.session.commit()
        
        flash('Intervention modifiée avec succès!', 'success')
        return redirect(url_for('interventions.view', id=intervention.id))
    
    return render_template('interventions/edit.html',
                         title='Modifier une intervention',
                         form=form,
                         intervention=intervention)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete(id):
    """Supprimer une intervention"""
    intervention = Intervention.query.get_or_404(id)
    
    db.session.delete(intervention)
    db.session.commit()
    
    flash('Intervention supprimée avec succès!', 'success')
    return redirect(url_for('interventions.index'))

# ==================== GESTION DU STOCK ====================
@bp.route('/<int:id>/stock', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def manage_stock(id):
    """Gérer les articles de stock d'une intervention"""
    intervention = Intervention.query.get_or_404(id)
    form = InterventionStockForm()
    
    # Remplir la liste des articles
    stock_items = StockItem.query.order_by('reference').all()
    form.stock_item_id.choices = [(s.id, f"{s.reference} - {s.libelle} (Stock: {s.quantity})") for s in stock_items]
    
    if form.validate_on_submit():
        stock_item = InterventionStock(
            intervention_id=id,
            stock_item_id=form.stock_item_id.data,
            estimated_quantity=form.estimated_quantity.data,
            actual_quantity=form.actual_quantity.data,
            remaining_quantity=form.remaining_quantity.data,
            additional_quantity=form.additional_quantity.data,
            justification=form.justification.data,
            validated=form.validated.data
        )
        
        db.session.add(stock_item)
        db.session.commit()
        
        flash('Article ajouté à l\'intervention!', 'success')
        return redirect(url_for('interventions.manage_stock', id=id))
    
    stock_items = intervention.stock_items.all()
    
    return render_template('interventions/stock.html',
                         title=f'Stock - Intervention #{intervention.intervention_number}',
                         intervention=intervention,
                         form=form,
                         stock_items=stock_items)

@bp.route('/stock/<int:stock_id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete_stock_item(stock_id):
    """Supprimer un article de stock d'une intervention"""
    stock_item = InterventionStock.query.get_or_404(stock_id)
    intervention_id = stock_item.intervention_id
    
    db.session.delete(stock_item)
    db.session.commit()
    
    flash('Article supprimé de l\'intervention!', 'success')
    return redirect(url_for('interventions.manage_stock', id=intervention_id))

# ==================== COÛTS SUPPLÉMENTAIRES ====================
@bp.route('/<int:id>/costs', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def manage_costs(id):
    """Gérer les coûts supplémentaires d'une intervention"""
    intervention = Intervention.query.get_or_404(id)
    form = AdditionalCostForm()
    
    if form.validate_on_submit():
        cost = InterventionCost(
            intervention_id=id,
            cost_name=form.cost_name.data,
            amount=form.amount.data
        )
        
        db.session.add(cost)
        db.session.commit()
        
        flash('Coût supplémentaire ajouté!', 'success')
        return redirect(url_for('interventions.manage_costs', id=id))
    
    costs = intervention.costs.all()
    
    return render_template('interventions/costs.html',
                         title=f'Coûts - Intervention #{intervention.intervention_number}',
                         intervention=intervention,
                         form=form,
                         costs=costs)

@bp.route('/costs/<int:cost_id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete_cost(cost_id):
    """Supprimer un coût supplémentaire"""
    cost = InterventionCost.query.get_or_404(cost_id)
    intervention_id = cost.intervention_id
    
    db.session.delete(cost)
    db.session.commit()
    
    flash('Coût supprimé!', 'success')
    return redirect(url_for('interventions.manage_costs', id=intervention_id))

# ==================== API ====================
@bp.route('/api/search')
@login_required
def api_search():
    """API pour la recherche AJAX"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    query = Intervention.query
    
    if search:
        query = query.filter(
            db.or_(
                Intervention.intervention_number.ilike(f'%{search}%'),
                Intervention.client_name.ilike(f'%{search}%'),
                Intervention.location.ilike(f'%{search}%')
            )
        )
    
    interventions = query.paginate(page=page, per_page=10, error_out=False)
    
    results = []
    for intervention in interventions.items:
        results.append({
            'id': intervention.id,
            'intervention_number': intervention.intervention_number,
            'client_name': intervention.client_name,
            'type': intervention.type.name if intervention.type else '',
            'class': intervention.intervention_class.name if intervention.intervention_class else '',
            'entity': intervention.entity.name if intervention.entity else '',
            'intervention_date': intervention.intervention_date.strftime('%d/%m/%Y') if intervention.intervention_date else '',
            'status': intervention.status
        })
    
    return jsonify({
        'results': results,
        'has_next': interventions.has_next,
        'has_prev': interventions.has_prev,
        'total': interventions.total
    })

@bp.route('/api/projects')
@login_required
def api_projects():
    """API pour rechercher des projets"""
    search = request.args.get('q', '')
    
    query = Project.query.filter_by(status='completed')
    
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
    
    projects = query.limit(10).all()
    
    results = []
    for project in projects:
        results.append({
            'id': project.id,
            'name': project.name,
            'client': project.client.name if project.client else '',
            'start_date': project.start_date.strftime('%d/%m/%Y') if project.start_date else '',
            'end_date': project.end_date.strftime('%d/%m/%Y') if project.end_date else ''
        })
    
    return jsonify(results)

# ==================== GESTION DES FICHIERS ====================
@bp.route('/<int:id>/files', methods=['GET', 'POST'])
@login_required
@permission_required('interventions', 'update')
def manage_files(id):
    """Gérer les fichiers d'une intervention"""
    intervention = Intervention.query.get_or_404(id)
    form = InterventionFileForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        # Sauvegarder le fichier
        file_info = save_uploaded_file(file, 'interventions')
        
        if file_info:
            intervention_file = InterventionFile(
                intervention_id=id,
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                file_type=file_info['extension'],
                file_name=form.file_name.data,
                description=form.description.data,
                uploaded_by=current_user.id
            )
            
            db.session.add(intervention_file)
            db.session.commit()
            
            flash('Fichier uploadé avec succès!', 'success')
            return redirect(url_for('interventions.manage_files', id=id))
        else:
            flash('Erreur lors de l\'upload du fichier!', 'danger')
    
    files = intervention.files.order_by(InterventionFile.uploaded_at.desc()).all()
    
    return render_template('interventions/files.html',
                         title=f'Fichiers - Intervention #{intervention.intervention_number}',
                         intervention=intervention,
                         form=form,
                         files=files)

@bp.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
@permission_required('interventions', 'delete')
def delete_file(file_id):
    """Supprimer un fichier d'intervention"""
    file = InterventionFile.query.get_or_404(file_id)
    intervention_id = file.intervention_id
    
    # Supprimer le fichier physique
    delete_uploaded_file(file.filename, 'interventions')
    
    db.session.delete(file)
    db.session.commit()
    
    flash('Fichier supprimé!', 'success')
    return redirect(url_for('interventions.manage_files', id=intervention_id))

@bp.route('/files/<int:file_id>/download')
@login_required
@permission_required('interventions', 'read')
def download_file(file_id):
    """Télécharger un fichier d'intervention"""
    file = InterventionFile.query.get_or_404(file_id)
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'interventions')
    
    return send_from_directory(
        upload_folder,
        file.filename,
        as_attachment=True,
        download_name=file.original_filename
    )

@bp.route('/files/<int:file_id>/view')
@login_required
@permission_required('interventions', 'read')
def view_file(file_id):
    """Voir un fichier d'intervention dans le navigateur"""
    file = InterventionFile.query.get_or_404(file_id)
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'interventions')
    
    return send_from_directory(
        upload_folder,
        file.filename,
        as_attachment=False
    )

@bp.route('/api/files')
@login_required
def api_files():
    """API pour récupérer les fichiers d'une intervention"""
    intervention_id = request.args.get('intervention_id', type=int)
    
    if not intervention_id:
        return jsonify([])
    
    intervention = Intervention.query.get_or_404(intervention_id)
    files = intervention.files.all()
    
    results = []
    for file in files:
        results.append({
            'id': file.id,
            'filename': file.filename,
            'original_filename': file.original_filename,
            'file_name': file.file_name,
            'file_type': file.file_type,
            'description': file.description,
            'uploaded_at': file.uploaded_at.isoformat() if file.uploaded_at else None,
            'uploader': file.uploader.username if file.uploader else None
        })
    
    return jsonify(results)