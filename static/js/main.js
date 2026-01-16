// Main JavaScript file for GMAO application

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Confirm before delete
    $('.confirm-delete').on('click', function(e) {
        e.preventDefault();
        var url = $(this).attr('href');
        var message = $(this).data('confirm') || 'Êtes-vous sûr de vouloir supprimer cet élément ?';
        
        if (confirm(message)) {
            window.location.href = url;
        }
    });
    
    // AJAX delete
    $('.ajax-delete').on('click', function(e) {
        e.preventDefault();
        var url = $(this).data('url');
        var message = $(this).data('confirm') || 'Êtes-vous sûr de vouloir supprimer cet élément ?';
        var target = $(this).data('target');
        
        if (confirm(message)) {
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    csrf_token: $('meta[name="csrf-token"]').attr('content')
                },
                success: function(response) {
                    if (response.success) {
                        if (target) {
                            $(target).remove();
                        }
                        showToast('success', 'Suppression effectuée avec succès.');
                    } else {
                        showToast('error', response.message || 'Erreur lors de la suppression.');
                    }
                },
                error: function() {
                    showToast('error', 'Erreur réseau. Veuillez réessayer.');
                }
            });
        }
    });
    
    // Auto-submit forms on change
    $('.auto-submit').on('change', function() {
        $(this).closest('form').submit();
    });
    
    // Toggle password visibility
    $('.toggle-password').on('click', function() {
        var input = $($(this).data('target'));
        var icon = $(this).find('i');
        
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            icon.removeClass('bi-eye').addClass('bi-eye-slash');
        } else {
            input.attr('type', 'password');
            icon.removeClass('bi-eye-slash').addClass('bi-eye');
        }
    });
    
    // Check for stock alerts periodically
    if ($('#stock-alerts-indicator').length > 0) {
        checkStockAlerts();
        setInterval(checkStockAlerts, 300000); // Every 5 minutes
    }
    
    // Initialize Select2
    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Sélectionner...',
            allowClear: true
        });
    }
    
    // Initialize Tempus Dominus date pickers (REMPLACEMENT de jQuery UI)
    if (typeof tempusDominus !== 'undefined') {
        document.querySelectorAll('.datepicker').forEach(function(el) {
            new tempusDominus.TempusDominus(el, {
                display: {
                    components: {
                        decades: false,
                        year: true,
                        month: true,
                        date: true,
                        hours: false,
                        minutes: false,
                        seconds: false
                    },
                    buttons: {
                        today: true,
                        clear: false,
                        close: true
                    },
                    theme: 'light'
                },
                localization: {
                    locale: 'fr',
                    format: 'yyyy-MM-dd'
                }
            });
        });
    }
    
    // Initialize DataTables if present
    if ($.fn.DataTable) {
        $('.datatable:not(.initialized)').each(function() {
            $(this).addClass('initialized');
            $(this).DataTable({
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/fr-FR.json'
                },
                pageLength: 25,
                responsive: true,
                order: [],
                dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                     '<"row"<"col-sm-12"tr>>' +
                     '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
                initComplete: function() {
                    // Add custom class to search input
                    $('.dataTables_filter input').addClass('form-control form-control-sm');
                    $('.dataTables_length select').addClass('form-select form-select-sm');
                }
            });
        });
    }
    
    // Auto-dismiss alerts
    setTimeout(function() {
        $('.alert:not(.alert-permanent)').alert('close');
    }, 5000);
    
    // Prevent double form submission
    $('form').on('submit', function() {
        var submitButton = $(this).find('button[type="submit"]');
        if (submitButton.length) {
            submitButton.prop('disabled', true);
            submitButton.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Chargement...');
        }
    });
    
    // File upload preview
    $('.file-input').on('change', function() {
        var fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').html(fileName);
    });
    
    // Dynamic form fields
    $('.add-field').on('click', function() {
        var template = $($(this).data('template'));
        var container = $($(this).data('target'));
        var newField = template.clone();
        newField.removeClass('d-none');
        newField.find('input, select, textarea').val('');
        container.append(newField);
        updateFieldIndexes(container);
    });
    
    $(document).on('click', '.remove-field', function() {
        if ($(this).closest('.field-group').siblings('.field-group').length > 0) {
            $(this).closest('.field-group').remove();
            updateFieldIndexes($(this).closest('.fields-container'));
        }
    });
});

// Function to update field indexes in dynamic forms
function updateFieldIndexes(container) {
    container.find('.field-group').each(function(index) {
        $(this).find('[name]').each(function() {
            var name = $(this).attr('name');
            if (name) {
                var newName = name.replace(/\[\d+\]/, '[' + index + ']');
                $(this).attr('name', newName);
            }
            
            var id = $(this).attr('id');
            if (id) {
                var newId = id.replace(/\d+/, index);
                $(this).attr('id', newId);
            }
        });
        
        $(this).find('label').each(function() {
            var forAttr = $(this).attr('for');
            if (forAttr) {
                var newFor = forAttr.replace(/\d+/, index);
                $(this).attr('for', newFor);
            }
        });
    });
}

// Function to check stock alerts via AJAX
function checkStockAlerts() {
    if (!window.location.pathname.includes('/stock/')) {
        $.ajax({
            url: '/stock/api/check-alerts',
            type: 'GET',
            success: function(response) {
                if (response.count > 0) {
                    updateStockAlertsBadge(response.count);
                    showStockAlertNotification(response);
                } else {
                    updateStockAlertsBadge(0);
                }
            },
            error: function() {
                console.error('Failed to check stock alerts');
            }
        });
    }
}

// Function to update stock alerts badge
function updateStockAlertsBadge(count) {
    var badge = $('#stock-alerts-badge');
    if (badge.length) {
        if (count > 0) {
            badge.text(count).removeClass('d-none');
        } else {
            badge.addClass('d-none');
        }
    }
}

// Function to show stock alert notification
function showStockAlertNotification(response) {
    // Only show notification if not on stock page
    if (!window.location.pathname.includes('/stock/')) {
        if (response.count === 1) {
            showToast('warning', '1 alerte de stock détectée.');
        } else if (response.count > 1) {
            showToast('warning', response.count + ' alertes de stock détectées.');
        }
    }
}

// Function to show toast notifications
function showToast(type, message) {
    var toastContainer = $('#toast-container');
    
    if (toastContainer.length === 0) {
        toastContainer = $('<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 1055;"></div>');
        $('body').append(toastContainer);
    }
    
    var toastId = 'toast-' + Date.now();
    var toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.append(toastHtml);
    
    var toastEl = document.getElementById(toastId);
    var toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove toast after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function () {
        $(this).remove();
        if ($('#toast-container').children().length === 0) {
            $('#toast-container').remove();
        }
    });
}

// Function to get icon for toast type
function getToastIcon(type) {
    switch (type) {
        case 'success': return 'bi-check-circle';
        case 'error': return 'bi-exclamation-circle';
        case 'warning': return 'bi-exclamation-triangle';
        case 'info': return 'bi-info-circle';
        default: return 'bi-info-circle';
    }
}

// Function to format dates
function formatDate(dateString, format = 'dd/mm/yyyy') {
    if (!dateString) return '';
    
    var date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    var day = date.getDate().toString().padStart(2, '0');
    var month = (date.getMonth() + 1).toString().padStart(2, '0');
    var year = date.getFullYear();
    
    if (format === 'dd/mm/yyyy') {
        return day + '/' + month + '/' + year;
    } else if (format === 'yyyy-mm-dd') {
        return year + '-' + month + '-' + day;
    }
    
    return date.toLocaleDateString('fr-FR');
}

// Function to format currency
function formatCurrency(amount, currency = '€') {
    if (isNaN(amount)) return '0.00 ' + currency;
    
    return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount) + ' ' + currency;
}

// Function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Function to validate email
function isValidEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Function to validate phone number (French format)
function isValidPhone(phone) {
    var re = /^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$/;
    return re.test(phone.replace(/\s/g, ''));
}

// Function to show confirmation modal
function showConfirmModal(title, message, confirmCallback, cancelCallback) {
    $('#confirmModal .modal-title').text(title);
    $('#confirmModal .modal-body').html(message);
    
    $('#confirmModal .btn-confirm').off('click').on('click', function() {
        if (typeof confirmCallback === 'function') {
            confirmCallback();
        }
        $('#confirmModal').modal('hide');
    });
    
    $('#confirmModal').modal('show');
    
    $('#confirmModal').off('hidden.bs.modal').on('hidden.bs.modal', function() {
        if (typeof cancelCallback === 'function') {
            cancelCallback();
        }
    });
}

// Function to show loading overlay
function showLoading(selector) {
    var target = selector ? $(selector) : $('body');
    if (target.find('.loading-overlay').length === 0) {
        target.append(`
            <div class="loading-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.8); z-index: 9999; display: flex; align-items: center; justify-content: center;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
            </div>
        `);
    }
}

// Function to hide loading overlay
function hideLoading(selector) {
    var target = selector ? $(selector) : $('body');
    target.find('.loading-overlay').remove();
}

// Function to copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('success', 'Copié dans le presse-papier');
    }).catch(function(err) {
        console.error('Erreur de copie: ', err);
        showToast('error', 'Échec de la copie');
    });
}

// Function to handle file upload with progress
function uploadFile(file, url, onProgress, onSuccess, onError) {
    var formData = new FormData();
    formData.append('file', file);
    
    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener('progress', function(evt) {
                if (evt.lengthComputable) {
                    var percentComplete = (evt.loaded / evt.total) * 100;
                    if (typeof onProgress === 'function') {
                        onProgress(percentComplete);
                    }
                }
            }, false);
            return xhr;
        },
        success: function(response) {
            if (typeof onSuccess === 'function') {
                onSuccess(response);
            }
        },
        error: function(xhr, status, error) {
            if (typeof onError === 'function') {
                onError(error);
            }
        }
    });
}

// CSRF token setup for AJAX requests
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            var token = $('meta[name="csrf-token"]').attr('content');
            if (token) {
                xhr.setRequestHeader("X-CSRFToken", token);
            }
        }
    }
});

// Global error handler for AJAX requests
$(document).ajaxError(function(event, jqxhr, settings, thrownError) {
    if (jqxhr.status === 401) {
        // Unauthorized - redirect to login
        window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
    } else if (jqxhr.status === 403) {
        // Forbidden
        showToast('error', 'Accès refusé. Vous n\'avez pas les permissions nécessaires.');
    } else if (jqxhr.status === 500) {
        // Server error
        showToast('error', 'Erreur serveur. Veuillez réessayer plus tard.');
    } else if (jqxhr.status === 0) {
        // Network error
        showToast('error', 'Erreur réseau. Vérifiez votre connexion.');
    }
});

// Export data function
function exportData(format, endpoint, params) {
    var url = endpoint + '?format=' + format;
    if (params) {
        for (var key in params) {
            if (params.hasOwnProperty(key)) {
                url += '&' + key + '=' + encodeURIComponent(params[key]);
            }
        }
    }
    window.open(url, '_blank');
}

// Debounce function for search inputs
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Throttle function for scroll events
function throttle(func, limit) {
    var inThrottle;
    return function() {
        var args = arguments;
        var context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(function() {
                inThrottle = false;
            }, limit);
        }
    };
}

// Initialize when document is ready
$(function() {
    // Add active class to current nav item
    var currentPath = window.location.pathname;
    $('.navbar-nav .nav-link').each(function() {
        var linkPath = $(this).attr('href');
        if (linkPath && currentPath.startsWith(linkPath) && linkPath !== '/') {
            $(this).addClass('active');
            $(this).closest('.dropdown').find('.dropdown-toggle').addClass('active');
        }
    });
    
    // Initialize all tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
});