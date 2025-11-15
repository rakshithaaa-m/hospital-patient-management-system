// Hospital Management System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initSidebar();
    initNotifications();
    initForms();
    initDataTables();
    initInteractiveElements();
});

// Sidebar functionality
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    if (sidebar) {
        // Add active state to current page
        const currentPath = window.location.pathname;
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
        
        // Mobile sidebar toggle
        const sidebarToggle = document.createElement('button');
        sidebarToggle.className = 'btn btn-primary d-md-none mb-3';
        sidebarToggle.innerHTML = '☰ Menu';
        sidebarToggle.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1000;';
        
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        document.body.appendChild(sidebarToggle);
    }
}

// Notification system
function initNotifications() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('alert-dismissible')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        }, 5000);
    });
}

// Form enhancements
function initForms() {
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Processing...';
                submitBtn.disabled = true;
            }
        });
    });
    
    // Real-time form validation
    const inputs = document.querySelectorAll('input[required], select[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

// Field validation
function validateField(field) {
    const value = field.value.trim();
    const errorElement = field.parentNode.querySelector('.invalid-feedback');
    
    if (!value && field.hasAttribute('required')) {
        showFieldError(field, 'This field is required');
    } else {
        clearFieldError(field);
    }
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let errorElement = field.parentNode.querySelector('.invalid-feedback');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback';
        field.parentNode.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    
    const errorElement = field.parentNode.querySelector('.invalid-feedback');
    if (errorElement) {
        errorElement.remove();
    }
}

// Data tables functionality
function initDataTables() {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        if (table.rows.length > 6) { // Only enhance tables with multiple rows
            addTableSearch(table);
            addTableSorting(table);
        }
    });
}

function addTableSearch(table) {
    const container = table.parentNode;
    const searchDiv = document.createElement('div');
    searchDiv.className = 'table-search mb-3';
    searchDiv.innerHTML = `
        <div class="input-group">
            <input type="text" class="form-control" placeholder="Search...">
            <button class="btn btn-outline-secondary" type="button">🔍</button>
        </div>
    `;
    
    container.insertBefore(searchDiv, table);
    
    const searchInput = searchDiv.querySelector('input');
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

function addTableSorting(table) {
    const headers = table.querySelectorAll('thead th');
    headers.forEach((header, index) => {
        if (index !== headers.length - 1) { // Don't add to action column
            header.style.cursor = 'pointer';
            header.title = 'Click to sort';
            
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        }
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isNumeric = !isNaN(rows[0].cells[columnIndex].textContent);
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        if (isNumeric) {
            return parseFloat(aVal) - parseFloat(bVal);
        } else {
            return aVal.localeCompare(bVal);
        }
    });
    
    // Clear and re-append sorted rows
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    rows.forEach(row => tbody.appendChild(row));
}

// Interactive elements
function initInteractiveElements() {
    // Doctor card selection
    const doctorCards = document.querySelectorAll('.doctor-card');
    doctorCards.forEach(card => {
        card.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                
                // Update visual selection
                doctorCards.forEach(c => c.classList.remove('selected'));
                this.classList.add('selected');
            }
        });
    });
    
    // Dynamic stock updates
    const stockButtons = document.querySelectorAll('[onclick*="updateStock"]');
    stockButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const onclick = this.getAttribute('onclick');
            const match = onclick.match(/updateStock\((\d+),\s*(\d+)\)/);
            if (match) {
                const medicineId = parseInt(match[1]);
                const newStock = parseInt(match[2]);
                updateStock(medicineId, newStock);
            }
        });
    });
}

// API functions
async function updateStock(medicineId, newStock) {
    try {
        const response = await fetch(`/update-stock/${medicineId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                stock_quantity: newStock
            })
        });
        
        const data = await response.json();
        
        if (data.message) {
            showNotification('Stock updated successfully!', 'success');
            
            if (data.alerts && data.alerts.length > 0) {
                data.alerts.forEach(alert => {
                    showNotification(alert.message, 'warning');
                });
            }
            
            // Reload after a short delay to show notifications
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    } catch (error) {
        console.error('Error updating stock:', error);
        showNotification('Error updating stock', 'danger');
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Utility functions
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN');
}

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

// Export for use in other scripts
window.HospitalSystem = {
    updateStock,
    showNotification,
    format