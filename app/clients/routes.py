from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
from app.clients import bp
from app.clients.forms import ClientForm
from app.models import Client, Project
from app import db
from app.decorators import permission_required
from app.utils import sanitize_input
from datetime import datetime

@bp.route('/')
@login_required
@permission_required('projects', 'read')
def index():
    """Liste des clients"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Construire la requête avec filtres
    query = Client.query
    
    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f'%{search}%'),
                Client.company.ilike(f'%{search}%'),
                Client.email.ilike(f'%{search}%'),
                Client.contact_person.ilike(f'%{search}%')
            )
        )
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    # Pagination
    clients = query.order_by(Client.name).paginate(
        page=page, 
        per_page=current_app.config['ITEMS_PER_PAGE'], 
        error_out=False
    )
    
    # Statistiques
    stats = {
        'total': Client.query.count(),
        'active': Client.query.filter_by(is_active=True).count(),
        'inactive': Client.query.filter_by(is_active=False).count()
    }
    
    return render_template('clients/index.html',
                         title='Gestion des Clients',
                         clients=clients,
                         search=search,
                         selected_status=status,
                         stats=stats)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('projects', 'create')
def add():
    """Ajouter un client"""
    form = ClientForm()
    
    if form.validate_on_submit():
        client = Client(
            name=sanitize_input(form.name.data),
            company=sanitize_input(form.company.data) if form.company.data else None,
            contact_person=sanitize_input(form.contact_person.data) if form.contact_person.data else None,
            email=sanitize_input(form.email.data) if form.email.data else None,
            phone=sanitize_input(form.phone.data) if form.phone.data else None,
            address=sanitize_input(form.address.data) if form.address.data else None,
            city=sanitize_input(form.city.data) if form.city.data else None,
            postal_code=sanitize_input(form.postal_code.data) if form.postal_code.data else None,
            country=sanitize_input(form.country.data) if form.country.data else None,
            website=sanitize_input(form.website.data) if form.website.data else None,
            siret=sanitize_input(form.siret.data) if form.siret.data else None,
            notes=sanitize_input(form.notes.data) if form.notes.data else None,
            is_active=form.is_active.data
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash(f'Client {client.name} créé avec succès!', 'success')
        return redirect(url_for('clients.view', client_id=client.id))
    
    return render_template('clients/form.html',
                         title='Ajouter un client',
                         form=form)

@bp.route('/<int:client_id>')
@login_required
@permission_required('projects', 'read')
def view(client_id):
    """Voir les détails d'un client"""
    client = Client.query.get_or_404(client_id)
    
    # Récupérer les projets du client
    projects = client.projects.order_by(Project.start_date.desc()).all()
    
    # Statistiques des projets
    project_stats = {
        'total': len(projects),
        'planning': len([p for p in projects if p.status == 'planning']),
        'in_progress': len([p for p in projects if p.status == 'in_progress']),
        'completed': len([p for p in projects if p.status == 'completed']),
        'cancelled': len([p for p in projects if p.status == 'cancelled'])
    }
    
    # Budget total
    total_budget = sum(p.estimated_budget for p in projects)
    total_cost = sum(p.actual_cost for p in projects)
    
    return render_template('clients/view.html',
                         title=f'Client - {client.name}',
                         client=client,
                         projects=projects,
                         project_stats=project_stats,
                         total_budget=total_budget,
                         total_cost=total_cost)

@bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('projects', 'update')
def edit(client_id):
    """Modifier un client"""
    client = Client.query.get_or_404(client_id)
    form = ClientForm()
    
    if form.validate_on_submit():
        client.name = sanitize_input(form.name.data)
        client.company = sanitize_input(form.company.data) if form.company.data else None
        client.contact_person = sanitize_input(form.contact_person.data) if form.contact_person.data else None
        client.email = sanitize_input(form.email.data) if form.email.data else None
        client.phone = sanitize_input(form.phone.data) if form.phone.data else None
        client.address = sanitize_input(form.address.data) if form.address.data else None
        client.city = sanitize_input(form.city.data) if form.city.data else None
        client.postal_code = sanitize_input(form.postal_code.data) if form.postal_code.data else None
        client.country = sanitize_input(form.country.data) if form.country.data else None
        client.website = sanitize_input(form.website.data) if form.website.data else None
        client.siret = sanitize_input(form.siret.data) if form.siret.data else None
        client.notes = sanitize_input(form.notes.data) if form.notes.data else None
        client.is_active = form.is_active.data
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Client {client.name} mis à jour avec succès!', 'success')
        return redirect(url_for('clients.view', client_id=client.id))
    
    # Pré-remplir le formulaire
    form.name.data = client.name
    form.company.data = client.company
    form.contact_person.data = client.contact_person
    form.email.data = client.email
    form.phone.data = client.phone
    form.address.data = client.address
    form.city.data = client.city
    form.postal_code.data = client.postal_code
    form.country.data = client.country
    form.website.data = client.website
    form.siret.data = client.siret
    form.notes.data = client.notes
    form.is_active.data = client.is_active
    
    return render_template('clients/form.html',
                         title='Modifier un client',
                         form=form,
                         client=client)

@bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
@permission_required('projects', 'delete')
def delete(client_id):
    """Supprimer un client"""
    client = Client.query.get_or_404(client_id)
    
    # Vérifier si le client a des projets
    if client.projects.count() > 0:
        flash('Impossible de supprimer ce client car il a des projets associés.', 'danger')
        return redirect(url_for('clients.view', client_id=client.id))
    
    name = client.name
    db.session.delete(client)
    db.session.commit()
    
    flash(f'Client {name} supprimé avec succès.', 'success')
    return redirect(url_for('clients.index'))

@bp.route('/<int:client_id>/toggle-status', methods=['POST'])
@login_required
@permission_required('projects', 'update')
def toggle_status(client_id):
    """Activer/désactiver un client"""
    client = Client.query.get_or_404(client_id)
    
    client.is_active = not client.is_active
    client.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    status = 'activé' if client.is_active else 'désactivé'
    flash(f'Client {client.name} {status} avec succès.', 'success')
    
    return redirect(url_for('clients.view', client_id=client.id))

@bp.route('/api/clients', methods=['GET'])
@login_required
def api_clients():
    """API pour récupérer la liste des clients (pour Select2)"""
    search = request.args.get('q', '')
    active_only = request.args.get('active_only', 'true') == 'true'
    
    query = Client.query
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f'%{search}%'),
                Client.company.ilike(f'%{search}%')
            )
        )
    
    clients = query.order_by(Client.name).limit(50).all()
    
    results = [
        {
            'id': c.id,
            'text': f"{c.name}" + (f" ({c.company})" if c.company else "")
        }
        for c in clients
    ]
    
    return jsonify({'results': results})