// Dashboard Ultra-Moderne - JavaScript Optimisé

$(document).ready(function() {
    // Initialiser le dashboard
    initializeDashboard();
    
    // Rafraîchissement automatique toutes les 5 minutes
    setInterval(refreshDashboardData, 300000);
    
    // Animation des compteurs au chargement
    animateCounters();
});

// Initialisation du dashboard
function initializeDashboard() {
    console.log('Dashboard initialisé');
    
    // Charger les données initiales
    loadDashboardStats();
    
    // Initialiser les tooltips Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Charger les statistiques du dashboard
function loadDashboardStats() {
    $.ajax({
        url: '/dashboard/api/dashboard-stats',
        type: 'GET',
        success: function(data) {
            updateStatsDisplay(data);
        },
        error: function(xhr, status, error) {
            console.error('Erreur lors du chargement des stats:', error);
        }
    });
}

// Mettre à jour l'affichage des statistiques
function updateStatsDisplay(stats) {
    // Mettre à jour chaque statistique
    if (stats.total_stock_items !== undefined) {
        updateStatValue('total-stock-items', stats.total_stock_items);
    }
    if (stats.stock_alerts !== undefined) {
        updateStatValue('stock-alerts', stats.stock_alerts);
    }
    if (stats.total_projects !== undefined) {
        updateStatValue('total-projects', stats.total_projects);
    }
    if (stats.active_projects !== undefined) {
        updateStatValue('active-projects', stats.active_projects);
    }
    if (stats.total_tasks !== undefined) {
        updateStatValue('total-tasks', stats.total_tasks);
    }
    if (stats.pending_tasks !== undefined) {
        updateStatValue('pending-tasks', stats.pending_tasks);
    }
    if (stats.total_personnel !== undefined) {
        updateStatValue('total-personnel', stats.total_personnel);
    }
    if (stats.total_stock_value !== undefined) {
        updateStatValue('total-stock-value', formatCurrency(stats.total_stock_value));
    }
    if (stats.total_project_budget !== undefined) {
        updateStatValue('total-project-budget', formatCurrency(stats.total_project_budget));
    }
}

// Mettre à jour une valeur de statistique
function updateStatValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Rafraîchir toutes les données du dashboard
function refreshDashboardData() {
    console.log('Rafraîchissement des données du dashboard...');
    
    // Recharger les statistiques
    loadDashboardStats();
    
    // Recharger les graphiques actifs
    $('.chart-container-modern canvas').each(function() {
        const canvasId = $(this).attr('id');
        if (canvasId && canvasId.startsWith('chart-')) {
            const chartId = canvasId.replace('chart-', '');
            refreshChart(parseInt(chartId));
        }
    });
}

// Rafraîchir un graphique spécifique
function refreshChart(chartId) {
    $.ajax({
        url: `/dashboard/api/chart-data/${chartId}`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const canvas = document.getElementById(`chart-${chartId}`);
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    
                    // Détruire le graphique existant
                    const existingChart = Chart.getChart(canvas);
                    if (existingChart) {
                        existingChart.destroy();
                    }
                    
                    // Recréer le graphique
                    const chartConfig = response.config || {};
                    renderModernChart(`chart-${chartId}`, chartConfig.chart_type || 'bar', response.data);
                }
            }
        },
        error: function(xhr, status, error) {
            console.error(`Erreur lors du rafraîchissement du graphique ${chartId}:`, error);
        }
    });
}

// Rendre un graphique moderne avec Chart.js
function renderModernChart(canvasId, chartType, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas ${canvasId} non trouvé`);
        return;
    }
    
    // Configuration moderne pour Chart.js
    const config = {
        type: chartType,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                            size: 13,
                            weight: '600'
                        },
                        color: '#495057'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 16,
                    cornerRadius: 12,
                    titleFont: {
                        size: 15,
                        weight: 'bold',
                        family: "'Inter', sans-serif"
                    },
                    bodyFont: {
                        size: 14,
                        family: "'Inter', sans-serif"
                    },
                    displayColors: true,
                    boxWidth: 12,
                    boxHeight: 12,
                    boxPadding: 6
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    };
    
    // Options spécifiques selon le type de graphique
    if (chartType === 'bar' || chartType === 'line') {
        config.options.scales = {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawBorder: false,
                    lineWidth: 1
                },
                ticks: {
                    font: {
                        family: "'Inter', sans-serif",
                        size: 12
                    },
                    color: '#6c757d',
                    padding: 10
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: "'Inter', sans-serif",
                        size: 12
                    },
                    color: '#6c757d',
                    padding: 10
                }
            }
        };
    }
    
    // Personnalisation pour les graphiques en ligne
    if (chartType === 'line' && data.datasets) {
        data.datasets.forEach(dataset => {
            dataset.tension = 0.4;
            dataset.fill = true;
            dataset.borderWidth = 3;
            dataset.pointRadius = 4;
            dataset.pointHoverRadius = 6;
            dataset.pointBackgroundColor = '#fff';
            dataset.pointBorderWidth = 2;
        });
    }
    
    // Personnalisation pour les graphiques en barres
    if (chartType === 'bar' && data.datasets) {
        data.datasets.forEach(dataset => {
            dataset.borderRadius = 8;
            dataset.borderSkipped = false;
        });
    }
    
    // Créer le graphique
    try {
        new Chart(ctx, config);
    } catch (error) {
        console.error(`Erreur lors de la création du graphique ${canvasId}:`, error);
    }
}

// Animation des compteurs
function animateCounters() {
    $('.stat-value').each(function() {
        const $this = $(this);
        const value = parseFloat($this.text().replace(/[^0-9.]/g, '')) || 0;
        
        if (value > 0 && value < 10000) {
            animateValue(this, 0, value, 1200);
        }
    });
}

// Animer une valeur
function animateValue(element, start, end, duration) {
    if (!element) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);
        
        // Vérifier si c'est un nombre décimal
        if (end % 1 !== 0) {
            element.innerHTML = current.toFixed(2);
        } else {
            element.innerHTML = current;
        }
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            // S'assurer que la valeur finale est exacte
            if (end % 1 !== 0) {
                element.innerHTML = end.toFixed(2);
            } else {
                element.innerHTML = end;
            }
        }
    };
    window.requestAnimationFrame(step);
}

// Formater une devise
function formatCurrency(value) {
    if (typeof value !== 'number') {
        value = parseFloat(value) || 0;
    }
    return value.toFixed(2);
}

// Fonction de debounce pour optimiser les performances
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Afficher un toast de notification
function showToast(type, message) {
    // Créer l'élément toast s'il n'existe pas
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Créer le toast
    const toastId = 'toast-' + Date.now();
    const iconClass = type === 'success' ? 'bi-check-circle-fill text-success' : 
                      type === 'error' ? 'bi-x-circle-fill text-danger' : 
                      'bi-info-circle-fill text-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="bi ${iconClass} me-2 fs-5"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Afficher le toast
    const toastElement = document.getElementById(toastId);
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 3000
        });
        toast.show();
        
        // Supprimer le toast après qu'il soit caché
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
}

// Exporter les données en CSV
function exportDashboardData() {
    const stats = [];
    
    // Collecter toutes les statistiques visibles
    $('.stat-card').each(function() {
        const label = $(this).find('.stat-label').text();
        const value = $(this).find('.stat-value').text();
        stats.push({ label, value });
    });
    
    if (stats.length === 0) {
        showToast('error', 'Aucune donnée à exporter');
        return;
    }
    
    // Créer le contenu CSV
    let csvContent = 'Statistique,Valeur\n';
    stats.forEach(stat => {
        csvContent += `"${stat.label}","${stat.value}"\n`;
    });
    
    // Télécharger le fichier
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `dashboard_stats_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('success', 'Données exportées avec succès');
}

// Imprimer le dashboard
function printDashboard() {
    window.print();
}

// Gestion du mode plein écran
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error('Erreur lors du passage en plein écran:', err);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Écouter les événements de plein écran
document.addEventListener('fullscreenchange', function() {
    const icon = document.querySelector('#fullscreenBtn i');
    if (icon) {
        if (document.fullscreenElement) {
            icon.classList.remove('bi-fullscreen');
            icon.classList.add('bi-fullscreen-exit');
        } else {
            icon.classList.remove('bi-fullscreen-exit');
            icon.classList.add('bi-fullscreen');
        }
    }
});

// Sauvegarder les préférences de l'utilisateur
function saveDashboardPreferences() {
    const preferences = {
        chartOrder: [],
        visibleCharts: []
    };
    
    // Collecter l'ordre et la visibilité des graphiques
    $('.chart-container-modern canvas').each(function() {
        const chartId = $(this).attr('id');
        if (chartId) {
            preferences.chartOrder.push(chartId);
            if ($(this).is(':visible')) {
                preferences.visibleCharts.push(chartId);
            }
        }
    });
    
    // Sauvegarder dans localStorage
    localStorage.setItem('dashboardPreferences', JSON.stringify(preferences));
    
    showToast('success', 'Préférences sauvegardées');
}

// Charger les préférences de l'utilisateur
function loadDashboardPreferences() {
    const savedPreferences = localStorage.getItem('dashboardPreferences');
    if (savedPreferences) {
        try {
            const preferences = JSON.parse(savedPreferences);
            console.log('Préférences chargées:', preferences);
            // Appliquer les préférences ici si nécessaire
        } catch (error) {
            console.error('Erreur lors du chargement des préférences:', error);
        }
    }
}

// Charger les préférences au démarrage
$(window).on('load', function() {
    loadDashboardPreferences();
});