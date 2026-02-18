from flask import render_template, current_app,redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from app.projects import bp
from app.projects.forms import ProjectForm, TaskForm, TaskTypeForm, TaskStockItemForm, AdditionalCostForm, ProjectFileForm
from app.models import Project, Task, TaskType, TaskStockItem, AdditionalCost, ProjectFile, StockItem, Personnel, Group
from app import db
from app.decorators import permission_required
from app.utils import save_uploaded_file, delete_uploaded_file, check_stock_availability, sanitize_input
from datetime import datetime, date
import os
import json

@bp.route('/')
@login_required
@permission_required('projects', 'read')
def index():
    """Liste des projets"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    
    # Construire la requête avec filtres
    query = Project.query
    
    if search:
        query = query.filter(
            db.or_(
                Project.name.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter_by(status=status)
    
    if priority:
        query = query.filter_by(priority=priority)
    
    # Pagination
    projects = query.order_by(Project.start_date.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    # Calculer les statistiques pour le dashboard
    stats = {
        'in_progress': Project.query.filter_by(status='in_progress').count(),
        'completed': Project.query.filter_by(status='completed').count(),
        'high_priority': Project.query.filter_by(priority='high').count()
    }
    
    return render_template('projects/index.html',
                         title='Gestion des Projets',
                         projects=projects,
                         search=search,
                         selected_status=status,
                         selected_priority=priority,
                         stats=stats,
                         Project=Project)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('projects', 'create')
def add():
    """Ajouter un projet"""
    form = ProjectForm()
    
    # NOUVEAU: Remplir les choix de clients
    from app.models import Client
    form.client_id.choices = [(0, '-- Sélectionner un client --')] + [
        (c.id, f"{c.name}" + (f" ({c.company})" if c.company else "")) 
        for c in Client.query.filter_by(is_active=True).order_by(Client.name).all()
    ]
    
    # Pré-sélectionner le client si passé en paramètre
    client_id = request.args.get('client_id', type=int)
    if client_id and not form.is_submitted():
        form.client_id.data = client_id
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        project = Project(
            name=sanitize_input(form.name.data),
            client_id=form.client_id.data,
            description=sanitize_input(form.description.data) if form.description.data else None,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            estimated_budget=form.estimated_budget.data,
            budget_reel=form.budget_reel.data or 0.0,
            prix_vente=form.prix_vente.data or 0.0,
            marge=(form.prix_vente.data or 0.0) - (form.budget_reel.data or 0.0),
            status=form.status.data,
            priority=form.priority.data,
            notes=sanitize_input(form.notes.data) if form.notes.data else None
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash(f'Projet {project.name} créé avec succès!', 'success')
        return redirect(url_for('projects.view', project_id=project.id))
    
    return render_template('projects/form.html',
                         title='Créer un projet',
                         form=form)

@bp.route('/<int:project_id>')
@login_required
@permission_required('projects', 'read')
def view(project_id):
    """Voir les détails d'un projet"""
    project = Project.query.get_or_404(project_id)
    
    # Calculer la progression et le coût
    project.calculate_actual_cost()
    
    # Tâches du projet
    tasks = project.tasks.order_by(Task.start_date).all()
    
    # Calculer les statistiques de tâches
    task_stats = {
        'total': len(tasks),
        'pending': len([t for t in tasks if t.status == 'pending']),
        'in_progress': len([t for t in tasks if t.status == 'in_progress']),
        'completed': len([t for t in tasks if t.status == 'completed']),
        'cancelled': len([t for t in tasks if t.status == 'cancelled'])
    }
    
    # Add today's date for template calculations
    today = date.today()
    
    return render_template('projects/view.html',
                         title=f'Projet - {project.name}',
                         project=project,
                         tasks=tasks,
                         task_stats=task_stats,
                         today=today)

@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('projects', 'update')
def edit(project_id):
    """Modifier un projet"""
    project = Project.query.get_or_404(project_id)
    form = ProjectForm()
    
    # NOUVEAU: Remplir les choix de clients
    from app.models import Client
    form.client_id.choices = [(0, '-- Sélectionner un client --')] + [
        (c.id, f"{c.name}" + (f" ({c.company})" if c.company else "")) 
        for c in Client.query.filter_by(is_active=True).order_by(Client.name).all()
    ]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        project.name = sanitize_input(form.name.data)
        project.client_id = form.client_id.data
        project.description = sanitize_input(form.description.data) if form.description.data else None
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.estimated_budget = form.estimated_budget.data
        project.budget_reel = form.budget_reel.data or 0.0
        project.prix_vente = form.prix_vente.data or 0.0
        project.marge = (form.prix_vente.data or 0.0) - (form.budget_reel.data or 0.0)
        project.status = form.status.data
        project.priority = form.priority.data
        project.notes = sanitize_input(form.notes.data) if form.notes.data else None
        project.updated_at = datetime.utcnow()
        
        # Si le projet est terminé, mettre à jour la date de fin réelle
        if project.status == 'completed' and not project.actual_end_date:
            project.actual_end_date = date.today()
        
        db.session.commit()
        
        flash(f'Projet {project.name} mis à jour avec succès!', 'success')
        return redirect(url_for('projects.view', project_id=project.id))
    
    # Pré-remplir le formulaire
    form.name.data = project.name
    form.client_id.data = project.client_id
    form.description.data = project.description
    form.start_date.data = project.start_date
    form.end_date.data = project.end_date
    form.estimated_budget.data = project.estimated_budget
    form.budget_reel.data = project.budget_reel
    form.prix_vente.data = project.prix_vente
    # marge est calculée automatiquement, pas besoin de pré-remplir
    form.status.data = project.status
    form.priority.data = project.priority
    form.notes.data = project.notes
    
    return render_template('projects/form.html',
                         title='Modifier un projet',
                         form=form, 
                         project=project)

@bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@permission_required('projects', 'delete')
def delete(project_id):
    """Supprimer un projet"""
    project = Project.query.get_or_404(project_id)
    
    # Supprimer les fichiers associés
    for file in project.files:
        delete_uploaded_file(file.filename, 'projects')
        db.session.delete(file)
    
    db.session.delete(project)
    db.session.commit()
    
    flash(f'Projet {project.name} supprimé avec succès.', 'success')
    return redirect(url_for('projects.index'))

@bp.route('/<int:project_id>/tasks/add', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'create')
def add_task(project_id):
    """Ajouter une tâche à un projet"""
    project = Project.query.get_or_404(project_id)
    form = TaskForm()
    
    # Remplir les choix dynamiques
    form.task_type_id.choices = [(0, '-- Sélectionner --')] + [(t.id, t.name) for t in TaskType.query.all()]
    form.assigned_personnel.choices = [(p.id, p.get_full_name()) for p in Personnel.query.filter_by(is_active=True).all()]
    form.assigned_groups.choices = [(g.id, g.name) for g in Group.query.all()]
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        task = Task(
            name=sanitize_input(form.name.data),
            description=sanitize_input(form.description.data) if form.description.data else None,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            task_type_id=form.task_type_id.data if form.task_type_id.data else None,
            status=form.status.data,
            priority=form.priority.data,
            use_stock=form.use_stock.data,
            justification=sanitize_input(form.justification.data) if form.justification.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            project_id=project.id
        )
        
        # Ajouter le personnel assigné
        selected_personnel = Personnel.query.filter(Personnel.id.in_(form.assigned_personnel.data)).all()
        task.assigned_personnel.extend(selected_personnel)
        
        # Ajouter les groupes assignés
        selected_groups = Group.query.filter(Group.id.in_(form.assigned_groups.data)).all()
        task.assigned_groups.extend(selected_groups)
        
        db.session.add(task)
        db.session.commit()
        
        flash(f'Tâche {task.name} ajoutée avec succès!', 'success')
        return redirect(url_for('projects.view_task', task_id=task.id))
    
    # Définir les dates par défaut (celles du projet)
    form.start_date.data = project.start_date
    form.end_date.data = project.end_date
    
    return render_template('projects/task_form.html',
                         title='Ajouter une tâche',
                         form=form, project=project)


@bp.route('/tasks/<int:task_id>')
@login_required
@permission_required('tasks', 'read')
def view_task(task_id):
    """Voir les détails d'une tâche"""
    task = Task.query.get_or_404(task_id)
    
    # Charger explicitement les relations
    stock_items = task.stock_items.all()  # Convertir Query en liste
    additional_costs = task.additional_costs.all()  # Convertir Query en liste
    
    # Pour les relations many-to-many (déjà des listes)
    assigned_personnel = task.assigned_personnel  # Déjà une liste
    assigned_groups = task.assigned_groups  # Déjà une liste
    
    # Vérifier la disponibilité du stock si nécessaire
    stock_issues = []
    if task.use_stock and task.status != 'completed':
        stock_issues = task.check_stock_availability()
    
    # Calculer le coût de la tâche
    task_cost = task.calculate_cost()
    
    # Calculer les sommes et counts
    stock_items_count = len(stock_items)
    additional_costs_count = len(additional_costs)
    assigned_personnel_count = len(assigned_personnel)
    assigned_groups_count = len(assigned_groups)
    
    # Calculer les coûts totaux
    stock_items_cost = sum(item.estimated_cost or 0 for item in stock_items)
    additional_costs_total = sum(cost.amount for cost in additional_costs)
    
    # Identifier les items avec manque de stock
    shortage_items = [item for item in stock_items if not item.is_quantity_sufficient()]
    
    return render_template('projects/task_view.html',
                         title=f'Tâche - {task.name}',
                         task=task,
                         stock_issues=stock_issues,
                         task_cost=task_cost,
                         stock_items=stock_items,
                         additional_costs=additional_costs,
                         assigned_personnel=assigned_personnel,
                         assigned_groups=assigned_groups,
                         stock_items_count=stock_items_count,
                         additional_costs_count=additional_costs_count,
                         assigned_personnel_count=assigned_personnel_count,
                         assigned_groups_count=assigned_groups_count,
                         stock_items_cost=stock_items_cost,
                         additional_costs_total=additional_costs_total,
                         shortage_items=shortage_items)


@bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'update')
def edit_task(task_id):
    """Modifier une tâche"""
    task = Task.query.get_or_404(task_id)
    form = TaskForm(obj=task)  # Utiliser obj pour pré-remplir automatiquement
    
    # Remplir les choix dynamiques
    form.task_type_id.choices = [(0, '-- Sélectionner --')] + [(t.id, t.name) for t in TaskType.query.all()]
    form.assigned_personnel.choices = [(p.id, p.get_full_name()) for p in Personnel.query.filter_by(is_active=True).all()]
    form.assigned_groups.choices = [(g.id, g.name) for g in Group.query.all()]
    
    if form.validate_on_submit():
        try:
            # DEBUG: Vérifier que nous modifions bien la tâche existante
            print(f"Modification de la tâche {task.id}: {task.name}")
            
            # Nettoyer les entrées
            task.name = sanitize_input(form.name.data)
            task.description = sanitize_input(form.description.data) if form.description.data else None
            task.start_date = form.start_date.data
            task.end_date = form.end_date.data
            task.task_type_id = form.task_type_id.data if form.task_type_id.data else None
            task.status = form.status.data
            task.priority = form.priority.data
            task.use_stock = form.use_stock.data
            task.justification = sanitize_input(form.justification.data) if form.justification.data else None
            task.notes = sanitize_input(form.notes.data) if form.notes.data else None
            task.updated_at = datetime.utcnow()
            
            # Mettre à jour le personnel assigné
            task.assigned_personnel.clear()
            if form.assigned_personnel.data:
                selected_personnel = Personnel.query.filter(Personnel.id.in_(form.assigned_personnel.data)).all()
                task.assigned_personnel.extend(selected_personnel)
            
            # Mettre à jour les groupes assignés
            task.assigned_groups.clear()
            if form.assigned_groups.data:
                selected_groups = Group.query.filter(Group.id.in_(form.assigned_groups.data)).all()
                task.assigned_groups.extend(selected_groups)
            
            # Si la tâche est terminée, mettre à jour la date de fin réelle
            if task.status == 'completed' and not task.actual_end_date:
                task.actual_end_date = date.today()
            
            db.session.commit()
            flash(f'Tâche "{task.name}" mise à jour avec succès!', 'success')
            return redirect(url_for('projects.view_task', task_id=task.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la modification: {str(e)}")  # DEBUG
            flash(f'Erreur lors de la modification de la tâche : {str(e)}', 'danger')
    
    # S'assurer que les données sont bien pré-remplies pour les champs SelectMultiple
    elif request.method == 'GET':
        form.assigned_personnel.data = [p.id for p in task.assigned_personnel]
        form.assigned_groups.data = [g.id for g in task.assigned_groups]
    
    return render_template('projects/task_form.html',
                         title='Modifier une tâche',
                         form=form, 
                         task=task, 
                         project=task.project)

@bp.route('/tasks/<int:task_id>/validate', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def validate_task(task_id):
    """Valider une tâche comme terminée et correcte"""
    task = Task.query.get_or_404(task_id)
    
    # Vérifier si la tâche est déjà terminée
    if task.status == 'completed':
        flash('Cette tâche est déjà marquée comme terminée.', 'warning')
        return redirect(url_for('projects.view_task', task_id=task.id))
    
    # Vérifier la disponibilité du stock si nécessaire
    if task.use_stock:
        stock_issues = task.check_stock_availability()
        if stock_issues:
            flash('Impossible de valider: stock insuffisant!', 'danger')
            return redirect(url_for('projects.view_task', task_id=task.id))
    
    # Mettre à jour le statut
    task.status = 'completed'
    task.actual_end_date = date.today()
    task.updated_at = datetime.utcnow()
    
    # Utiliser le stock si nécessaire
    if task.use_stock:
        for task_item in task.stock_items:
            if task_item.stock_item and task_item.actual_quantity_used:
                task_item.stock_item.quantity -= task_item.actual_quantity_used
                task_item.stock_item.calculate_value()
    
    db.session.commit()
    
    flash(f'Tâche {task.name} validée avec succès!', 'success')
    return redirect(url_for('projects.view_task', task_id=task.id))

@bp.route('/tasks/<int:task_id>/invalidate', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'update')
def invalidate_task(task_id):
    """Invalider une tâche (erreur ou besoin de temps supplémentaire)"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        justification = request.form.get('justification')
        
        if not justification:
            flash('Veuillez fournir un justificatif.', 'danger')
            return redirect(url_for('projects.invalidate_task', task_id=task.id))
        
        # Restaurer le stock si nécessaire
        if task.use_stock and task.status == 'completed':
            for task_item in task.stock_items:
                if task_item.stock_item and task_item.actual_quantity_used:
                    task_item.stock_item.quantity += task_item.actual_quantity_used
                    task_item.stock_item.calculate_value()
        
        # Mettre à jour la tâche
        task.status = 'in_progress'
        task.actual_end_date = None
        task.justification = f"{task.justification or ''}\n\n[INVALIDATION - {datetime.now().strftime('%d/%m/%Y %H:%M')}]: {justification}"
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Tâche invalidée. Retour en statut "En cours".', 'warning')
        return redirect(url_for('projects.view_task', task_id=task.id))
    
    return render_template('projects/task_invalidate.html',
                         title='Invalider la tâche',
                         task=task)

@bp.route('/tasks/<int:task_id>/complete-with-error', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def complete_with_error(task_id):
    """Marquer une tâche comme terminée avec erreur/justificatif"""
    task = Task.query.get_or_404(task_id)
    
    error_description = request.form.get('error_description')
    additional_time_needed = request.form.get('additional_time_needed')
    
    if not error_description:
        flash('Veuillez décrire l\'erreur ou le problème.', 'danger')
        return redirect(url_for('projects.view_task', task_id=task.id))
    
    # Mettre à jour la tâche
    task.status = 'completed'
    task.actual_end_date = date.today()
    task.justification = f"{task.justification or ''}\n\n[TERMINÉ AVEC ERREUR - {datetime.now().strftime('%d/%m/%Y %H:%M')}]: {error_description}"
    task.notes = f"{task.notes or ''}\n\nTemps supplémentaire nécessaire: {additional_time_needed or 'Non spécifié'}"
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Tâche marquée comme terminée avec erreur/justificatif.', 'warning')
    return redirect(url_for('projects.view_task', task_id=task.id))

@bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
@permission_required('tasks', 'delete')
def delete_task(task_id):
    """Supprimer une tâche"""
    task = Task.query.get_or_404(task_id)
    project_id = task.project_id
    
    db.session.delete(task)
    db.session.commit()
    
    flash(f'Tâche {task.name} supprimée avec succès.', 'success')
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/tasks/types')
@login_required
@permission_required('tasks', 'read')
def task_types():
    """Liste des types de tâches"""
    task_types = TaskType.query.all()
    return render_template('projects/task_types.html',
                         title='Types de Tâches',
                         task_types=task_types)



@bp.route('/tasks/types/add', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'create')
def add_task_type():
    """Ajouter un type de tâche"""
    form = TaskTypeForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        task_type = TaskType(
            name=sanitize_input(form.name.data),
            description=sanitize_input(form.description.data) if form.description.data else None,
            default_duration=form.default_duration.data
        )
        
        db.session.add(task_type)
        db.session.commit()
        
        flash(f'Type de tâche {task_type.name} ajouté avec succès!', 'success')
        return redirect(url_for('projects.task_types'))
    
    return render_template('projects/task_type_form.html',
                         title='Ajouter un type de tâche',
                         form=form)

@bp.route('/tasks/types/<int:type_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'update')
def edit_task_type(type_id):
    """Modifier un type de tâche"""
    task_type = TaskType.query.get_or_404(type_id)
    form = TaskTypeForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        task_type.name = sanitize_input(form.name.data)
        task_type.description = sanitize_input(form.description.data) if form.description.data else None
        task_type.default_duration = form.default_duration.data
        
        db.session.commit()
        
        flash(f'Type de tâche {task_type.name} mis à jour avec succès!', 'success')
        return redirect(url_for('projects.task_types'))
    
    # Pré-remplir le formulaire
    form.name.data = task_type.name
    form.description.data = task_type.description
    form.default_duration.data = task_type.default_duration
    
    return render_template('projects/task_type_form.html',
                         title='Modifier un type de tâche',
                         form=form, task_type=task_type)

@bp.route('/tasks/types/<int:type_id>/delete', methods=['POST'])
@login_required
@permission_required('tasks', 'delete')
def delete_task_type(type_id):
    """Supprimer un type de tâche"""
    task_type = TaskType.query.get_or_404(type_id)
    
    # Vérifier si le type est utilisé
    if task_type.tasks.count() > 0:
        flash('Impossible de supprimer ce type de tâche car il est utilisé.', 'danger')
        return redirect(url_for('projects.task_types'))
    
    db.session.delete(task_type)
    db.session.commit()
    
    flash(f'Type de tâche {task_type.name} supprimé avec succès.', 'success')
    return redirect(url_for('projects.task_types'))

@bp.route('/tasks/<int:task_id>/stock-items', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'update')
def manage_stock_items(task_id):
    """Gérer les éléments de stock d'une tâche"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Mettre à jour ou ajouter des éléments de stock
            for item_data in data.get('items', []):
                if item_data.get('id'):
                    # Mettre à jour un élément existant
                    task_item = TaskStockItem.query.get(item_data['id'])
                    if task_item and task_item.task_id == task.id:
                        task_item.estimated_quantity = item_data['estimated_quantity']
                        task_item.actual_quantity_used = item_data.get('actual_quantity_used')
                        task_item.remaining_quantity = item_data.get('remaining_quantity')
                        task_item.estimated_cost = item_data.get('estimated_cost')
                        task_item.return_to_stock = item_data.get('return_to_stock', False)
                        task_item.notes = sanitize_input(item_data.get('notes'))
                else:
                    # Ajouter un nouvel élément
                    if item_data.get('stock_item_id'):
                        task_item = TaskStockItem(
                            task_id=task.id,
                            stock_item_id=item_data['stock_item_id'],
                            estimated_quantity=item_data['estimated_quantity'],
                            estimated_cost=item_data.get('estimated_cost'),
                            notes=sanitize_input(item_data.get('notes')),
                            return_to_stock=item_data.get('return_to_stock', False)
                        )
                        db.session.add(task_item)
            
            # Supprimer les éléments non présents
            existing_ids = [item['id'] for item in data.get('items', []) if item.get('id')]
            if existing_ids:
                TaskStockItem.query.filter(
                    TaskStockItem.task_id == task.id,
                    ~TaskStockItem.id.in_(existing_ids)
                ).delete(synchronize_session=False)
            
            db.session.commit()
            
            # Mettre à jour le stock si nécessaire
            if task.use_stock and task.status == 'in_progress':
                update_stock_from_task(task)
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    # GET: Retourner les éléments de stock de la tâche
    stock_items = StockItem.query.all()
    task_items = task.stock_items.all()
    
    items_data = []
    for item in task_items:
        items_data.append({
            'id': item.id,
            'stock_item_id': item.stock_item_id,
            'stock_item_name': item.stock_item.libelle if item.stock_item else '',
            'reference': item.stock_item.reference if item.stock_item else '',
            'estimated_quantity': item.estimated_quantity,
            'actual_quantity_used': item.actual_quantity_used,
            'remaining_quantity': item.remaining_quantity,
            'estimated_cost': item.estimated_cost,
            'return_to_stock': item.return_to_stock,
            'notes': item.notes,
            'available_quantity': item.stock_item.quantity if item.stock_item else 0
        })
    
    return jsonify({
        'success': True,
        'items': items_data,
        'stock_items': [{'id': s.id, 'text': f'{s.reference} - {s.libelle}'} for s in stock_items]
    })

def update_stock_from_task(task):
    """Mettre à jour le stock à partir des éléments d'une tâche"""
    for task_item in task.stock_items:
        if task_item.stock_item and task_item.actual_quantity_used:
            # Diminuer le stock pour la quantité utilisée
            task_item.stock_item.quantity -= task_item.actual_quantity_used
            
            # Ajouter la quantité retournée si applicable
            if task_item.return_to_stock and task_item.remaining_quantity:
                task_item.stock_item.quantity += task_item.remaining_quantity
            
            # Recalculer la valeur
            task_item.stock_item.calculate_value()
    
    db.session.commit()

@bp.route('/tasks/<int:task_id>/additional-costs', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'update')
def manage_additional_costs(task_id):
    """Gérer les frais supplémentaires d'une tâche"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        form = AdditionalCostForm()
        
        if form.validate_on_submit():
            # Nettoyer les entrées
            cost = AdditionalCost(
                name=sanitize_input(form.name.data),
                amount=form.amount.data,
                justification=sanitize_input(form.justification.data) if form.justification.data else None,
                date=form.date.data,
                task_id=task.id
            )
            
            db.session.add(cost)
            db.session.commit()
            
            flash('Frais supplémentaire ajouté avec succès!', 'success')
        
        return redirect(url_for('projects.view_task', task_id=task.id))
    
    # GET: Afficher le formulaire
    form = AdditionalCostForm()
    
    return render_template('projects/additional_cost_form.html',
                         title='Ajouter un frais supplémentaire',
                         form=form, task=task)

@bp.route('/additional-costs/<int:cost_id>/delete', methods=['POST'])
@login_required
@permission_required('tasks', 'delete')
def delete_additional_cost(cost_id):
    """Supprimer un frais supplémentaire"""
    cost = AdditionalCost.query.get_or_404(cost_id)
    task_id = cost.task_id
    
    db.session.delete(cost)
    db.session.commit()
    
    flash('Frais supplémentaire supprimé avec succès.', 'success')
    return redirect(url_for('projects.view_task', task_id=task_id))

@bp.route('/<int:project_id>/upload', methods=['POST'])
@login_required
@permission_required('projects', 'update')
def upload_file(project_id):
    """Uploader un fichier pour un projet - OPTIMIZED"""
    project = Project.query.get_or_404(project_id)
    
    # Vérifier qu'un fichier a été envoyé
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
    
    # Vérifier la taille du fichier (10MB max)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Revenir au début
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        return jsonify({
            'success': False, 
            'error': f'Fichier trop volumineux. Max: {max_size/(1024*1024)}MB'
        }), 400
    
    # Sauvegarder le fichier
    file_info = save_uploaded_file(file, 'projects')
    
    if file_info:
        # Récupérer la description
        description = request.form.get('description', '')
        
        # Créer l'entrée en base de données
        project_file = ProjectFile(
            filename=file_info['filename'],
            original_filename=file_info['original_filename'],
            file_type=file_info['extension'],
            description=sanitize_input(description) if description else None,
            project_id=project.id
        )
        
        db.session.add(project_file)
        db.session.commit()
        
        # Si c'est une requête AJAX, retourner JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'file_id': project_file.id,
                'filename': project_file.original_filename
            })
        
        flash('Fichier uploadé avec succès!', 'success')
        return redirect(url_for('projects.view', project_id=project.id))
    else:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Type de fichier non autorisé'}), 400
        
        flash('Erreur lors de l\'upload du fichier.', 'danger')
        return redirect(url_for('projects.view', project_id=project.id))


@bp.route('/file/<int:file_id>/preview')
@login_required
@permission_required('projects', 'read')
def preview_project_file(file_id):
    """Prévisualiser un fichier de projet (pour images et PDFs)"""
    project_file = ProjectFile.query.get_or_404(file_id)
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects')
    
    # Vérifier que le type de fichier est prévisualisable
    if project_file.file_type not in ['pdf', 'png', 'jpg', 'jpeg']:
        return "Aperçu non disponible pour ce type de fichier", 400
    
    # Déterminer le type MIME
    mime_types = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg'
    }
    
    return send_from_directory(
        upload_folder,
        project_file.filename,
        mimetype=mime_types.get(project_file.file_type, 'application/octet-stream')
    )

@bp.route('/file/<int:file_id>/download')
@login_required
@permission_required('projects', 'read')
def download_project_file(file_id):
    """Télécharger un fichier de projet"""
    project_file = ProjectFile.query.get_or_404(file_id)
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects')
    
    return send_from_directory(
        upload_folder,
        project_file.filename,
        as_attachment=True,
        download_name=project_file.original_filename
    )

@bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
@permission_required('projects', 'delete')
def delete_project_file(file_id):
    """Supprimer un fichier de projet"""
    project_file = ProjectFile.query.get_or_404(file_id)
    project_id = project_file.project_id
    
    # Supprimer le fichier physique
    delete_uploaded_file(project_file.filename, 'projects')
    
    # Supprimer l'entrée de la base de données
    db.session.delete(project_file)
    db.session.commit()
    
    flash('Fichier supprimé avec succès.', 'success')
    return redirect(url_for('projects.view', project_id=project_id))


@bp.route('/api/projects-data', methods=['GET'])
@login_required
def projects_data_api():
    """API pour les données des projets (pour graphiques)"""
    projects = Project.query.all()
    
    data = {
        'labels': [p.name for p in projects],
        'datasets': [{
            'label': 'Budget estimé',
            'data': [p.estimated_budget for p in projects],
            'backgroundColor': '#007bff'
        }, {
            'label': 'Coût actuel',
            'data': [p.actual_cost for p in projects],
            'backgroundColor': '#dc3545'
        }]
    }
    
    return jsonify(data)

@bp.route('/api/tasks-calendar', methods=['GET'])
@login_required
def tasks_calendar_api():
    """API pour les tâches du calendrier"""
    start = request.args.get('start')
    end = request.args.get('end')
    
    # Filtrer les tâches par période
    query = Task.query
    
    if start and end:
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            query = query.filter(Task.start_date <= end_date, Task.end_date >= start_date)
        except ValueError:
            pass
    
    tasks = query.all()
    
    events = []
    for task in tasks:
        # Déterminer la couleur en fonction de la priorité
        color_map = {
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        color = color_map.get(task.priority, '#007bff')
        
        events.append({
            'id': task.id,
            'title': task.name,
            'start': task.start_date.isoformat(),
            'end': task.end_date.isoformat(),
            'color': color,
            'extendedProps': {
                'project': task.project.name,
                'status': task.status,
                'priority': task.priority,
                'url': url_for('projects.view_task', task_id=task.id)
            }
        })
    
    return jsonify(events)

@bp.route('/tasks/<int:task_id>/check-stock', methods=['GET'])
@login_required
def check_task_stock(task_id):
    """Vérifier la disponibilité du stock pour une tâche"""
    task = Task.query.get_or_404(task_id)
    
    if not task.use_stock:
        return jsonify({'available': True, 'issues': []})
    
    issues = task.check_stock_availability()
    
    return jsonify({
        'available': len(issues) == 0,
        'issues': issues
    })

@bp.route('/tasks/<int:task_id>/update-status', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def update_task_status(task_id):
    """Mettre à jour le statut d'une tâche"""
    task = Task.query.get_or_404(task_id)
    
    new_status = request.form.get('status')
    if new_status not in ['pending', 'in_progress', 'completed', 'cancelled']:
        return jsonify({'success': False, 'error': 'Statut invalide'})
    
    task.status = new_status
    
    # Mettre à jour la date de fin réelle si la tâche est terminée
    if new_status == 'completed' and not task.actual_end_date:
        task.actual_end_date = date.today()
    
    # Mettre à jour le stock si la tâche commence
    if new_status == 'in_progress' and task.use_stock:
        update_stock_from_task(task)
    
    db.session.commit()
    
    return jsonify({'success': True, 'status': task.status})

@bp.route('/tasks/new', methods=['GET', 'POST'])
@login_required
@permission_required('tasks', 'create')
def new_task():
    """Créer une nouvelle tâche (standalone - pour le calendrier)"""
    form = TaskForm()
    
    # Remplir les choix dynamiques
    form.task_type_id.choices = [(0, '-- Sélectionner --')] + [(t.id, t.name) for t in TaskType.query.all()]
    form.assigned_personnel.choices = [(p.id, p.get_full_name()) for p in Personnel.query.filter_by(is_active=True).all()]
    form.assigned_groups.choices = [(g.id, g.name) for g in Group.query.all()]
    
    # Récupérer les projets actifs pour le dropdown
    active_projects = Project.query.filter(
        Project.status.in_(['planning', 'in_progress'])
    ).order_by(Project.name).all()
    
    if form.validate_on_submit():
        # Récupérer le projet sélectionné
        project_id = request.form.get('project_id')
        
        if not project_id:
            flash('Veuillez sélectionner un projet.', 'danger')
            return render_template('projects/task_form_standalone.html',
                                 title='Créer une tâche',
                                 form=form,
                                 projects=active_projects)
        
        project = Project.query.get(project_id)
        if not project:
            flash('Projet invalide.', 'danger')
            return render_template('projects/task_form_standalone.html',
                                 title='Créer une tâche',
                                 form=form,
                                 projects=active_projects)
        
        # Créer la tâche
        task = Task(
            name=sanitize_input(form.name.data),
            description=sanitize_input(form.description.data) if form.description.data else None,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            task_type_id=form.task_type_id.data if form.task_type_id.data else None,
            status=form.status.data,
            priority=form.priority.data,
            use_stock=form.use_stock.data,
            justification=sanitize_input(form.justification.data) if form.justification.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            project_id=project_id
        )
        
        # Ajouter le personnel assigné
        if form.assigned_personnel.data:
            selected_personnel = Personnel.query.filter(Personnel.id.in_(form.assigned_personnel.data)).all()
            task.assigned_personnel.extend(selected_personnel)
        
        # Ajouter les groupes assignés
        if form.assigned_groups.data:
            selected_groups = Group.query.filter(Group.id.in_(form.assigned_groups.data)).all()
            task.assigned_groups.extend(selected_groups)
        
        db.session.add(task)
        db.session.commit()
        
        flash(f'Tâche {task.name} créée avec succès!', 'success')
        return redirect(url_for('projects.view_task', task_id=task.id))
    
    # Définir les dates par défaut
    if not form.start_date.data:
        form.start_date.data = date.today()
    if not form.end_date.data:
        form.end_date.data = date.today()
    
    return render_template('projects/task_form_standalone.html',
                         title='Créer une tâche',
                         form=form,
                         projects=active_projects)


@bp.route('/tasks/<int:task_id>/materials')
@login_required
@permission_required('tasks', 'read')
def task_materials(task_id):
    """Gestion des matériaux d'une tâche"""
    task = Task.query.get_or_404(task_id)
    
    # Récupérer tous les éléments de stock
    all_stock_items = StockItem.query.order_by(StockItem.libelle).all()
    
    # Récupérer les catégories et fournisseurs pour les filtres
    from app.models import StockCategory, Supplier
    categories = StockCategory.query.all()
    suppliers = Supplier.query.all()
    
    # Récupérer les items de stock de la tâche
    stock_items = task.stock_items.all()
    
    # Calculer les listes directement dans la route
    sufficient_items = []
    shortage_items = []
    return_items = []
    
    for item in stock_items:
        # Vérifier si la quantité est suffisante
        if item.stock_item and item.estimated_quantity <= item.stock_item.quantity:
            sufficient_items.append(item)
        else:
            shortage_items.append(item)
        
        # Vérifier si l'item doit être retourné au stock
        if item.return_to_stock:
            return_items.append(item)
    
    return render_template('projects/task_materials.html',
                         title=f'Matériaux - {task.name}',
                         task=task,
                         stock_items=stock_items,
                         sufficient_items=sufficient_items,
                         shortage_items=shortage_items,
                         return_items=return_items,
                         all_stock_items=all_stock_items,
                         categories=categories,
                         suppliers=suppliers)

@bp.route('/tasks/<int:task_id>/materials/add', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def add_stock_item(task_id):
    """Ajouter un élément de stock à une tâche"""
    task = Task.query.get_or_404(task_id)
    
    stock_item_id = request.form.get('stock_item_id')
    estimated_quantity = float(request.form.get('estimated_quantity', 0))
    unit_type = request.form.get('unit_type', 'piece')
    return_to_stock = request.form.get('return_to_stock') == 'on'
    justification_shortage = sanitize_input(request.form.get('justification_shortage', ''))
    notes = sanitize_input(request.form.get('notes', ''))
    
    stock_item = StockItem.query.get(stock_item_id)
    if not stock_item:
        flash('Matériau non trouvé.', 'danger')
        return redirect(url_for('projects.task_materials', task_id=task.id))
    
    # Vérifier la disponibilité
    is_sufficient = estimated_quantity <= stock_item.quantity
    
    task_stock_item = TaskStockItem(
        task_id=task.id,
        stock_item_id=stock_item_id,
        estimated_quantity=estimated_quantity,
        unit_type=unit_type,
        return_to_stock=return_to_stock,
        justification_shortage=justification_shortage if not is_sufficient else None,
        notes=notes
    )
    
    db.session.add(task_stock_item)
    db.session.commit()
    
    if not is_sufficient:
        flash(f'Matériau ajouté avec alerte: stock insuffisant!', 'warning')
    else:
        flash('Matériau ajouté avec succès.', 'success')
    
    return redirect(url_for('projects.task_materials', task_id=task.id))

@bp.route('/tasks/materials/<int:item_id>/edit', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def edit_stock_item(item_id):
    """Modifier un élément de stock d'une tâche"""
    task_stock_item = TaskStockItem.query.get_or_404(item_id)
    task = task_stock_item.task
    
    stock_item_id = request.form.get('stock_item_id')
    estimated_quantity = float(request.form.get('estimated_quantity', 0))
    unit_type = request.form.get('unit_type', 'piece')
    actual_quantity_used = request.form.get('actual_quantity_used')
    remaining_quantity = request.form.get('remaining_quantity')
    return_to_stock = request.form.get('return_to_stock') == 'on'
    justification_shortage = sanitize_input(request.form.get('justification_shortage', ''))
    notes = sanitize_input(request.form.get('notes', ''))
    
    stock_item = StockItem.query.get(stock_item_id)
    if not stock_item:
        flash('Matériau non trouvé.', 'danger')
        return redirect(url_for('projects.task_materials', task_id=task.id))
    
    # Mettre à jour
    task_stock_item.stock_item_id = stock_item_id
    task_stock_item.estimated_quantity = estimated_quantity
    task_stock_item.unit_type = unit_type
    task_stock_item.return_to_stock = return_to_stock
    task_stock_item.justification_shortage = justification_shortage
    task_stock_item.notes = notes
    
    if actual_quantity_used:
        task_stock_item.actual_quantity_used = float(actual_quantity_used)
    if remaining_quantity:
        task_stock_item.remaining_quantity = float(remaining_quantity)
    
    task_stock_item.updated_at = datetime.utcnow()
    
    # Vérifier la disponibilité
    is_sufficient = estimated_quantity <= stock_item.quantity
    if is_sufficient and task_stock_item.justification_shortage:
        task_stock_item.justification_shortage = None  # Nettoyer si maintenant suffisant
    
    db.session.commit()
    
    flash('Matériau mis à jour avec succès.', 'success')
    return redirect(url_for('projects.task_materials', task_id=task.id))

@bp.route('/tasks/materials/<int:item_id>/justify-shortage', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def justify_shortage(item_id):
    """Justifier un manque de stock"""
    task_stock_item = TaskStockItem.query.get_or_404(item_id)
    task = task_stock_item.task
    
    shortage_quantity = float(request.form.get('shortage_quantity', 0))
    justification = sanitize_input(request.form.get('justification', ''))
    urgent = request.form.get('urgent') == 'on'
    
    if not justification:
        flash('La justification est obligatoire.', 'danger')
        return redirect(url_for('projects.task_materials', task_id=task.id))
    
    task_stock_item.justification_shortage = f"""
    Quantité manquante: {shortage_quantity}
    Urgent: {'Oui' if urgent else 'Non'}
    Justification: {justification}
    Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """
    
    # Créer une notification pour les gestionnaires
    notification = Notification(
        title=f'Manque de stock pour {task.name}',
        message=f'Le matériau {task_stock_item.stock_item.libelle} nécessite {shortage_quantity} unités supplémentaires. Justification: {justification}',
        notification_type='stock_shortage',
        user_id=current_user.id,
        task_id=task.id,
        stock_item_id=task_stock_item.stock_item_id
    )
    db.session.add(notification)
    
    db.session.commit()
    
    flash('Justificatif enregistré et notification envoyée.', 'success')
    return redirect(url_for('projects.task_materials', task_id=task.id))

@bp.route('/api/update-actual-quantity', methods=['POST'])
@login_required
def update_actual_quantity():
    """API pour mettre à jour la quantité réellement utilisée"""
    data = request.get_json()
    item_id = data.get('item_id')
    actual_quantity_used = data.get('actual_quantity_used')
    
    task_stock_item = TaskStockItem.query.get(item_id)
    if not task_stock_item:
        return jsonify({'success': False, 'error': 'Élément non trouvé'})
    
    task_stock_item.actual_quantity_used = float(actual_quantity_used)
    task_stock_item.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/api/update-remaining-quantity', methods=['POST'])
@login_required
def update_remaining_quantity():
    """API pour mettre à jour la quantité restante"""
    data = request.get_json()
    item_id = data.get('item_id')
    remaining_quantity = data.get('remaining_quantity')
    
    task_stock_item = TaskStockItem.query.get(item_id)
    if not task_stock_item:
        return jsonify({'success': False, 'error': 'Élément non trouvé'})
    
    task_stock_item.remaining_quantity = float(remaining_quantity)
    task_stock_item.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/tasks/<int:task_id>/use-stock', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def use_stock(task_id):
    """Utiliser le stock pour une tâche (diminuer les quantités)"""
    task = Task.query.get_or_404(task_id)
    
    if not task.use_stock:
        return jsonify({'success': False, 'error': 'Cette tâche n\'utilise pas le stock'})
    
    # Vérifier d'abord la disponibilité
    insufficient_items = []
    for item in task.stock_items:
        if item.stock_item and item.actual_quantity_used:
            if item.actual_quantity_used > item.stock_item.quantity:
                insufficient_items.append({
                    'name': item.stock_item.libelle,
                    'needed': item.actual_quantity_used,
                    'available': item.stock_item.quantity
                })
    
    if insufficient_items:
        return jsonify({
            'success': False,
            'error': 'Stock insuffisant',
            'insufficient_items': insufficient_items
        })
    
    # Diminuer le stock et retourner les restes
    for item in task.stock_items:
        if item.stock_item and item.actual_quantity_used:
            # Diminuer la quantité utilisée
            item.stock_item.quantity -= item.actual_quantity_used
            
            # Retourner la quantité restante si applicable
            if item.return_to_stock and item.remaining_quantity:
                item.stock_item.quantity += item.remaining_quantity
            
            # Recalculer la valeur
            item.stock_item.calculate_value()
    
    db.session.commit()
    
    flash('Stock mis à jour avec succès.', 'success')
    return jsonify({'success': True})

@bp.route('/tasks/materials/<int:item_id>/delete', methods=['POST'])
@login_required
@permission_required('tasks', 'delete')
def delete_stock_item(item_id):
    """Supprimer un élément de stock d'une tâche"""
    task_stock_item = TaskStockItem.query.get_or_404(item_id)
    task_id = task_stock_item.task_id
    
    db.session.delete(task_stock_item)
    db.session.commit()
    
    flash('Matériau supprimé de la tâche.', 'success')
    return redirect(url_for('projects.task_materials', task_id=task_id))

@bp.route('/tasks/<int:task_id>/materials/add-batch', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def add_stock_items_batch(task_id):
    """Ajouter plusieurs éléments de stock à une tâche en une fois"""
    task = Task.query.get_or_404(task_id)
    
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        for item_data in items:
            stock_item = StockItem.query.get(item_data['stock_item_id'])
            if not stock_item:
                continue
            
            # Vérifier la disponibilité
            is_sufficient = float(item_data['estimated_quantity']) <= stock_item.quantity
            
            task_stock_item = TaskStockItem(
                task_id=task.id,
                stock_item_id=item_data['stock_item_id'],
                estimated_quantity=item_data['estimated_quantity'],
                unit_type=item_data.get('unit_type', 'piece'),
                return_to_stock=item_data.get('return_to_stock', True),
                justification_shortage=None if is_sufficient else 'Manque de stock - justificatif à fournir',
                notes=item_data.get('notes', '')
            )
            
            db.session.add(task_stock_item)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Matériaux ajoutés avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/submit-additional-request', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def submit_additional_request():
    """Soumettre une demande supplémentaire de matériaux"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        additional_quantity = data.get('additional_quantity')
        justification = data.get('justification')
        request_type = data.get('request_type', 'urgent')
        
        task_stock_item = TaskStockItem.query.get_or_404(item_id)
        
        # Créer une notification pour la demande supplémentaire
        notification = Notification(
            title=f'Demande supplémentaire pour {task_stock_item.task.name}',
            message=f'''
            Matériau: {task_stock_item.stock_item.libelle} ({task_stock_item.stock_item.reference})
            Quantité supplémentaire demandée: {additional_quantity} {task_stock_item.unit_type}
            Type: {request_type}
            Justification: {justification}
            Tâche: {task_stock_item.task.name}
            ''',
            notification_type='additional_request',
            user_id=current_user.id,
            task_id=task_stock_item.task_id,
            stock_item_id=task_stock_item.stock_item_id
        )
        
        # Ajouter une note à l'item
        current_notes = task_stock_item.notes or ''
        task_stock_item.notes = f"{current_notes}\n\n[DEMANDE SUPPLÉMENTAIRE - {datetime.now().strftime('%d/%m/%Y %H:%M')}]\nQuantité: +{additional_quantity}\nJustification: {justification}\nType: {request_type}"
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Demande envoyée avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/update-additional-quantity', methods=['POST'])
@login_required
def update_additional_quantity():
    """API pour mettre à jour la quantité supplémentaire"""
    data = request.get_json()
    item_id = data.get('item_id')
    additional_quantity = data.get('additional_quantity')
    
    task_stock_item = TaskStockItem.query.get(item_id)
    if not task_stock_item:
        return jsonify({'success': False, 'error': 'Élément non trouvé'})
    
    task_stock_item.additional_quantity = float(additional_quantity)
    task_stock_item.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/tasks/<int:task_id>/materials/check-stock', methods=['GET'])
@login_required
def check_task_stock_availability(task_id):
    """Vérifier la disponibilité du stock pour tous les matériaux de la tâche"""
    task = Task.query.get_or_404(task_id)
    
    issues = []
    for item in task.stock_items:
        if item.stock_item and item.estimated_quantity > item.stock_item.quantity:
            shortage = item.estimated_quantity - item.stock_item.quantity
            issues.append({
                'item': item.stock_item.libelle,
                'reference': item.stock_item.reference,
                'required': item.estimated_quantity,
                'available': item.stock_item.quantity,
                'shortage': shortage
            })
    
    return jsonify({
        'all_available': len(issues) == 0,
        'issues': issues,
        'total_shortage': sum(issue['shortage'] for issue in issues)
    })

# ============================================================================
# ROUTES API POUR GESTION DES MATÉRIAUX - SOLUTION OPTIMALE
# ============================================================================

@bp.route('/api/get-material/<int:item_id>')
@login_required
@permission_required('tasks', 'read')
def get_material(item_id):
    """Récupère les détails d'un matériau pour le modal d'édition"""
    try:
        task_stock_item = TaskStockItem.query.get_or_404(item_id)
        stock_item = StockItem.query.get(task_stock_item.stock_item_id)
        
        return jsonify({
            'success': True,
            'item': {
                'id': task_stock_item.id,
                'estimated_quantity': float(task_stock_item.estimated_quantity),
                'actual_quantity_used': float(task_stock_item.actual_quantity_used) if task_stock_item.actual_quantity_used else None,
                'remaining_quantity': float(task_stock_item.remaining_quantity) if task_stock_item.remaining_quantity else 0,
                'additional_quantity': float(task_stock_item.additional_quantity) if task_stock_item.additional_quantity else 0,
                'return_to_stock': bool(task_stock_item.return_to_stock),
                'justification_shortage': task_stock_item.justification_shortage or '',
                'notes': task_stock_item.notes or '',
                'unit_type': task_stock_item.unit_type or 'piece'
            },
            'stock_item': {
                'id': stock_item.id if stock_item else None,
                'libelle': stock_item.libelle if stock_item else 'N/A',
                'reference': stock_item.reference if stock_item else '',
                'quantity': float(stock_item.quantity) if stock_item else 0
            } if stock_item else None
        })
        
    except Exception as e:
        current_app.logger.error(f'Erreur get_material: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/update-material-full', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def update_material_full():
    """Mise à jour complète d'un matériau (via modal)"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({'success': False, 'error': 'ID manquant'}), 400
        
        task_stock_item = TaskStockItem.query.get_or_404(item_id)
        task = Task.query.get(task_stock_item.task_id)
        
        # Vérifier que la tâche est modifiable
        if not task or task.status == 'completed':
            return jsonify({'success': False, 'error': 'Tâche non modifiable (terminée)'}), 403
        
        # Validation des quantités
        estimated = float(task_stock_item.estimated_quantity)
        actual = float(data.get('actual_quantity_used', 0) or 0)
        additional = float(data.get('additional_quantity', 0) or 0)
        remaining = float(data.get('remaining_quantity', 0) or 0)
        
        # Vérifications logiques
        if actual > estimated + additional:
            return jsonify({
                'success': False,
                'error': 'La quantité utilisée ne peut pas dépasser la quantité estimée + additionnelle'
            }), 400
        
        if remaining > estimated + additional:
            return jsonify({
                'success': False,
                'error': 'Le reste ne peut pas dépasser la quantité totale disponible'
            }), 400
        
        # Mise à jour des champs
        task_stock_item.actual_quantity_used = actual if actual > 0 else None
        task_stock_item.remaining_quantity = remaining if remaining > 0 else None
        task_stock_item.additional_quantity = additional if additional > 0 else None
        task_stock_item.return_to_stock = bool(data.get('return_to_stock', False))
        task_stock_item.justification_shortage = sanitize_input(data.get('justification_shortage')) if data.get('justification_shortage') else None
        task_stock_item.notes = sanitize_input(data.get('notes')) if data.get('notes') else None
        task_stock_item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Modifications enregistrées avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur update_material_full: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


# Route unifiée pour mise à jour inline (remplace les 3 routes séparées)
@bp.route('/api/update-material-field', methods=['POST'])
@login_required
@permission_required('tasks', 'update')
def update_material_field():
    """Mise à jour rapide d'un champ (inline editing)"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([item_id, field]) or value is None:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        # Vérifier les champs autorisés
        allowed_fields = ['actual_quantity_used', 'remaining_quantity', 'additional_quantity']
        if field not in allowed_fields:
            return jsonify({'success': False, 'error': 'Champ non autorisé'}), 403
        
        # Récupérer l'item
        task_stock_item = TaskStockItem.query.get_or_404(item_id)
        task = Task.query.get(task_stock_item.task_id)
        
        # Vérifier que la tâche est modifiable
        if not task or task.status == 'completed':
            return jsonify({'success': False, 'error': 'Tâche non modifiable (terminée)'}), 403
        
        # Convertir et valider la valeur
        try:
            float_value = float(value)
            if float_value < 0:
                return jsonify({'success': False, 'error': 'La valeur ne peut pas être négative'}), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'Valeur numérique invalide'}), 400
        
        # Mise à jour spécifique selon le champ
        if field == 'actual_quantity_used':
            # Vérifier que la quantité utilisée ne dépasse pas l'estimée + additionnelle
            max_allowed = float(task_stock_item.estimated_quantity) + float(task_stock_item.additional_quantity or 0)
            if float_value > max_allowed:
                return jsonify({
                    'success': False, 
                    'error': f'La quantité utilisée ne peut pas dépasser {max_allowed}'
                }), 400
            
            task_stock_item.actual_quantity_used = float_value
            
            # Auto-calculer le reste si retour au stock est activé
            if task_stock_item.return_to_stock:
                estimated = float(task_stock_item.estimated_quantity) + float(task_stock_item.additional_quantity or 0)
                used = float_value
                task_stock_item.remaining_quantity = max(0, estimated - used)
        
        elif field == 'remaining_quantity':
            max_remaining = float(task_stock_item.estimated_quantity) + float(task_stock_item.additional_quantity or 0)
            if float_value > max_remaining:
                return jsonify({
                    'success': False,
                    'error': f'Le reste ne peut pas dépasser {max_remaining}'
                }), 400
            task_stock_item.remaining_quantity = float_value
        
        elif field == 'additional_quantity':
            task_stock_item.additional_quantity = float_value
        
        task_stock_item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mise à jour effectuée',
            'value': float_value,
            'remaining_quantity': float(task_stock_item.remaining_quantity) if task_stock_item.remaining_quantity else 0,
            'auto_calculated': field == 'actual_quantity_used' and task_stock_item.return_to_stock
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur update_material_field: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500