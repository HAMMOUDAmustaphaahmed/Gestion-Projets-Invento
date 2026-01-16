// Stock management specific JavaScript

$(document).ready(function() {
    // Initialize stock management features
    initializeStockManagement();
    
    // Load stock statistics
    loadStockStats();
    
    // Initialize stock alerts
    initializeStockAlerts();
    
    // Initialize stock search
    initializeStockSearch();
    
    // Initialize stock filters
    initializeStockFilters();
    
    // Initialize stock import/export
    initializeStockImportExport();
});

// Initialize stock management
function initializeStockManagement() {
    // Initialize quantity validation
    initializeQuantityValidation();
    
    // Initialize price calculation
    initializePriceCalculation();
    
    // Initialize stock movement tracking
    initializeStockMovementTracking();
    
    // Initialize supplier management
    initializeSupplierManagement();
    
    // Initialize category management
    initializeCategoryManagement();
}

// Initialize quantity validation
function initializeQuantityValidation() {
    $('.quantity-input').on('change', function() {
        var quantity = parseFloat($(this).val());
        var minQuantity = parseFloat($(this).data('min-quantity') || 0);
        
        if (isNaN(quantity)) {
            $(this).val(0);
            return;
        }
        
        if (quantity < 0) {
            $(this).val(0);
            showToast('warning', 'La quantité ne peut pas être négative');
        }
        
        // Check if below minimum quantity
        if (minQuantity > 0 && quantity < minQuantity) {
            $(this).addClass('is-invalid');
            $(this).next('.invalid-feedback').remove();
            $(this).after('<div class="invalid-feedback">Quantité inférieure au minimum (' + minQuantity + ')</div>');
        } else {
            $(this).removeClass('is-invalid');
            $(this).next('.invalid-feedback').remove();
        }
        
        // Update value calculation
        updateItemValue($(this));
    });
}

// Update item value based on quantity and price
function updateItemValue(quantityInput) {
    var row = quantityInput.closest('tr');
    var quantity = parseFloat(quantityInput.val()) || 0;
    var price = parseFloat(row.find('.price-input').val()) || 0;
    var value = quantity * price;
    
    row.find('.value-display').text(formatCurrency(value));
    
    // Update total value
    updateTotalValue();
}

// Update total value of all items
function updateTotalValue() {
    var total = 0;
    
    $('.quantity-input').each(function() {
        var row = $(this).closest('tr');
        var quantity = parseFloat($(this).val()) || 0;
        var price = parseFloat(row.find('.price-input').val()) || 0;
        total += quantity * price;
    });
    
    $('#totalStockValue').text(formatCurrency(total));
}

// Initialize price calculation
function initializePriceCalculation() {
    $('.price-input').on('change', function() {
        var price = parseFloat($(this).val());
        
        if (isNaN(price)) {
            $(this).val(0);
            return;
        }
        
        if (price < 0) {
            $(this).val(0);
            showToast('warning', 'Le prix ne peut pas être négatif');
        }
        
        // Update value calculation
        updateItemValue($(this));
    });
}

// Initialize stock movement tracking
function initializeStockMovementTracking() {
    // Initialize movement type selection
    $('.movement-type').on('change', function() {
        var type = $(this).val();
        var reasonField = $(this).closest('.stock-movement').find('.movement-reason');
        
        if (type === 'adjustment' || type === 'correction') {
            reasonField.show();
        } else {
            reasonField.hide();
        }
    });
    
    // Initialize movement form submission
    $('.stock-movement-form').on('submit', function(e) {
        e.preventDefault();
        
        var form = $(this);
        var itemId = form.data('item-id');
        var data = form.serialize();
        
        $.ajax({
            url: '/stock/api/movement/' + itemId,
            type: 'POST',
            data: data,
            success: function(response) {
                if (response.success) {
                    form[0].reset();
                    showToast('success', 'Mouvement enregistré');
                    
                    // Update stock quantity display
                    updateStockQuantity(itemId, response.new_quantity);
                    
                    // Refresh stock alerts
                    checkStockAlerts();
                } else {
                    showToast('error', response.message || 'Erreur lors de l\'enregistrement');
                }
            },
            error: function() {
                showToast('error', 'Erreur réseau');
            }
        });
    });
}

// Update stock quantity display
function updateStockQuantity(itemId, newQuantity) {
    var quantityDisplay = $('#item-quantity-' + itemId);
    if (quantityDisplay.length) {
        quantityDisplay.text(newQuantity);
        
        // Update row styling based on quantity
        var row = quantityDisplay.closest('tr');
        var minQuantity = parseFloat(row.data('min-quantity') || 0);
        
        if (newQuantity <= minQuantity && minQuantity > 0) {
            row.addClass('table-warning');
            row.find('.stock-status').html('<span class="badge bg-danger">Stock bas</span>');
        } else if (newQuantity === 0) {
            row.addClass('table-secondary');
            row.find('.stock-status').html('<span class="badge bg-secondary">Rupture</span>');
        } else {
            row.removeClass('table-warning table-secondary');
            row.find('.stock-status').html('<span class="badge bg-success">Disponible</span>');
        }
    }
}

// Initialize supplier management
function initializeSupplierManagement() {
    // Supplier search
    $('#supplierSearch').on('keyup', debounce(function() {
        var searchTerm = $(this).val();
        searchSuppliers(searchTerm);
    }, 300));
    
    // Add supplier
    $('#addSupplier').on('click', function() {
        showSupplierForm();
    });
    
    // Edit supplier
    $('.edit-supplier').on('click', function(e) {
        e.preventDefault();
        var supplierId = $(this).data('supplier-id');
        editSupplier(supplierId);
    });
    
    // Delete supplier
    $('.delete-supplier').on('click', function(e) {
        e.preventDefault();
        var supplierId = $(this).data('supplier-id');
        var supplierName = $(this).data('supplier-name');
        deleteSupplier(supplierId, supplierName);
    });
}

// Search suppliers
function searchSuppliers(searchTerm) {
    $.ajax({
        url: '/stock/api/suppliers/search',
        type: 'GET',
        data: { q: searchTerm },
        success: function(response) {
            displaySupplierSearchResults(response);
        }
    });
}

// Display supplier search results
function displaySupplierSearchResults(results) {
    var container = $('#supplierResults');
    
    if (!container.length) {
        container = $('<div id="supplierResults" class="card mt-3"></div>');
        $('#supplierManagement').after(container);
    }
    
    if (results.length === 0) {
        container.html(`
            <div class="card-body">
                <p class="text-muted mb-0">Aucun fournisseur trouvé</p>
            </div>
        `);
        return;
    }
    
    var html = `
        <div class="card-header">
            <h6 class="mb-0">Résultats de recherche</h6>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Contact</th>
                            <th>Téléphone</th>
                            <th>Email</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    results.forEach(function(supplier) {
        html += `
            <tr>
                <td>${supplier.name}</td>
                <td>${supplier.contact_person || '-'}</td>
                <td>${supplier.phone || '-'}</td>
                <td>${supplier.email || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="selectSupplier(${supplier.id}, '${supplier.name}')">
                        Sélectionner
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.html(html);
}

// Select supplier
function selectSupplier(supplierId, supplierName) {
    $('#supplierId').val(supplierId);
    $('#supplierName').val(supplierName);
    $('#supplierResults').remove();
    showToast('success', 'Fournisseur sélectionné: ' + supplierName);
}

// Show supplier form
function showSupplierForm(supplierData) {
    var modalContent = `
        <div class="modal-header">
            <h5 class="modal-title">${supplierData ? 'Modifier le fournisseur' : 'Nouveau fournisseur'}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            <form id="supplierForm">
                <div class="mb-3">
                    <label for="supplierFormName" class="form-label">Nom *</label>
                    <input type="text" class="form-control" id="supplierFormName" name="name" 
                           value="${supplierData ? supplierData.name : ''}" required>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label for="supplierFormContact" class="form-label">Personne de contact</label>
                        <input type="text" class="form-control" id="supplierFormContact" name="contact_person"
                               value="${supplierData ? supplierData.contact_person || '' : ''}">
                    </div>
                    <div class="col-md-6">
                        <label for="supplierFormPhone" class="form-label">Téléphone</label>
                        <input type="tel" class="form-control" id="supplierFormPhone" name="phone"
                               value="${supplierData ? supplierData.phone || '' : ''}">
                    </div>
                </div>
                
                <div class="mb-3">
                    <label for="supplierFormEmail" class="form-label">Email</label>
                    <input type="email" class="form-control" id="supplierFormEmail" name="email"
                           value="${supplierData ? supplierData.email || '' : ''}">
                </div>
                
                <div class="mb-3">
                    <label for="supplierFormAddress" class="form-label">Adresse</label>
                    <textarea class="form-control" id="supplierFormAddress" name="address" rows="3">${supplierData ? supplierData.address || '' : ''}</textarea>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label for="supplierFormCity" class="form-label">Ville</label>
                        <input type="text" class="form-control" id="supplierFormCity" name="city"
                               value="${supplierData ? supplierData.city || '' : ''}">
                    </div>
                    <div class="col-md-6">
                        <label for="supplierFormCountry" class="form-label">Pays</label>
                        <input type="text" class="form-control" id="supplierFormCountry" name="country"
                               value="${supplierData ? supplierData.country || '' : ''}">
                    </div>
                </div>
                
                <div class="mb-3">
                    <label for="supplierFormWebsite" class="form-label">Site web</label>
                    <input type="url" class="form-control" id="supplierFormWebsite" name="website"
                           value="${supplierData ? supplierData.website || '' : ''}">
                </div>
                
                <div class="mb-3">
                    <label for="supplierFormNotes" class="form-label">Notes</label>
                    <textarea class="form-control" id="supplierFormNotes" name="notes" rows="3">${supplierData ? supplierData.notes || '' : ''}</textarea>
                </div>
                
                ${supplierData ? '<input type="hidden" name="supplier_id" value="' + supplierData.id + '">' : ''}
            </form>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
            <button type="button" class="btn btn-primary" onclick="saveSupplier()">
                ${supplierData ? 'Mettre à jour' : 'Créer'}
            </button>
        </div>
    `;
    
    $('#supplierModal .modal-content').html(modalContent);
    $('#supplierModal').modal('show');
}

// Save supplier
function saveSupplier() {
    var formData = $('#supplierForm').serialize();
    var url = $('#supplierForm input[name="supplier_id"]').length ? '/stock/suppliers/update' : '/stock/suppliers/add';
    
    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        success: function(response) {
            if (response.success) {
                $('#supplierModal').modal('hide');
                showToast('success', response.message || 'Fournisseur sauvegardé');
                location.reload();
            } else {
                showToast('error', response.message || 'Erreur lors de la sauvegarde');
            }
        },
        error: function() {
            showToast('error', 'Erreur réseau');
        }
    });
}

// Edit supplier
function editSupplier(supplierId) {
    $.ajax({
        url: '/stock/api/suppliers/' + supplierId,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                showSupplierForm(response.supplier);
            }
        }
    });
}

// Delete supplier
function deleteSupplier(supplierId, supplierName) {
    showConfirmModal(
        'Supprimer le fournisseur',
        `Êtes-vous sûr de vouloir supprimer le fournisseur <strong>${supplierName}</strong> ?`,
        function() {
            $.ajax({
                url: '/stock/suppliers/' + supplierId + '/delete',
                type: 'POST',
                success: function(response) {
                    if (response.success) {
                        showToast('success', 'Fournisseur supprimé');
                        location.reload();
                    } else {
                        showToast('error', response.message || 'Erreur lors de la suppression');
                    }
                },
                error: function() {
                    showToast('error', 'Erreur réseau');
                }
            });
        }
    );
}

// Initialize category management
function initializeCategoryManagement() {
    // Similar to supplier management, implement category CRUD operations
    // This would include:
    // - Category search
    // - Add/edit/delete category
    // - Category attribute templates
}

// Load stock statistics
function loadStockStats() {
    $.ajax({
        url: '/stock/api/stats',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                updateStockStatsDisplay(response.stats);
            }
        }
    });
}

// Update stock statistics display
function updateStockStatsDisplay(stats) {
    if (stats.total_items !== undefined) {
        $('#totalStockItems').text(stats.total_items);
    }
    
    if (stats.total_value !== undefined) {
        $('#totalStockValue').text(formatCurrency(stats.total_value));
    }
    
    if (stats.low_stock_count !== undefined) {
        $('#lowStockCount').text(stats.low_stock_count);
    }
    
    if (stats.out_of_stock_count !== undefined) {
        $('#outOfStockCount').text(stats.out_of_stock_count);
    }
    
    if (stats.recent_movements !== undefined) {
        $('#recentMovements').text(stats.recent_movements);
    }
}

// Initialize stock alerts
function initializeStockAlerts() {
    // Check for stock alerts on page load
    checkStockAlerts();
    
    // Set up periodic checking (every 5 minutes)
    setInterval(checkStockAlerts, 300000);
    
    // Initialize alert notifications
    $('#stockAlerts').on('click', function() {
        showStockAlerts();
    });
}

// Show stock alerts
function showStockAlerts() {
    $.ajax({
        url: '/stock/alerts',
        type: 'GET',
        success: function(response) {
            // This would open a modal or navigate to alerts page
            window.location.href = '/stock/alerts';
        }
    });
}

// Initialize stock search
function initializeStockSearch() {
    var searchInput = $('#stockSearch');
    
    if (searchInput.length) {
        searchInput.on('keyup', debounce(function() {
            var searchTerm = $(this).val();
            
            if (searchTerm.length >= 2) {
                searchStockItems(searchTerm);
            } else {
                $('#stockSearchResults').remove();
            }
        }, 300));
    }
}

// Search stock items
function searchStockItems(searchTerm) {
    $.ajax({
        url: '/stock/api/search',
        type: 'GET',
        data: { q: searchTerm },
        success: function(response) {
            displayStockSearchResults(response);
        }
    });
}

// Display stock search results
function displayStockSearchResults(results) {
    var container = $('#stockSearchResults');
    
    if (!container.length) {
        container = $('<div id="stockSearchResults" class="card mt-3 position-absolute" style="z-index: 1000; width: 100%;"></div>');
        $('#stockSearch').after(container);
    }
    
    if (results.length === 0) {
        container.html(`
            <div class="card-body">
                <p class="text-muted mb-0">Aucun élément trouvé</p>
            </div>
        `);
        return;
    }
    
    var html = `
        <div class="card-header">
            <h6 class="mb-0">Résultats de recherche (${results.length})</h6>
        </div>
        <div class="card-body p-0">
            <div class="list-group list-group-flush">
    `;
    
    results.forEach(function(item) {
        html += `
            <a href="/stock/view/${item.id}" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${item.reference}</h6>
                    <small class="text-${item.quantity <= item.min_quantity ? 'danger' : 'success'}">
                        ${item.quantity} en stock
                    </small>
                </div>
                <p class="mb-1">${item.libelle}</p>
                <small class="text-muted">${item.category || 'Non catégorisé'}</small>
            </a>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    container.html(html);
}

// Initialize stock filters
function initializeStockFilters() {
    $('.stock-filter').on('change', function() {
        applyStockFilters();
    });
    
    // Date range filter for movements
    $('#stockDateRange').on('apply.daterangepicker', function() {
        applyStockFilters();
    });
}

// Apply stock filters
function applyStockFilters() {
    var filters = {
        category: $('#categoryFilter').val(),
        supplier: $('#supplierFilter').val(),
        status: $('#statusFilter').val(),
        min_quantity: $('#minQuantityFilter').val(),
        max_quantity: $('#maxQuantityFilter').val(),
        date_range: $('#stockDateRange').val()
    };
    
    // Update URL with filters
    var url = new URL(window.location);
    Object.keys(filters).forEach(function(key) {
        if (filters[key]) {
            url.searchParams.set(key, filters[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    window.location.href = url.toString();
}

// Initialize stock import/export
function initializeStockImportExport() {
    // Import
    $('#importStock').on('click', function() {
        showImportModal();
    });
    
    // Export
    $('#exportStock').on('click', function() {
        exportStockData();
    });
    
    // Import template download
    $('#downloadTemplate').on('click', function() {
        downloadImportTemplate();
    });
}

// Show import modal
function showImportModal() {
    var modalContent = `
        <div class="modal-header">
            <h5 class="modal-title">Importer des éléments de stock</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            <div class="alert alert-info">
                <h6><i class="bi bi-info-circle"></i> Instructions</h6>
                <p class="mb-0">
                    Téléchargez le modèle, remplissez-le avec vos données, puis importez-le ici.
                    Format supporté: CSV, Excel.
                </p>
            </div>
            
            <div class="mb-3">
                <label for="importFile" class="form-label">Fichier à importer</label>
                <input type="file" class="form-control" id="importFile" accept=".csv,.xlsx,.xls">
            </div>
            
            <div class="mb-3">
                <label for="importType" class="form-label">Type d'importation</label>
                <select class="form-select" id="importType">
                    <option value="create">Créer de nouveaux éléments</option>
                    <option value="update">Mettre à jour les éléments existants</option>
                    <option value="both">Créer et mettre à jour</option>
                </select>
            </div>
            
            <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="importHeaders" checked>
                <label class="form-check-label" for="importHeaders">
                    Le fichier contient des en-têtes de colonnes
                </label>
            </div>
            
            <div class="progress mb-3 d-none" id="importProgress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" onclick="downloadImportTemplate()">
                <i class="bi bi-download"></i> Télécharger le modèle
            </button>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
            <button type="button" class="btn btn-primary" onclick="startImport()">
                <i class="bi bi-upload"></i> Importer
            </button>
        </div>
    `;
    
    $('#importModal .modal-content').html(modalContent);
    $('#importModal').modal('show');
}

// Download import template
function downloadImportTemplate() {
    window.open('/stock/export/template', '_blank');
}

// Start import
function startImport() {
    var fileInput = $('#importFile')[0];
    var file = fileInput.files[0];
    
    if (!file) {
        showToast('error', 'Veuillez sélectionner un fichier');
        return;
    }
    
    var formData = new FormData();
    formData.append('file', file);
    formData.append('import_type', $('#importType').val());
    formData.append('has_headers', $('#importHeaders').is(':checked'));
    
    $('#importProgress').removeClass('d-none');
    
    $.ajax({
        url: '/stock/api/import',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener('progress', function(evt) {
                if (evt.lengthComputable) {
                    var percentComplete = (evt.loaded / evt.total) * 100;
                    $('#importProgress .progress-bar').css('width', percentComplete + '%');
                }
            }, false);
            return xhr;
        },
        success: function(response) {
            $('#importProgress').addClass('d-none');
            
            if (response.success) {
                $('#importModal').modal('hide');
                showToast('success', `Importation réussie: ${response.created} créés, ${response.updated} mis à jour`);
                location.reload();
            } else {
                showToast('error', response.message || 'Erreur lors de l\'importation');
            }
        },
        error: function() {
            $('#importProgress').addClass('d-none');
            showToast('error', 'Erreur réseau lors de l\'importation');
        }
    });
}

// Export stock data
function exportStockData() {
    var format = $('#exportFormat').val() || 'csv';
    var filters = {
        category: $('#categoryFilter').val(),
        supplier: $('#supplierFilter').val(),
        status: $('#statusFilter').val()
    };
    
    var params = $.param(filters) + '&format=' + format;
    var url = '/stock/export?' + params;
    
    window.open(url, '_blank');
}

// Stock item quick actions
function initializeStockQuickActions() {
    // Quick add to cart
    $('.add-to-cart').on('click', function() {
        var itemId = $(this).data('item-id');
        var itemName = $(this).data('item-name');
        addToCart(itemId, itemName);
    });
    
    // Quick edit
    $('.quick-edit').on('click', function() {
        var itemId = $(this).data('item-id');
        quickEditItem(itemId);
    });
    
    // Quick view
    $('.quick-view').on('click', function() {
        var itemId = $(this).data('item-id');
        quickViewItem(itemId);
    });
}

// Add item to cart
function addToCart(itemId, itemName) {
    // Implement cart functionality
    showToast('success', itemName + ' ajouté au panier');
}

// Quick edit item
function quickEditItem(itemId) {
    // Load item data and show quick edit form
    $.ajax({
        url: '/stock/api/item/' + itemId,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                showQuickEditForm(response.item);
            }
        }
    });
}

// Show quick edit form
function showQuickEditForm(item) {
    var modalContent = `
        <div class="modal-header">
            <h5 class="modal-title">Modifier: ${item.reference}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            <form id="quickEditForm">
                <div class="mb-3">
                    <label class="form-label">Quantité</label>
                    <input type="number" class="form-control" name="quantity" value="${item.quantity}" min="0">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Prix unitaire</label>
                    <input type="number" class="form-control" name="price" value="${item.price}" step="0.01" min="0">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Emplacement</label>
                    <input type="text" class="form-control" name="location" value="${item.location || ''}">
                </div>
                
                <input type="hidden" name="item_id" value="${item.id}">
            </form>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
            <button type="button" class="btn btn-primary" onclick="saveQuickEdit()">Enregistrer</button>
        </div>
    `;
    
    $('#quickEditModal .modal-content').html(modalContent);
    $('#quickEditModal').modal('show');
}

// Save quick edit
function saveQuickEdit() {
    var formData = $('#quickEditForm').serialize();
    
    $.ajax({
        url: '/stock/api/quick-edit',
        type: 'POST',
        data: formData,
        success: function(response) {
            if (response.success) {
                $('#quickEditModal').modal('hide');
                showToast('success', 'Élément mis à jour');
                location.reload();
            }
        }
    });
}

// Quick view item
function quickViewItem(itemId) {
    window.location.href = '/stock/view/' + itemId;
}

// Initialize when document is ready
$(function() {
    // Check if we're on a stock page
    if (window.location.pathname.includes('/stock')) {
        // Initialize additional stock features
        initializeStockQuickActions();
        
        // Load initial data
        loadStockStats();
        
        // Set up auto-refresh for stock data (every 2 minutes)
        setInterval(loadStockStats, 120000);
    }
});