from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.calendar import bp
from app.models import Task, Project, Personnel, Group
from app.decorators import permission_required
from app import db
from datetime import datetime, timedelta

@bp.route('/')
@login_required
@permission_required('calendar', 'read')
def index():
    """Page principale du calendrier"""
    try:
        projects = Project.query.order_by(Project.name).all()
        personnel = Personnel.query.filter_by(is_active=True).order_by(Personnel.first_name).all()
        
        return render_template('calendar/index.html', 
                             title='Calendrier',
                             projects=projects,
                             personnel=personnel)
    except Exception as e:
        print(f"Erreur dans calendar.index: {str(e)}")
        return render_template('errors/500.html'), 500


@bp.route('/events')
@login_required
def events():
    """API pour les événements du calendrier (FullCalendar)"""
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        project_filter = request.args.get('project', 'all')
        status_filter = request.args.get('status', 'all')
        
        print(f"Chargement événements: start={start}, end={end}, project={project_filter}, status={status_filter}")
        
        # Requête de base
        query = Task.query.options(
            db.joinedload(Task.project),
            db.joinedload(Task.assigned_personnel),
            db.joinedload(Task.task_type_ref)
        )
        
        # Filtrer par période
        if start and end:
            try:
                start_date = datetime.strptime(start, '%Y-%m-%d').date()
                end_date = datetime.strptime(end, '%Y-%m-%d').date()
                query = query.filter(
                    db.or_(
                        db.and_(Task.start_date <= end_date, Task.end_date >= start_date),
                        db.and_(Task.start_date >= start_date, Task.start_date <= end_date)
                    )
                )
            except ValueError as ve:
                print(f"Erreur de format de date: {ve}")
        
        # Filtrer par projet
        if project_filter and project_filter != 'all':
            try:
                query = query.filter(Task.project_id == int(project_filter))
            except ValueError:
                pass
        
        # Filtrer par statut
        if status_filter and status_filter != 'all':
            query = query.filter(Task.status == status_filter)
        
        tasks = query.all()
        print(f"Nombre de tâches trouvées: {len(tasks)}")
        
        # Formater les événements
        events = []
        for task in tasks:
            try:
                color = get_task_color(task)
                
                event = {
                    'id': str(task.id),
                    'title': task.name,
                    'start': task.start_date.isoformat(),
                    'end': (task.end_date + timedelta(days=1)).isoformat() if task.end_date else (task.start_date + timedelta(days=1)).isoformat(),
                    'allDay': True,
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#ffffff',
                    'classNames': get_task_classes(task),
                    'extendedProps': {
                        'type': 'task',
                        'project_id': task.project_id,
                        'project_name': task.project.name,
                        'status': task.status,
                        'status_text': get_status_text(task.status),
                        'priority': task.priority,
                        'priority_text': get_priority_text(task.priority),
                        'description': task.description or '',
                        'task_type': task.task_type_ref.name if task.task_type_ref else '',
                        'assigned_personnel': [
                            {'id': p.id, 'name': p.get_full_name()} 
                            for p in task.assigned_personnel
                        ]
                    }
                }
                events.append(event)
            except Exception as e:
                print(f"Erreur formatage tâche {task.id}: {str(e)}")
                continue
        
        print(f"Événements formatés: {len(events)}")
        return jsonify(events)
        
    except Exception as e:
        print(f"Erreur dans /calendar/events: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify([])


@bp.route('/task/<int:task_id>')
@login_required
def task_details(task_id):
    """Détails d'une tâche pour le modal"""
    try:
        task = Task.query.get_or_404(task_id)
        
        data = {
            'id': task.id,
            'name': task.name,
            'description': task.description or '',
            'start_date': task.start_date.strftime('%d/%m/%Y'),
            'end_date': task.end_date.strftime('%d/%m/%Y') if task.end_date else '',
            'status': task.status,
            'status_text': get_status_text(task.status),
            'priority': task.priority,
            'priority_text': get_priority_text(task.priority),
            'project': {
                'id': task.project.id,
                'name': task.project.name,
                'url': f'/projects/{task.project.id}'
            },
            'task_type': task.task_type_ref.name if task.task_type_ref else '',
            'assigned_personnel': [{
                'id': p.id,
                'name': p.get_full_name(),
                'url': f'/personnel/view/{p.id}'
            } for p in task.assigned_personnel],
            'assigned_groups': [{
                'id': g.id,
                'name': g.name,
                'member_count': len(g.members),
                'url': f'/personnel/groups/{g.id}/edit'
            } for g in task.assigned_groups],
            'notes': task.notes or '',
            'created_at': task.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': task.updated_at.strftime('%d/%m/%Y %H:%M') if task.updated_at else ''
        }
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Erreur dans /calendar/task/{task_id}: {str(e)}")
        return jsonify({'error': 'Tâche non trouvée'}), 404

@bp.route('/api/events-by-range')
@login_required
def events_by_range():
    """API pour les événements par plage de dates (pour les vues semaine/jour)"""
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        
        print(f"Chargement événements par plage: start={start}, end={end}")
        
        if not start or not end:
            return jsonify([])
        
        query = Task.query.options(
            db.joinedload(Task.project),
            db.joinedload(Task.assigned_personnel),
            db.joinedload(Task.task_type_ref)
        )
        
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
            query = query.filter(
                db.or_(
                    db.and_(Task.start_date <= end_date, Task.end_date >= start_date),
                    db.and_(Task.start_date >= start_date, Task.start_date <= end_date)
                )
            )
        except ValueError as ve:
            print(f"Erreur de format de date: {ve}")
            return jsonify([])
        
        tasks = query.order_by(Task.start_date).all()
        
        # Formater les événements
        events = []
        for task in tasks:
            try:
                color = get_task_color(task)
                
                event = {
                    'id': str(task.id),
                    'title': task.name,
                    'start': task.start_date.isoformat(),
                    'end': (task.end_date + timedelta(days=1)).isoformat() if task.end_date else (task.start_date + timedelta(days=1)).isoformat(),
                    'allDay': True,
                    'backgroundColor': color,
                    'borderColor': color,
                    'textColor': '#ffffff',
                    'classNames': get_task_classes(task),
                    'extendedProps': {
                        'type': 'task',
                        'project_id': task.project_id,
                        'project_name': task.project.name,
                        'status': task.status,
                        'status_text': get_status_text(task.status),
                        'priority': task.priority,
                        'priority_text': get_priority_text(task.priority),
                        'description': task.description or '',
                        'task_type': task.task_type_ref.name if task.task_type_ref else '',
                        'assigned_personnel': [
                            {'id': p.id, 'name': p.get_full_name()} 
                            for p in task.assigned_personnel
                        ]
                    }
                }
                events.append(event)
            except Exception as e:
                print(f"Erreur formatage tâche {task.id}: {str(e)}")
                continue
        
        return jsonify(events)
        
    except Exception as e:
        print(f"Erreur dans /calendar/api/events-by-range: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify([])
        
@bp.route('/api/stats')
@login_required
def calendar_stats():
    """Statistiques pour le calendrier"""
    try:
        today = datetime.now().date()
        
        total_tasks = Task.query.count()
        
        # Tâches en cours (in_progress)
        in_progress_tasks = Task.query.filter_by(status='in_progress').count()
        
        # Tâches terminées (completed)
        completed_tasks = Task.query.filter_by(status='completed').count()
        
        # Tâches en retard (date de fin passée et statut pas terminé)
        overdue_tasks = Task.query.filter(
            Task.end_date < today,
            Task.status.in_(['pending', 'planning', 'in_progress'])
        ).count()
        
        stats = {
            'total': total_tasks,
            'completed': completed_tasks,
            'in_progress': in_progress_tasks,
            'overdue': overdue_tasks
        }
        
        print(f"Stats calculées: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"Erreur dans /calendar/api/stats: {str(e)}")
        return jsonify({'total': 0, 'completed': 0, 'in_progress': 0, 'overdue': 0})

@bp.route('/api/upcoming-events')
@login_required
def upcoming_events():
    """Événements à venir (30 prochains jours)"""
    try:
        today = datetime.now().date()
        end_date = today + timedelta(days=30)
        
        print(f"🔍 Recherche d'événements à venir: {today} -> {end_date}")
        
        # Debug: afficher la requête
        tasks = Task.query.filter(
            Task.start_date <= end_date,
            Task.end_date >= today,
            Task.status.in_(['pending', 'in_progress'])
        ).order_by(Task.start_date).limit(10).all()
        
        print(f"📋 Tâches trouvées: {len(tasks)}")
        
        events = []
        for task in tasks:
            days_remaining = (task.start_date - today).days if task.start_date > today else 0
            
            events.append({
                'id': task.id,
                'title': task.name,
                'project': task.project.name if task.project else 'Sans projet',
                'start_date': task.start_date.strftime('%d/%m/%Y'),
                'end_date': task.end_date.strftime('%d/%m/%Y'),
                'status': task.status,
                'priority': task.priority,
                'days_remaining': days_remaining,
                'url': f'/projects/tasks/{task.id}'
            })
        
        print(f"✅ Événements à venir formatés: {len(events)}")
        return jsonify(events)
        
    except Exception as e:
        print(f"❌ Erreur dans /calendar/api/upcoming-events: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@bp.route('/api/search')
@login_required
def search_tasks():
    """Recherche de tâches"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify([])
        
        tasks = Task.query.filter(
            db.or_(
                Task.name.ilike(f'%{query}%'),
                Task.description.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results = []
        for task in tasks:
            results.append({
                'id': task.id,
                'title': task.name,
                'start': task.start_date.isoformat(),
                'end': task.end_date.isoformat() if task.end_date else task.start_date.isoformat(),
                'project_name': task.project.name,
                'status': task.status
            })
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Erreur dans /calendar/api/search: {str(e)}")
        return jsonify([])


# Fonctions utilitaires

def get_task_color(task):
    """Retourne la couleur d'une tâche selon priorité et statut"""
    if task.status == 'completed':
        return '#28a745'
    elif task.status == 'cancelled':
        return '#6c757d'
    elif task.status == 'in_progress':
        if task.priority == 'high':
            return '#dc3545'
        elif task.priority == 'medium':
            return '#fd7e14'
        else:
            return '#17a2b8'
    else:  # pending
        if task.priority == 'high':
            return '#e83e8c'
        elif task.priority == 'medium':
            return '#ffc107'
        else:
            return '#007bff'


def get_task_classes(task):
    """Retourne les classes CSS pour une tâche"""
    classes = ['fc-event-task']
    
    if task.priority:
        classes.append(f'fc-event-{task.priority}')
    
    if task.status:
        classes.append(f'fc-event-{task.status}')
    
    return classes


def get_status_text(status):
    """Convertit le code de statut en texte"""
    statuses = {
        'pending': 'En attente',
        'planning': 'Planification',
        'in_progress': 'En cours',
        'completed': 'Terminé',
        'cancelled': 'Annulé'
    }
    return statuses.get(status, status)


def get_priority_text(priority):
    """Convertit le code de priorité en texte"""
    priorities = {
        'high': 'Haute',
        'medium': 'Moyenne',
        'low': 'Basse'
    }
    return priorities.get(priority, priority)