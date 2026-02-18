from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.personnel import bp
from app.personnel.forms import PersonnelForm
from app.groups.forms import GroupForm  # Changement ici: importer depuis app.groups.forms
from app.models import Personnel, Group, User, Task  # Ajout de Task
from app import db
from app.decorators import permission_required
from app.utils import sanitize_input
from datetime import datetime
import json
import csv
from io import StringIO

@bp.route('/')
@login_required
@permission_required('personnel', 'read')
def index():
    """Liste du personnel"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    is_active = request.args.get('is_active', 'true')
    
    # Construire la requête avec filtres
    query = Personnel.query
    
    if search:
        query = query.filter(
            db.or_(
                Personnel.first_name.ilike(f'%{search}%'),
                Personnel.last_name.ilike(f'%{search}%'),
                Personnel.employee_id.ilike(f'%{search}%')
            )
        )
    
    if department:
        query = query.filter_by(department=department)
    
    if is_active.lower() == 'true':
        query = query.filter_by(is_active=True)
    elif is_active.lower() == 'false':
        query = query.filter_by(is_active=False)
    
    # Pagination
    personnel_list = query.order_by(Personnel.last_name, Personnel.first_name).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    # Liste des départements uniques
    departments = db.session.query(Personnel.department).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    # Calculer les statistiques
    stats = {
        'active': Personnel.query.filter_by(is_active=True).count(),
        'groups_count': Group.query.count()
    }
    
    return render_template('personnel/index.html',
                         title='Gestion du Personnel',
                         personnel_list=personnel_list,
                         departments=departments,
                         search=search,
                         selected_department=department,
                         is_active=is_active,
                         stats=stats)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('personnel', 'create')
def add():
    """Ajouter un membre du personnel"""
    form = PersonnelForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        personnel = Personnel(
            employee_id=sanitize_input(form.employee_id.data),
            first_name=sanitize_input(form.first_name.data),
            last_name=sanitize_input(form.last_name.data),
            email=sanitize_input(form.email.data) if form.email.data else None,
            phone=sanitize_input(form.phone.data) if form.phone.data else None,
            department=sanitize_input(form.department.data) if form.department.data else None,
            position=sanitize_input(form.position.data) if form.position.data else None,
            hire_date=form.hire_date.data,
            address=sanitize_input(form.address.data) if form.address.data else None,
            city=sanitize_input(form.city.data) if form.city.data else None,
            country=sanitize_input(form.country.data) if form.country.data else None,
            emergency_contact=sanitize_input(form.emergency_contact.data) if form.emergency_contact.data else None,
            emergency_phone=sanitize_input(form.emergency_phone.data) if form.emergency_phone.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            is_active=form.is_active.data
        )
        
        db.session.add(personnel)
        db.session.commit()
        
        flash(f'Personnel {personnel.get_full_name()} ajouté avec succès!', 'success')
        return redirect(url_for('personnel.index'))
    
    return render_template('personnel/form.html',
                         title='Ajouter un membre du personnel',
                         form=form)

@bp.route('/edit/<int:personnel_id>', methods=['GET', 'POST'])
@login_required
@permission_required('personnel', 'update')
def edit(personnel_id):
    """Modifier un membre du personnel"""
    personnel = Personnel.query.get_or_404(personnel_id)
    form = PersonnelForm()
    
    if form.validate_on_submit():
        # Nettoyer les entrées
        personnel.employee_id = sanitize_input(form.employee_id.data)
        personnel.first_name = sanitize_input(form.first_name.data)
        personnel.last_name = sanitize_input(form.last_name.data)
        personnel.email = sanitize_input(form.email.data) if form.email.data else None
        personnel.phone = sanitize_input(form.phone.data) if form.phone.data else None
        personnel.department = sanitize_input(form.department.data) if form.department.data else None
        personnel.position = sanitize_input(form.position.data) if form.position.data else None
        personnel.hire_date = form.hire_date.data
        personnel.address = sanitize_input(form.address.data) if form.address.data else None
        personnel.city = sanitize_input(form.city.data) if form.city.data else None
        personnel.country = sanitize_input(form.country.data) if form.country.data else None
        personnel.emergency_contact = sanitize_input(form.emergency_contact.data) if form.emergency_contact.data else None
        personnel.emergency_phone = sanitize_input(form.emergency_phone.data) if form.emergency_phone.data else None
        personnel.notes = sanitize_input(form.notes.data) if form.notes.data else None
        personnel.is_active = form.is_active.data
        
        db.session.commit()
        
        flash(f'Personnel {personnel.get_full_name()} mis à jour avec succès!', 'success')
        return redirect(url_for('personnel.index'))
    
    # Pré-remplir le formulaire
    form.employee_id.data = personnel.employee_id
    form.first_name.data = personnel.first_name
    form.last_name.data = personnel.last_name
    form.email.data = personnel.email
    form.phone.data = personnel.phone
    form.department.data = personnel.department
    form.position.data = personnel.position
    form.hire_date.data = personnel.hire_date
    form.address.data = personnel.address
    form.city.data = personnel.city
    form.country.data = personnel.country
    form.emergency_contact.data = personnel.emergency_contact
    form.emergency_phone.data = personnel.emergency_phone
    form.notes.data = personnel.notes
    form.is_active.data = personnel.is_active
    
    return render_template('personnel/form.html',
                         title='Modifier un membre du personnel',
                         form=form, personnel=personnel)

@bp.route('/delete/<int:personnel_id>', methods=['POST'])
@login_required
@permission_required('personnel', 'delete')
def delete(personnel_id):
    """Supprimer un membre du personnel"""
    personnel = Personnel.query.get_or_404(personnel_id)
    
    # Vérifier si le personnel est assigné à des tâches ou groupes
    if personnel.tasks.count() > 0 or personnel.groups.count() > 0:
        flash('Impossible de supprimer ce membre du personnel car il est assigné à des tâches ou groupes.', 'danger')
        return redirect(url_for('personnel.index'))
    
    db.session.delete(personnel)
    db.session.commit()
    
    flash(f'Personnel {personnel.get_full_name()} supprimé avec succès.', 'success')
    return redirect(url_for('personnel.index'))

@bp.route('/view/<int:personnel_id>')
@login_required
@permission_required('personnel', 'read')
def view(personnel_id):
    """Voir les détails d'un membre du personnel"""
    personnel = Personnel.query.get_or_404(personnel_id)
    
    # Récupérer les tâches assignées
    assigned_tasks = Task.query.filter(Task.assigned_personnel.contains(personnel)).order_by(Task.start_date.desc()).limit(10).all()
    
    return render_template('personnel/view.html',
                         title=f'Personnel - {personnel.get_full_name()}',
                         personnel=personnel,
                         assigned_tasks=assigned_tasks)

@bp.route('/api/personnel-list', methods=['GET'])
@login_required
def personnel_list_api():
    """API pour la liste du personnel (AJAX)"""
    search = request.args.get('search', '')
    
    query = Personnel.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Personnel.first_name.ilike(f'%{search}%'),
                Personnel.last_name.ilike(f'%{search}%')
            )
        )
    
    personnel = query.order_by(Personnel.last_name).limit(20).all()
    
    results = []
    for p in personnel:
        results.append({
            'id': p.id,
            'text': f"{p.get_full_name()} ({p.employee_id})",
            'name': p.get_full_name(),
            'employee_id': p.employee_id
        })
    
    return jsonify({'results': results})

@bp.route('/api/groups-list', methods=['GET'])
@login_required
def groups_list_api():
    """API pour la liste des groupes (AJAX)"""
    groups = Group.query.all()
    
    results = []
    for g in groups:
        results.append({
            'id': g.id,
            'text': g.name,
            'member_count': len(g.members)
        })
    
    return jsonify({'results': results})

@bp.route('/export', methods=['GET'])
@login_required
@permission_required('personnel', 'read')
def export():
    """Exporter la liste du personnel"""
    # Récupérer tous les membres du personnel
    personnel = Personnel.query.order_by(Personnel.last_name, Personnel.first_name).all()
    
    # Créer le fichier CSV en mémoire
    si = StringIO()
    csv_writer = csv.writer(si)
    
    # En-têtes
    csv_writer.writerow([
        'Matricule', 'Nom', 'Prénom', 'Email', 'Téléphone', 'Département',
        'Poste', 'Date d\'embauche', 'Ville', 'Pays', 'Actif'
    ])
    
    # Données
    for p in personnel:
        csv_writer.writerow([
            p.employee_id,
            p.last_name,
            p.first_name,
            p.email or '',
            p.phone or '',
            p.department or '',
            p.position or '',
            p.hire_date.strftime('%d/%m/%Y') if p.hire_date else '',
            p.city or '',
            p.country or '',
            'Oui' if p.is_active else 'Non'
        ])
    
    # Créer la réponse
    output = si.getvalue()
    si.close()
    
    response = current_app.response_class(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=personnel.csv'}
    )
    
    return response