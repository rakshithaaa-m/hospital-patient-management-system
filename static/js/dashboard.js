// Dashboard Specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initDashboardCharts();
    initRealTimeUpdates();
    initDashboardFilters();
});

// Initialize dashboard charts
function initDashboardCharts() {
    // Revenue chart (if chart.js is available)
    if (typeof Chart !== 'undefined') {
        initRevenueChart();
        initAppointmentChart();
    }
    
    // Statistics animations
    animateStatistics();
}

// Animate statistic numbers
function animateStatistics() {
    const statNumbers = document.querySelectorAll('.stat-number, .text-value-lg');
    
    statNumbers.forEach(stat => {
        const finalValue = parseInt(stat.textContent);
        let currentValue = 0;
        const duration = 2000; // 2 seconds
        const increment = finalValue / (duration / 16); // 60fps
        
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                stat.textContent = finalValue.toLocaleString();
                clearInterval(timer);
            } else {
                stat.textContent = Math.floor(currentValue).toLocaleString();
            }
        }, 16);
    });
}

// Real-time updates
function initRealTimeUpdates() {
    // Update time every minute
    updateDashboardTime();
    setInterval(updateDashboardTime, 60000);
    
    // Simulate real-time notifications
    simulateRealTimeData();
}

function updateDashboardTime() {
    const timeElements = document.querySelectorAll('.current-time');
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    timeElements.forEach(element => {
        element.textContent = timeString;
    });
}

function simulateRealTimeData() {
    // Simulate new appointments or updates
    setInterval(() => {
        const shouldUpdate = Math.random() < 0.1; // 10% chance every interval
        
        if (shouldUpdate) {
            showNotification('New appointment scheduled', 'info');
            
            // Update statistics slightly
            const appointmentCount = document.querySelector('[data-stat="appointments"]');
            if (appointmentCount) {
                const current = parseInt(appointmentCount.textContent);
                appointmentCount.textContent = (current + 1).toString();
            }
        }
    }, 30000); // Check every 30 seconds
}

// Dashboard filters
function initDashboardFilters() {
    const dateFilters = document.querySelectorAll('.date-filter');
    const statusFilters = document.querySelectorAll('.status-filter');
    
    // Date filter functionality
    dateFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            filterDataByDate(period);
            
            // Update active state
            dateFilters.forEach(f => f.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Status filter functionality
    statusFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const status = this.getAttribute('data-status');
            filterDataByStatus(status);
            
            // Update active state
            statusFilters.forEach(f => f.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function filterDataByDate(period) {
    const tables = document.querySelectorAll('table[data-filterable="true"]');
    
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        const now = new Date();
        
        rows.forEach(row => {
            const dateCell = row.querySelector('[data-date]');
            if (dateCell) {
                const rowDate = new Date(dateCell.getAttribute('data-date'));
                let showRow = false;
                
                switch (period) {
                    case 'today':
                        showRow = isSameDay(rowDate, now);
                        break;
                    case 'week':
                        showRow = isSameWeek(rowDate, now);
                        break;
                    case 'month':
                        showRow = isSameMonth(rowDate, now);
                        break;
                    default:
                        showRow = true;
                }
                
                row.style.display = showRow ? '' : 'none';
            }
        });
    });
}

function filterDataByStatus(status) {
    const tables = document.querySelectorAll('table[data-filterable="true"]');
    
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const statusBadge = row.querySelector('.badge');
            if (statusBadge) {
                const rowStatus = statusBadge.textContent.toLowerCase();
                const showRow = status === 'all' || rowStatus === status.toLowerCase();
                row.style.display = showRow ? '' : 'none';
            }
        });
    });
}

// Date utility functions
function isSameDay(date1, date2) {
    return date1.toDateString() === date2.toDateString();
}

function isSameWeek(date1, date2) {
    const startOfWeek = new Date(date2);
    startOfWeek.setDate(date2.getDate() - date2.getDay());
    startOfWeek.setHours(0, 0, 0, 0);
    
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    endOfWeek.setHours(23, 59, 59, 999);
    
    return date1 >= startOfWeek && date1 <= endOfWeek;
}

function isSameMonth(date1, date2) {
    return date1.getMonth() === date2.getMonth() && 
           date1.getFullYear() === date2.getFullYear();
}

// Quick action handlers
function handleQuickAction(action, data = null) {
    switch (action) {
        case 'discharge-patient':
            dischargePatient(data);
            break;
        case 'generate-report':
            generateReport(data);
            break;
        case 'send-reminder':
            sendReminder(data);
            break;
        default:
            console.log('Action not implemented:', action);
    }
}

function dischargePatient(patientId) {
    if (confirm('Are you sure you want to discharge this patient?')) {
        window.location.href = `/demo/discharge-patient/${patientId}`;
    }
}

function generateReport(type) {
    showNotification(`Generating ${type} report...`, 'info');
    
    // Simulate report generation
    setTimeout(() => {
        showNotification(`${type} report generated successfully!`, 'success');
    }, 2000);
}

function sendReminder(target) {
    showNotification(`Reminder sent to ${target}`, 'info');
}

// Export dashboard functions
window.Dashboard = {
    filterDataByDate,
    filterDataByStatus,
    handleQuickAction,
    animateStatistics
};