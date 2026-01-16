/**
 * CALENDAR.JS - Version Améliorée
 * Gestion complète du calendrier avec affichage des tâches et projets
 */

$(document).ready(function() {
    // Variables globales
    let calendar;
    let currentFilters = {
        project: 'all',
        status: 'all',
        priority: ['high', 'medium', 'low'],
        personnel: [],
        dateFrom: null,
        dateTo: null
    };

    // Initialisation
    initCalendar();
    loadStatistics();
    loadUpcomingEvents();
    initStatsChart();
    setupEventHandlers();
});

/**
 * Initialisation du calendrier FullCalendar
 */
function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'fr',
        firstDay: 1, // Lundi
        timeZone: 'Europe/Paris',
        headerToolbar: false, // On utilise notre propre toolbar
        initialView: 'dayGridMonth',
        height: 'auto',
        contentHeight: 650,
        aspectRatio: 2,
        expandRows: true,
        navLinks: true,
        editable: false, // Désactivé pour éviter les modifications accidentelles
        selectable: false,
        dayMaxEvents: true,
        nowIndicator: true,
        
        // Source des événements
        events: function(fetchInfo, successCallback, failureCallback) {
            loadCalendarEvents(fetchInfo, successCallback, failureCallback);
        },
        
        // Clic sur un événement
        eventClick: function(info) {
            info.jsEvent.preventDefault();
            handleEventClick(info.event);
        },
        
        // Rendu de l'événement
        eventDidMount: function(info) {
            setupEventTooltip(info);
        },
        
        // Changement de dates
        datesSet: function(info) {
            updateCalendarTitle(info);
        },
        
        // Style des événements
        eventClassNames: function(arg) {
            return getEventClasses(arg.event);
        }
    });

    calendar.render();
    window.calendar = calendar;
    
    console.log('✓ Calendrier initialisé avec succès');
}

/**
 * Charge les événements du calendrier
 */
function loadCalendarEvents(fetchInfo, successCallback, failureCallback) {
    const params = new URLSearchParams({
        start: fetchInfo.start.toISOString().split('T')[0],
        end: fetchInfo.end.toISOString().split('T')[0],
        project: currentFilters.project || 'all',
        status: currentFilters.status || 'all'
    });

    $.ajax({
        url: '/calendar/events?' + params.toString(),
        type: 'GET',
        success: function(events) {
            console.log(`✓ ${events.length} événements chargés`);
            successCallback(events);
            updateStatistics(events);
        },
        error: function(xhr, status, error) {
            console.error('✗ Erreur chargement événements:', error);
            showToast('error', 'Erreur lors du chargement des événements');
            if (failureCallback) failureCallback(error);
        }
    });
}

/**
 * Configure le tooltip pour un événement
 */
function setupEventTooltip(info) {
    const event = info.event;
    const props = event.extendedProps;
    
    // Créer le contenu du tooltip
    let tooltipContent = '';
    
    if (props.type === 'task') {
        tooltipContent = `
            <div class="text-start">
                <strong>${event.title}</strong><br>
                <small>📁 ${props.project_name}</small><br>
                <small>📅 ${formatDate(event.start)} → ${formatDate(event.end)}</small><br>
                <small>📊 ${props.status_text}</small><br>
                <small>⚡ ${props.priority_text}</small>
                ${props.assigned_personnel && props.assigned_personnel.length > 0 ? 
                    `<br><small>👤 ${props.assigned_personnel.map(p => p.name).join(', ')}</small>` 
                    : ''}
                ${props.description ? 
                    `<br><br><small>${truncateText(props.description, 100)}</small>` 
                    : ''}
            </div>
        `;
    } else if (props.type === 'project') {
        tooltipContent = `
            <div class="text-start">
                <strong>📁 Projet: ${event.title.replace('📁 ', '')}</strong><br>
                <small>📅 ${formatDate(event.start)} → ${formatDate(event.end)}</small><br>
                <small>📊 ${props.status}</small>
            </div>
        `;
    }
    
    // Initialiser le tooltip Bootstrap
    new bootstrap.Tooltip(info.el, {
        title: tooltipContent,
        html: true,
        placement: 'top',
        trigger: 'hover',
        container: 'body',
        customClass: 'custom-calendar-tooltip',
        boundary: 'window'
    });
    
    // Ajouter un effet de survol
    info.el.addEventListener('mouseenter', function() {
        this.style.zIndex = '1000';
    });
    
    info.el.addEventListener('mouseleave', function() {
        this.style.zIndex = '';
    });
}

/**
 * Gère le clic sur un événement
 */
function handleEventClick(event) {
    const props = event.extendedProps;
    
    if (props.type === 'task') {
        showTaskDetails(event.id);
    } else if (props.type === 'project') {
        // Rediriger vers la page du projet
        window.location.href = props.url;
    }
}

/**
 * Affiche les détails d'une tâche dans un modal
 */
function showTaskDetails(taskId) {
    $.ajax({
        url: `/calendar/task/${taskId}`,
        type: 'GET',
        success: function(task) {
            displayTaskModal(task);
        },
        error: function() {
            showToast('error', 'Impossible de charger les détails de la tâche');
        }
    });
}

/**
 * Affiche le modal des détails de la tâche
 */
function displayTaskModal(task) {
    const modal = $('#eventDetailsModal');
    
    const html = `
        <div class="modal-header">
            <h5 class="modal-title">
                <i class="bi bi-check-square me-2"></i>${task.name}
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            <!-- Informations principales -->
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong>Projet</strong>
                    <p><a href="${task.project.url}" class="text-decoration-none">
                        <i class="bi bi-folder me-1"></i>${task.project.name}
                    </a></p>
                </div>
                <div class="col-md-6">
                    <strong>Statut</strong>
                    <p><span class="badge bg-${getStatusColor(task.status)}">${task.status_text}</span></p>
                </div>
            </div>
            
            <!-- Dates -->
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Date de début</strong>
                    <p><i class="bi bi-calendar-event me-1"></i>${task.start_date}</p>
                </div>
                <div class="col-md-4">
                    <strong>Date de fin prévue</strong>
                    <p><i class="bi bi-calendar-check me-1"></i>${task.end_date}</p>
                </div>
                <div class="col-md-4">
                    <strong>Priorité</strong>
                    <p><span class="badge bg-${getPriorityColor(task.priority)}">${task.priority_text}</span></p>
                </div>
            </div>
            
            <!-- Description -->
            ${task.description ? `
            <div class="mb-3">
                <strong>Description</strong>
                <p class="text-muted">${task.description}</p>
            </div>
            ` : ''}
            
            <!-- Type de tâche -->
            ${task.task_type ? `
            <div class="mb-3">
                <strong>Type de tâche</strong>
                <p><span class="badge bg-secondary">${task.task_type}</span></p>
            </div>
            ` : ''}
            
            <!-- Personnel assigné -->
            ${task.assigned_personnel && task.assigned_personnel.length > 0 ? `
            <div class="mb-3">
                <strong>Personnel assigné</strong>
                <div class="d-flex flex-wrap gap-2 mt-2">
                    ${task.assigned_personnel.map(p => `
                        <div class="badge bg-light text-dark border">
                            <i class="bi bi-person me-1"></i>${p.name}
                            ${p.position ? `<small class="text-muted"> - ${p.position}</small>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <!-- Groupes assignés -->
            ${task.assigned_groups && task.assigned_groups.length > 0 ? `
            <div class="mb-3">
                <strong>Groupes assignés</strong>
                <div class="d-flex flex-wrap gap-2 mt-2">
                    ${task.assigned_groups.map(g => `
                        <div class="badge bg-info">
                            <i class="bi bi-people me-1"></i>${g.name}
                            <small>(${g.member_count} membres)</small>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <!-- Informations sur le stock -->
            ${task.use_stock ? `
            <div class="mb-3">
                <strong>Utilisation du stock</strong>
                <p>
                    <span class="badge bg-warning text-dark">
                        <i class="bi bi-box-seam me-1"></i>${task.stock_items_count} article(s)
                    </span>
                    <span class="badge bg-success ms-2">
                        <i class="bi bi-cash me-1"></i>Coût estimé: ${formatCurrency(task.total_cost)}
                    </span>
                </p>
            </div>
            ` : ''}
            
            <!-- Justification -->
            ${task.justification ? `
            <div class="mb-3">
                <strong>Justification</strong>
                <p class="text-muted">${task.justification}</p>
            </div>
            ` : ''}
            
            <!-- Notes -->
            ${task.notes ? `
            <div class="mb-3">
                <strong>Notes</strong>
                <p class="text-muted">${task.notes}</p>
            </div>
            ` : ''}
            
            <!-- Métadonnées -->
            <div class="row mt-4 pt-3 border-top">
                <div class="col-md-6">
                    <small class="text-muted">
                        <i class="bi bi-clock me-1"></i>Créé le ${task.created_at}
                    </small>
                </div>
                <div class="col-md-6 text-end">
                    <small class="text-muted">
                        <i class="bi bi-pencil me-1"></i>Modifié le ${task.updated_at || 'Jamais'}
                    </small>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <a href="/projects/tasks/${task.id}" class="btn btn-primary">
                <i class="bi bi-pencil me-2"></i>Modifier la tâche
            </a>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Fermer
            </button>
        </div>
    `;
    
    modal.find('.modal-content').html(html);
    modal.modal('show');
}

/**
 * Met à jour le titre du calendrier
 */
function updateCalendarTitle(info) {
    const start = info.start;
    const end = info.end;
    const viewType = info.view.type;
    
    let title = '';
    
    switch(viewType) {
        case 'dayGridMonth':
            title = start.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
            title = title.charAt(0).toUpperCase() + title.slice(1);
            break;
        case 'timeGridWeek':
            const weekEnd = new Date(end.getTime() - 86400000);
            title = `Semaine du ${formatDate(start)} au ${formatDate(weekEnd)}`;
            break;
        case 'timeGridDay':
            title = formatDate(start, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
            break;
        case 'listMonth':
            title = start.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
            title = title.charAt(0).toUpperCase() + title.slice(1);
            break;
    }
    
    $('#calendarTitle').text(title);
}

/**
 * Charge les statistiques
 */
function loadStatistics() {
    $.ajax({
        url: '/calendar/api/stats',
        type: 'GET',
        success: function(stats) {
            updateStatsDisplay(stats);
            updateStatsChart(stats);
        },
        error: function() {
            console.error('✗ Erreur chargement statistiques');
        }
    });
}

/**
 * Met à jour l'affichage des statistiques
 */
function updateStatsDisplay(stats) {
    $('#totalEvents').text(stats.total || 0);
    $('#upcomingEvents').text(stats.upcoming || 0);
    $('#overdueEvents').text(stats.overdue || 0);
    $('#completedEvents').text(stats.completed || 0);
}

/**
 * Met à jour les statistiques depuis les événements
 */
function updateStatistics(events) {
    const now = new Date();
    const weekFromNow = new Date(now.getTime() + 7 * 86400000);
    
    const taskEvents = events.filter(e => e.extendedProps && e.extendedProps.type === 'task');
    
    const stats = {
        total: taskEvents.length,
        upcoming: taskEvents.filter(e => {
            const start = new Date(e.start);
            return start > now && start <= weekFromNow && e.extendedProps.status !== 'completed';
        }).length,
        overdue: taskEvents.filter(e => {
            const end = new Date(e.end || e.start);
            return end < now && e.extendedProps.status === 'in_progress';
        }).length,
        completed: taskEvents.filter(e => e.extendedProps.status === 'completed').length
    };
    
    updateStatsDisplay(stats);
    updateStatsChart(stats);
}

/**
 * Initialise le graphique des statistiques
 */
function initStatsChart() {
    const ctx = document.getElementById('calendarStatsChart');
    if (!ctx) return;
    
    window.statsChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Terminées', 'En cours', 'En retard', 'À venir'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ['#28a745', '#0d6efd', '#dc3545', '#ffc107'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Met à jour le graphique des statistiques
 */
function updateStatsChart(stats) {
    if (window.statsChart) {
        const inProgress = Math.max(0, stats.total - stats.completed - stats.overdue - stats.upcoming);
        
        window.statsChart.data.datasets[0].data = [
            stats.completed || 0,
            inProgress || 0,
            stats.overdue || 0,
            stats.upcoming || 0
        ];
        window.statsChart.update();
    }
}

/**
 * Charge les événements à venir
 */
function loadUpcomingEvents() {
    $.ajax({
        url: '/calendar/api/upcoming-events',
        type: 'GET',
        success: function(events) {
            displayUpcomingEvents(events);
        },
        error: function() {
            console.error('✗ Erreur chargement événements à venir');
        }
    });
}

/**
 * Affiche les événements à venir
 */
function displayUpcomingEvents(events) {
    const container = $('#upcomingEventsList');
    
    if (events.length === 0) {
        container.html(`
            <div class="text-center py-5">
                <i class="bi bi-calendar-check text-muted" style="font-size: 3rem;"></i>
                <p class="text-muted mt-3">Aucun événement à venir dans les 30 prochains jours</p>
            </div>
        `);
        return;
    }
    
    let html = '<div class="list-group list-group-flush">';
    
    events.forEach(event => {
        const daysLeft = event.days_remaining;
        let badgeClass = 'secondary';
        let badgeIcon = 'calendar';
        
        if (daysLeft === 0) {
            badgeClass = 'danger';
            badgeIcon = 'exclamation-circle';
        } else if (daysLeft <= 3) {
            badgeClass = 'warning';
            badgeIcon = 'clock';
        } else if (daysLeft <= 7) {
            badgeClass = 'info';
            badgeIcon = 'calendar-week';
        }
        
        html += `
            <a href="${event.url}" class="list-group-item list-group-item-action py-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <i class="bi bi-check-square me-1 text-primary"></i>${event.title}
                        </h6>
                        <p class="text-muted small mb-2">
                            <i class="bi bi-folder me-1"></i>${event.project}
                        </p>
                        <div class="d-flex align-items-center gap-2 flex-wrap">
                            <span class="badge bg-${getStatusColor(event.status)}">${event.status}</span>
                            <span class="badge bg-${getPriorityColor(event.priority)}">${event.priority}</span>
                            <small class="text-muted">
                                <i class="bi bi-calendar me-1"></i>${event.start_date} → ${event.end_date}
                            </small>
                        </div>
                    </div>
                    <div class="text-end ms-3">
                        <div class="badge bg-${badgeClass} p-2">
                            <i class="bi bi-${badgeIcon} me-1"></i>
                            ${daysLeft === 0 ? "Aujourd'hui" : `${daysLeft}j`}
                        </div>
                    </div>
                </div>
            </a>
        `;
    });
    
    html += '</div>';
    container.html(html);
}

/**
 * Configure les gestionnaires d'événements
 */
function setupEventHandlers() {
    // Navigation
    $('#prevBtn').on('click', () => calendar.prev());
    $('#nextBtn').on('click', () => calendar.next());
    $('#todayBtn').on('click', () => {
        calendar.today();
        $('.calendar-view-btn').removeClass('active');
        $('.calendar-view-btn[data-view="dayGridMonth"]').addClass('active');
    });
    
    // Changement de vue
    $('.calendar-view-btn').on('click', function() {
        const view = $(this).data('view');
        calendar.changeView(view);
        $('.calendar-view-btn').removeClass('active');
        $(this).addClass('active');
    });
    
    // Filtres
    $('#applyFilters').on('click', applyFilters);
    $('#resetFilters').on('click', resetFilters);
    
    // Recherche
    let searchTimeout;
    $('#calendarSearch').on('keyup', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => searchTasks(query), 300);
        } else {
            calendar.refetchEvents();
        }
    });
    
    $('#clearSearch').on('click', function() {
        $('#calendarSearch').val('');
        calendar.refetchEvents();
    });
    
    // Actions rapides
    $('#viewTodayTasks').on('click', () => {
        calendar.today();
        calendar.changeView('timeGridDay');
        $('.calendar-view-btn').removeClass('active');
        $('.calendar-view-btn[data-view="timeGridDay"]').addClass('active');
    });
    
    $('#viewOverdueTasks').on('click', () => {
        currentFilters.status = 'in_progress';
        calendar.refetchEvents();
        showToast('warning', 'Affichage des tâches en retard');
    });
    
    $('#viewUpcomingTasks').on('click', () => {
        const today = new Date();
        const nextWeek = new Date(today.getTime() + 7 * 86400000);
        calendar.gotoDate(nextWeek);
        calendar.changeView('timeGridWeek');
        $('.calendar-view-btn').removeClass('active');
        $('.calendar-view-btn[data-view="timeGridWeek"]').addClass('active');
    });
    
    // Actualiser
    $('#refreshCalendar').on('click', () => {
        calendar.refetchEvents();
        loadStatistics();
        loadUpcomingEvents();
        showToast('success', 'Calendrier actualisé');
    });
    
    // Export & Impression
    $('#exportCalendar').on('click', () => $('#exportModal').modal('show'));
    $('#printCalendar').on('click', () => window.print());
}

/**
 * Applique les filtres
 */
function applyFilters() {
    currentFilters.project = $('#projectFilter').val() || 'all';
    currentFilters.status = $('#statusFilter').val() || 'all';
    
    calendar.refetchEvents();
    showToast('success', 'Filtres appliqués');
}

/**
 * Réinitialise les filtres
 */
function resetFilters() {
    $('#projectFilter').val('all');
    $('#statusFilter').val('all');
    $('#calendarSearch').val('');
    
    currentFilters = {
        project: 'all',
        status: 'all',
        priority: ['high', 'medium', 'low'],
        personnel: [],
        dateFrom: null,
        dateTo: null
    };
    
    calendar.refetchEvents();
    showToast('info', 'Filtres réinitialisés');
}

/**
 * Recherche de tâches
 */
function searchTasks(query) {
    $.ajax({
        url: '/calendar/api/search',
        type: 'GET',
        data: { q: query },
        success: function(tasks) {
            if (tasks.length > 0) {
                highlightSearchResults(tasks);
                showToast('info', `${tasks.length} résultat(s) trouvé(s)`);
            } else {
                showToast('warning', 'Aucun résultat');
            }
        }
    });
}

/**
 * Surligne les résultats de recherche
 */
function highlightSearchResults(tasks) {
    const taskIds = tasks.map(t => t.id.toString());
    
    calendar.getEvents().forEach(event => {
        if (event.extendedProps.type === 'task' && taskIds.includes(event.id)) {
            event.setProp('classNames', [...event.classNames, 'fc-event-highlighted']);
        }
    });
}

/**
 * Fonctions utilitaires
 */

function getEventClasses(event) {
    const classes = [];
    const props = event.extendedProps;
    
    if (props.type === 'task') {
        classes.push('fc-event-task');
        
        // Statut
        if (props.status === 'completed') classes.push('fc-event-completed');
        else if (props.status === 'cancelled') classes.push('fc-event-cancelled');
        else if (props.status === 'in_progress') classes.push('fc-event-in-progress');
        
        // Priorité
        if (props.priority === 'high') classes.push('fc-event-high-priority');
        else if (props.priority === 'medium') classes.push('fc-event-medium-priority');
        else if (props.priority === 'low') classes.push('fc-event-low-priority');
        
        // En retard
        const now = new Date();
        const end = new Date(event.end || event.start);
        if (end < now && props.status in ['pending', 'in_progress']) {
            classes.push('fc-event-overdue');
        }
    } else if (props.type === 'project') {
        classes.push('fc-event-project');
    }
    
    return classes;
}

function getStatusColor(status) {
    const colors = {
        'pending': 'secondary',
        'planning': 'info',
        'in_progress': 'primary',
        'completed': 'success',
        'cancelled': 'danger'
    };
    return colors[status] || 'secondary';
}

function getPriorityColor(priority) {
    const colors = {
        'high': 'danger',
        'medium': 'warning',
        'low': 'info'
    };
    return colors[priority] || 'secondary';
}

function formatDate(date, options = { day: 'numeric', month: 'short', year: 'numeric' }) {
    return new Date(date).toLocaleDateString('fr-FR', options);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'TND',
        minimumFractionDigits: 3
    }).format(amount || 0);
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function showToast(type, message) {
    if (!$('#toastContainer').length) {
        $('body').append('<div id="toastContainer" class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
    }
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-secondary';
    
    const toast = $(`
        <div class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);
    
    $('#toastContainer').append(toast);
    const bsToast = new bootstrap.Toast(toast[0], { delay: 3000 });
    bsToast.show();
    
    toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// Log de démarrage
console.log('✓ Module Calendar chargé');