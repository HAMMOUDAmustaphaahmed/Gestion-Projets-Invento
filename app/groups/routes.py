from flask import render_template, current_app, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.groups import bp
from app.groups.forms import GroupForm, GroupMembersForm
from app.models import Group, Personnel, Task
from app import db
from app.decorators import permission_required
from app.utils import sanitize_input


@bp.route('/')
@login_required
@permission_required('personnel', 'read')
def index():
    """Liste des groupes"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Group.query
    
    if search:
        query = query.filter(Group.name.ilike(f'%{search}%'))
    
    groups = query.order_by(Group.name).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 20), error_out=False
    )
    
    return render_template('groups/index.html',
                         title='Groupes',
                         groups=groups,
                         search=search)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('personnel', 'create')
def add():
    """Créer un nouveau groupe"""
    form = GroupForm()
    
    if form.validate_on_submit():
        name = sanitize_input(form.name.data)
        description = sanitize_input(form.description.data) if form.description.data else None
        
        existing = Group.query.filter_by(name=name).first()
        if existing:
            flash('Un groupe avec ce nom existe déjà.', 'danger')
            return redirect(url_for('groups.add'))
        
        group = Group(name=name, description=description)
        db.session.add(group)
        db.session.commit()
        
        flash(f'Groupe "{group.name}" créé avec succès!', 'success')
        return redirect(url_for('groups.view', group_id=group.id))
    
    return render_template('groups/form.html',
                         title='Créer un groupe',
                         form=form)


@bp.route('/<int:group_id>')
@login_required
@permission_required('personnel', 'read')
def view(group_id):
    """Voir les détails d'un groupe"""
    group = Group.query.get_or_404(group_id)
    
    assigned_tasks = Task.query.join(Task.assigned_groups)\
                                .filter(Group.id == group_id)\
                                .order_by(Task.start_date.desc())\
                                .limit(10)\
                                .all()
    
    return render_template('groups/view.html',
                         title=f'Groupe - {group.name}',
                         group=group,
                         assigned_tasks=assigned_tasks)


@bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('personnel', 'update')
def edit(group_id):
    """Modifier un groupe"""
    group = Group.query.get_or_404(group_id)
    form = GroupForm()
    
    if form.validate_on_submit():
        group.name = sanitize_input(form.name.data)
        group.description = sanitize_input(form.description.data) if form.description.data else None
        db.session.commit()
        
        flash(f'Groupe "{group.name}" mis à jour avec succès!', 'success')
        return redirect(url_for('groups.view', group_id=group.id))
    
    form.name.data = group.name
    form.description.data = group.description
    
    return render_template('groups/form.html',
                         title='Modifier un groupe',
                         form=form,
                         group=group)


@bp.route('/<int:group_id>/delete', methods=['POST'])
@login_required
@permission_required('personnel', 'delete')
def delete(group_id):
    """Supprimer un groupe"""
    group = Group.query.get_or_404(group_id)
    
    if group.tasks.count() > 0:
        flash('Impossible de supprimer ce groupe car il est assigné à des tâches.', 'danger')
        return redirect(url_for('groups.view', group_id=group_id))
    
    db.session.delete(group)
    db.session.commit()
    
    flash(f'Groupe "{group.name}" supprimé avec succès.', 'success')
    return redirect(url_for('groups.index'))


@bp.route('/<int:group_id>/members', methods=['GET', 'POST'])
@login_required
@permission_required('personnel', 'update')
def manage_members(group_id):
    """Gérer les membres d'un groupe (page traditionnelle - optionnel maintenant)"""
    group = Group.query.get_or_404(group_id)
    form = GroupMembersForm()
    
    available_members = Personnel.query.filter_by(is_active=True).all()
    form.members.choices = [(m.id, f"{m.get_full_name()} ({m.employee_id})") for m in available_members]
    
    if form.validate_on_submit():
        selected_members = Personnel.query.filter(Personnel.id.in_(form.members.data)).all()
        group.members = selected_members
        db.session.commit()
        
        flash(f'Membres du groupe "{group.name}" mis à jour avec succès!', 'success')
        return redirect(url_for('groups.view', group_id=group.id))
    
    form.members.data = [member.id for member in group.members]
    
    return render_template('groups/members.html',
                         title=f'Membres - {group.name}',
                         form=form,
                         group=group)


# ============================================================================
# ROUTES AJAX POUR GESTION DES MEMBRES VIA MODAL
# ============================================================================

@bp.route('/<int:group_id>/add-member-ajax', methods=['POST'])
@login_required
@permission_required('personnel', 'update')
def add_member_ajax(group_id):
    """Ajouter un membre au groupe via AJAX"""
    group = Group.query.get_or_404(group_id)
    personnel_id = request.form.get('personnel_id', type=int)
    
    if not personnel_id:
        return jsonify({'success': False, 'error': 'ID personnel manquant'})
    
    personnel = Personnel.query.get_or_404(personnel_id)
    
    if not personnel.is_active:
        return jsonify({'success': False, 'error': 'Ce personnel est inactif et ne peut pas être ajouté'})
    
    if personnel in group.members:
        return jsonify({'success': False, 'error': 'Ce personnel est déjà membre du groupe'})
    
    group.members.append(personnel)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{personnel.get_full_name()} ajouté au groupe',
        'member': {
            'id': personnel.id,
            'name': personnel.get_full_name(),
            'employee_id': personnel.employee_id,
            'department': personnel.department,
            'position': personnel.position
        }
    })


@bp.route('/<int:group_id>/remove-member-ajax', methods=['POST'])
@login_required
@permission_required('personnel', 'update')
def remove_member_ajax(group_id):
    """Retirer un membre du groupe via AJAX"""
    group = Group.query.get_or_404(group_id)
    personnel_id = request.form.get('personnel_id', type=int)
    
    if not personnel_id:
        return jsonify({'success': False, 'error': 'ID personnel manquant'})
    
    personnel = Personnel.query.get_or_404(personnel_id)
    
    if personnel not in group.members:
        return jsonify({'success': False, 'error': 'Ce personnel n\'est pas membre du groupe'})
    
    group.members.remove(personnel)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{personnel.get_full_name()} retiré du groupe',
        'member_id': personnel.id
    })


# ============================================================================
# ROUTES API
# ============================================================================

@bp.route('/<int:group_id>/tasks')
@login_required
@permission_required('tasks', 'read')
def group_tasks(group_id):
    """Tâches assignées à un groupe"""
    group = Group.query.get_or_404(group_id)
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Task.query.join(Task.assigned_groups).filter(Group.id == group_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.start_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('groups/tasks.html',
                         title=f'Tâches - {group.name}',
                         group=group,
                         tasks=tasks,
                         status=status)


@bp.route('/api/list', methods=['GET'])
@login_required
def groups_list_api():
    """API pour la liste des groupes (AJAX)"""
    search = request.args.get('search', '')
    
    query = Group.query
    
    if search:
        query = query.filter(Group.name.ilike(f'%{search}%'))
    
    groups = query.order_by(Group.name).limit(20).all()
    
    results = [{'id': g.id, 'text': g.name, 'member_count': len(g.members)} for g in groups]
    
    return jsonify({'results': results})


@bp.route('/api/<int:group_id>/members', methods=['GET'])
@login_required
def group_members_api(group_id):
    """API pour les membres d'un groupe"""
    group = Group.query.get_or_404(group_id)
    
    members = [{
        'id': m.id,
        'name': m.get_full_name(),
        'employee_id': m.employee_id,
        'department': m.department,
        'position': m.position
    } for m in group.members]
    
    return jsonify({'members': members})


@bp.route('/api/stats', methods=['GET'])
@login_required
def groups_stats():
    """Statistiques des groupes"""
    total_groups = Group.query.count()
    
    groups_with_member_count = db.session.query(
        Group.id,
        Group.name,
        db.func.count(Personnel.id).label('member_count')
    ).join(Group.members, isouter=True) \
     .group_by(Group.id) \
     .order_by(db.desc('member_count')) \
     .limit(5).all()
    
    stats = {
        'total_groups': total_groups,
        'top_groups': [{
            'id': g.id,
            'name': g.name,
            'member_count': g.member_count
        } for g in groups_with_member_count]
    }
    
    return jsonify(stats)