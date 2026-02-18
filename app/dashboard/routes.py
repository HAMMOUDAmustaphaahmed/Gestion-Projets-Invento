# app/dashboard/routes.py

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.dashboard import bp
from app.dashboard.forms import DashboardChartForm
from app.models import (DashboardChart, StockItem, Project, Task, Personnel, User, 
                       StockCategory, Notification, Supplier, Client, TaskType,
                       StockMovement, PurchaseOrder, Group, AdditionalCost)
from app import db
from app.decorators import permission_required
from app.utils import sanitize_input, format_date
import json
from datetime import datetime, timedelta
from sqlalchemy import func, extract, case, and_, or_

@bp.route('/')
@login_required
@permission_required('dashboard', 'read')
def index():
    """Tableau de bord principal optimisé"""
    # Récupérer les graphiques de l'utilisateur
    charts = DashboardChart.query.filter_by(
        user_id=current_user.id, is_active=True
    ).order_by(DashboardChart.position).all()
    
    # Statistiques globales complètes
    stats = get_comprehensive_stats()
    
    # Dernières activités
    recent_activities = get_recent_activities()
    
    # Projets actifs
    active_projects = Project.query.filter_by(
        status='in_progress'
    ).order_by(Project.created_at.desc()).limit(5).all()
    
    # Notifications non lues
    unread_notifications = current_user.notifications.filter_by(is_read=False).count()
    
    return render_template('dashboard/index.html',
                         title='Tableau de Bord',
                         charts=charts,
                         stats=stats,
                         recent_activities=recent_activities,
                         active_projects=active_projects,
                         unread_notifications=unread_notifications)

@bp.route('/custom')
@login_required
@permission_required('dashboard', 'read')
def custom():
    """Personnalisation du tableau de bord"""
    charts = DashboardChart.query.filter_by(
        user_id=current_user.id
    ).order_by(DashboardChart.position).all()
    
    form = DashboardChartForm()
    
    return render_template('dashboard/custom.html',
                         title='Personnalisation du Dashboard',
                         charts=charts,
                         form=form)

@bp.route('/charts/add', methods=['GET', 'POST'])
@login_required
@permission_required('dashboard', 'create')
def add_chart():
    """Ajouter un graphique au tableau de bord"""
    form = DashboardChartForm()
    
    if form.validate_on_submit():
        try:
            title = sanitize_input(form.title.data)
            
            last_position = db.session.query(func.max(DashboardChart.position)).filter_by(
                user_id=current_user.id
            ).scalar() or 0
            
            chart = DashboardChart(
                title=title,
                chart_type=form.chart_type.data,
                data_source=form.data_source.data,
                user_id=current_user.id,
                position=last_position + 1,
                is_active=request.form.get('add_to_dashboard') == 'on'
            )
            
            config = {
                'width': request.form.get('width', 6),
                'height': request.form.get('height', 300)
            }
            chart.set_config(config)
            
            db.session.add(chart)
            db.session.commit()
            
            flash(f'Graphique "{title}" créé avec succès!', 'success')
            
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'id': chart.id})
            
            return redirect(url_for('dashboard.custom'))
            
        except Exception as e:
            db.session.rollback()
            
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)}), 400
            
            flash(f'Erreur lors de la création du graphique: {str(e)}', 'danger')
            return redirect(url_for('dashboard.custom'))
    
    if request.method == 'POST':
        errors = {field: errors[0] for field, errors in form.errors.items()}
        
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'errors': errors}), 400
    
    return render_template('dashboard/chart_form.html',
                         title='Ajouter un graphique',
                         form=form)

@bp.route('/charts/<int:chart_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('dashboard', 'update')
def edit_chart(chart_id):
    """Modifier un graphique"""
    chart = DashboardChart.query.get_or_404(chart_id)
    
    if chart.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard.custom'))
    
    form = DashboardChartForm(obj=chart)
    
    if form.validate_on_submit():
        try:
            chart.title = sanitize_input(form.title.data)
            chart.chart_type = form.chart_type.data
            chart.data_source = form.data_source.data
            
            db.session.commit()
            
            flash(f'Graphique "{chart.title}" mis à jour avec succès!', 'success')
            return redirect(url_for('dashboard.custom'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'danger')
    
    return render_template('dashboard/chart_form.html',
                         title='Modifier le graphique',
                         form=form,
                         chart=chart)

@bp.route('/charts/<int:chart_id>/delete', methods=['POST'])
@login_required
def delete_chart(chart_id):
    """Supprimer un graphique"""
    chart = DashboardChart.query.get_or_404(chart_id)
    
    if chart.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Accès non autorisé.'}), 403
    
    db.session.delete(chart)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/charts/<int:chart_id>/toggle', methods=['POST'])
@login_required
def toggle_chart(chart_id):
    """Activer/désactiver un graphique"""
    chart = DashboardChart.query.get_or_404(chart_id)
    
    if chart.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Accès non autorisé.'}), 403
    
    chart.is_active = not chart.is_active
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': chart.is_active})

@bp.route('/charts/update-order', methods=['POST'])
@login_required
def update_chart_order():
    """Mettre à jour l'ordre des graphiques"""
    try:
        data = request.get_json()
        order = data.get('order', [])
        
        for position, chart_id in enumerate(order):
            chart = DashboardChart.query.get(chart_id)
            if chart and chart.user_id == current_user.id:
                chart.position = position
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/api/chart-data/<int:chart_id>')
@login_required
def chart_data(chart_id):
    """Récupérer les données d'un graphique"""
    chart = DashboardChart.query.get_or_404(chart_id)
    
    if chart.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Accès non autorisé.'}), 403
    
    try:
        data = generate_chart_data(chart)
        
        return jsonify({
            'success': True,
            'data': data,
            'config': chart.get_config()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def generate_chart_data(chart):
    """Générer les données d'un graphique"""
    
    if chart.data_source == 'stock':
        items = StockItem.query.order_by(StockItem.quantity.desc()).limit(10).all()
        return {
            'labels': [item.reference for item in items],
            'datasets': [{
                'label': 'Quantité en stock',
                'data': [float(item.quantity) for item in items],
                'backgroundColor': '#667eea',
                'borderColor': '#667eea',
                'borderWidth': 2
            }]
        }
        
    elif chart.data_source == 'stock_value':
        items = StockItem.query.order_by(StockItem.value.desc()).limit(10).all()
        return {
            'labels': [item.reference for item in items],
            'datasets': [{
                'label': 'Valeur (TND)',
                'data': [float(item.value) for item in items],
                'backgroundColor': '#764ba2',
                'borderColor': '#764ba2',
                'borderWidth': 2
            }]
        }
        
    elif chart.data_source == 'projects':
        projects = Project.query.limit(10).all()
        return {
            'labels': [p.name[:20] for p in projects],
            'datasets': [{
                'label': 'Budget estimé (TND)',
                'data': [float(p.estimated_budget or 0) for p in projects],
                'backgroundColor': '#f093fb',
                'borderColor': '#f5576c',
                'borderWidth': 2
            }]
        }
        
    elif chart.data_source == 'tasks':
        tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
        return {
            'labels': [t.name[:20] for t in tasks],
            'datasets': [{
                'label': 'Progression (%)',
                'data': [100 if t.status == 'completed' else 50 if t.status == 'in_progress' else 0 for t in tasks],
                'backgroundColor': '#4facfe',
                'borderColor': '#00f2fe',
                'borderWidth': 2
            }]
        }
        
    elif chart.data_source == 'personnel':
        personnel = Personnel.query.filter_by(is_active=True).all()
        dept_counts = {}
        for p in personnel:
            dept = p.department or 'Non assigné'
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        return {
            'labels': list(dept_counts.keys()),
            'datasets': [{
                'label': 'Personnel par département',
                'data': list(dept_counts.values()),
                'backgroundColor': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
            }]
        }
        
    elif chart.data_source == 'stock_by_category':
        categories = db.session.query(
            StockCategory.name,
            func.count(StockItem.id).label('count')
        ).join(StockItem, StockCategory.id == StockItem.category_id, isouter=True) \
         .group_by(StockCategory.id, StockCategory.name).all()
        
        return {
            'labels': [cat[0] or 'Non catégorisé' for cat in categories],
            'datasets': [{
                'label': "Nombre d'éléments",
                'data': [cat[1] for cat in categories],
                'backgroundColor': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
            }]
        }
        
    elif chart.data_source == 'project_status':
        status_counts = db.session.query(
            Project.status,
            func.count(Project.id).label('count')
        ).group_by(Project.status).all()
        
        status_labels = {
            'planning': 'Planification',
            'in_progress': 'En cours',
            'completed': 'Terminé',
            'cancelled': 'Annulé'
        }
        
        return {
            'labels': [status_labels.get(status, status) for status, count in status_counts],
            'datasets': [{
                'label': 'Nombre de projets',
                'data': [count for status, count in status_counts],
                'backgroundColor': ['#ffd89b', '#4facfe', '#43e97b', '#fa709a']
            }]
        }
        
    elif chart.data_source == 'task_status':
        status_counts = db.session.query(
            Task.status,
            func.count(Task.id).label('count')
        ).group_by(Task.status).all()
        
        status_labels = {
            'pending': 'En attente',
            'in_progress': 'En cours',
            'completed': 'Terminée',
            'cancelled': 'Annulée'
        }
        
        return {
            'labels': [status_labels.get(status, status) for status, count in status_counts],
            'datasets': [{
                'label': 'Nombre de tâches',
                'data': [count for status, count in status_counts],
                'backgroundColor': ['#a8edea', '#4facfe', '#43e97b', '#fa709a']
            }]
        }
        
    elif chart.data_source == 'monthly_costs':
        today = datetime.now()
        months = []
        costs = []
        
        for i in range(6, 0, -1):
            month = today - timedelta(days=30*i)
            month_start = month.replace(day=1)
            
            if i > 1:
                next_month = (month_start + timedelta(days=32)).replace(day=1)
            else:
                next_month = today
            
            cost = db.session.query(func.sum(Task.actual_cost)).filter(
                Task.created_at >= month_start,
                Task.created_at < next_month
            ).scalar() or 0
            
            months.append(month_start.strftime('%b %Y'))
            costs.append(float(cost))
        
        return {
            'labels': months,
            'datasets': [{
                'label': 'Coûts mensuels (TND)',
                'data': costs,
                'backgroundColor': 'rgba(102, 126, 234, 0.2)',
                'borderColor': '#667eea',
                'borderWidth': 3,
                'fill': True,
                'tension': 0.4
            }]
        }
    
    elif chart.data_source == 'suppliers':
        suppliers = Supplier.query.limit(10).all()
        supplier_counts = []
        
        for supplier in suppliers:
            count = StockItem.query.filter_by(supplier_id=supplier.id).count()
            supplier_counts.append({
                'name': supplier.name,
                'count': count
            })
        
        supplier_counts.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'labels': [s['name'][:20] for s in supplier_counts[:8]],
            'datasets': [{
                'label': 'Articles fournis',
                'data': [s['count'] for s in supplier_counts[:8]],
                'backgroundColor': '#667eea'
            }]
        }
    
    elif chart.data_source == 'clients':
        clients = Client.query.filter_by(is_active=True).limit(10).all()
        client_projects = []
        
        for client in clients:
            count = Project.query.filter_by(client_id=client.id).count()
            client_projects.append({
                'name': client.name,
                'count': count
            })
        
        client_projects.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'labels': [c['name'][:20] for c in client_projects[:8]],
            'datasets': [{
                'label': 'Projets par client',
                'data': [c['count'] for c in client_projects[:8]],
                'backgroundColor': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
            }]
        }
    
    else:
        return {
            'labels': ['Aucune donnée'],
            'datasets': [{
                'label': 'Pas de données',
                'data': [0],
                'backgroundColor': '#6c757d'
            }]
        }

def get_comprehensive_stats():
    """Récupérer toutes les statistiques complètes"""
    today = datetime.now().date()
    
    # Stats de base
    stats = {
        # Stock
        'total_stock_items': StockItem.query.count(),
        'stock_alerts': StockItem.query.filter(
            StockItem.quantity <= StockItem.min_quantity,
            StockItem.min_quantity > 0
        ).count(),
        'total_stock_value': float(db.session.query(func.sum(StockItem.value)).scalar() or 0),
        'stock_categories': StockCategory.query.count(),
        
        # Projets
        'total_projects': Project.query.count(),
        'active_projects': Project.query.filter_by(status='in_progress').count(),
        'completed_projects': Project.query.filter_by(status='completed').count(),
        'planning_projects': Project.query.filter_by(status='planning').count(),
        'total_project_budget': float(db.session.query(func.sum(Project.estimated_budget)).scalar() or 0),
        'total_project_cost': float(db.session.query(func.sum(Project.actual_cost)).scalar() or 0),
        
        # Tâches
        'total_tasks': Task.query.count(),
        'pending_tasks': Task.query.filter_by(status='pending').count(),
        'in_progress_tasks': Task.query.filter_by(status='in_progress').count(),
        'completed_tasks': Task.query.filter_by(status='completed').count(),
        'overdue_tasks': Task.query.filter(
            Task.end_date < today,
            Task.status.in_(['pending', 'in_progress'])
        ).count(),
        
        # Personnel
        'total_personnel': Personnel.query.filter_by(is_active=True).count(),
        'total_groups': Group.query.count(),
        
        # Utilisateurs
        'total_users': User.query.filter_by(is_active=True).count(),
        
        # Fournisseurs et Clients
        'total_suppliers': Supplier.query.count(),
        'total_clients': Client.query.filter_by(is_active=True).count(),
        
        # Stats du jour
        'tasks_completed_today': Task.query.filter(
            Task.actual_end_date == today,
            Task.status == 'completed'
        ).count(),
        
        # Stats du mois
        'monthly_tasks': Task.query.filter(
            extract('month', Task.created_at) == today.month,
            extract('year', Task.created_at) == today.year
        ).count(),
        'monthly_projects': Project.query.filter(
            extract('month', Project.created_at) == today.month,
            extract('year', Project.created_at) == today.year
        ).count(),
    }
    
    # Calcul du taux de complétion des projets
    if stats['total_projects'] > 0:
        stats['project_completion_rate'] = round((stats['completed_projects'] / stats['total_projects']) * 100, 1)
    else:
        stats['project_completion_rate'] = 0
    
    # Calcul du taux de complétion des tâches
    if stats['total_tasks'] > 0:
        stats['task_completion_rate'] = round((stats['completed_tasks'] / stats['total_tasks']) * 100, 1)
    else:
        stats['task_completion_rate'] = 0
    
    return stats

def get_recent_activities():
    """Récupérer les activités récentes (optimisé)"""
    activities = []
    
    # Derniers éléments de stock ajoutés
    recent_stock = StockItem.query.order_by(StockItem.created_at.desc()).limit(3).all()
    for item in recent_stock:
        activities.append({
            'type': 'primary',
            'icon': 'box-seam',
            'title': f'Nouvel élément: {item.reference}',
            'description': item.libelle,
            'date': item.created_at
        })
    
    # Derniers projets créés
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(2).all()
    for project in recent_projects:
        activities.append({
            'type': 'success',
            'icon': 'kanban',
            'title': f'Nouveau projet: {project.name}',
            'description': f'Budget: {project.estimated_budget} TND',
            'date': project.created_at
        })
    
    # Dernières tâches créées
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(2).all()
    for task in recent_tasks:
        activities.append({
            'type': 'info',
            'icon': 'list-task',
            'title': f'Nouvelle tâche: {task.name}',
            'description': f'Projet: {task.project.name if task.project else "N/A"}',
            'date': task.created_at
        })
    
    # Trier par date
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    return activities[:8]

@bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats_api():
    """API pour les statistiques du dashboard"""
    stats = get_comprehensive_stats()
    return jsonify(stats)

@bp.route('/api/recent-activities')
@login_required
def recent_activities_api():
    """API pour les activités récentes"""
    activities = get_recent_activities()
    
    formatted = []
    for activity in activities:
        formatted.append({
            'type': activity['type'],
            'icon': activity['icon'],
            'title': activity['title'],
            'description': activity['description'],
            'time': format_time_ago(activity['date'])
        })
    
    return jsonify({'success': True, 'activities': formatted})

def format_time_ago(dt):
    """Formate une date en 'il y a ...'"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f'il y a {years} an{"s" if years > 1 else ""}'
    elif diff.days > 30:
        months = diff.days // 30
        return f'il y a {months} mois'
    elif diff.days > 0:
        return f'il y a {diff.days} jour{"s" if diff.days > 1 else ""}'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'il y a {hours} heure{"s" if hours > 1 else ""}'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'il y a {minutes} minute{"s" if minutes > 1 else ""}'
    else:
        return "à l'instant"