// File Path: meeting_app/static/js/main.js

// Global variables
let currentUser = null;
let notifications = [];

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadUserPreferences();
});

// Initialize the application
function initializeApp() {
    console.log('Meeting App initialized');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize modals
    initializeModals();
    
    // Check for auto-dismissible alerts
    setupAlerts();
    
    // Setup form validation
    setupFormValidation();
    
    // Initialize dashboard if on dashboard page
    if (window.location.pathname.includes('dashboard')) {
        initializeDashboard();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navbar toggle for mobile
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            const navbar = document.querySelector('.navbar-collapse');
            navbar.classList.toggle('show');
        });
    }
    
    // Dropdown menus
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdownMenu = this.nextElementSibling;
            if (dropdownMenu) {
                dropdownMenu.classList.toggle('show');
            }
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target) && !dropdown.previousElementSibling.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
    });
    
    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
    
    // Button click animations
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            animateButton(this);
        });
    });
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize modals
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const targetModal = document.querySelector(this.getAttribute('data-bs-target'));
            if (targetModal) {
                const modal = new bootstrap.Modal(targetModal);
                modal.show();
            }
        });
    });
}

// Setup alerts
function setupAlerts() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            fadeOut(alert);
        }, 5000);
    });
}

// Setup form validation
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Initialize dashboard
function initializeDashboard() {
    // Load dashboard data
    loadDashboardData();
    
    // Setup dashboard refresh
    setInterval(loadDashboardData, 300000); // Refresh every 5 minutes
    
    // Setup real-time updates
    setupRealTimeUpdates();
}

// Load dashboard data
function loadDashboardData() {
    // This would typically make AJAX calls to load dashboard data
    console.log('Loading dashboard data...');
    
    // Update stats
    updateDashboardStats();
    
    // Update charts
    updateCharts();
    
    // Update notifications
    updateNotifications();
}

// Update dashboard stats
function updateDashboardStats() {
    const statCards = document.querySelectorAll('.dashboard-stat');
    statCards.forEach(card => {
        const value = card.querySelector('.stat-value');
        if (value) {
            animateCounter(value);
        }
    });
}

// Update charts (placeholder for chart libraries)
function updateCharts() {
    // This would integrate with Chart.js or similar
    console.log('Updating charts...');
}

// Update notifications
function updateNotifications() {
    const notificationBadge = document.querySelector('.notification-badge');
    if (notificationBadge) {
        // This would fetch notifications from the server
        const notificationCount = notifications.length;
        notificationBadge.textContent = notificationCount;
        
        if (notificationCount > 0) {
            notificationBadge.style.display = 'inline-block';
        } else {
            notificationBadge.style.display = 'none';
        }
    }
}

// Setup real-time updates
function setupRealTimeUpdates() {
    // This would set up WebSocket connections or polling
    console.log('Setting up real-time updates...');
}

// Form validation
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        if (input.hasAttribute('required') && !input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else if (input.type === 'email' && input.value && !isValidEmail(input.value)) {
            showFieldError(input, 'Please enter a valid email address');
            isValid = false;
        } else if (input.type === 'password' && input.value && input.value.length < 8) {
            showFieldError(input, 'Password must be at least 8 characters long');
            isValid = false;
        } else {
            clearFieldError(input);
        }
    });
    
    return isValid;
}

// Show field error
function showFieldError(input, message) {
    input.classList.add('is-invalid');
    let errorDiv = input.nextElementSibling;
    
    if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    
    errorDiv.textContent = message;
}

// Clear field error
function clearFieldError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
        errorDiv.remove();
    }
}

// Email validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Button animation
function animateButton(button) {
    button.classList.add('animate-click');
    setTimeout(() => {
        button.classList.remove('animate-click');
    }, 150);
}

// Counter animation
function animateCounter(element) {
    const target = parseInt(element.textContent);
    const increment = target / 20;
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        element.textContent = Math.floor(current);
        
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        }
    }, 50);
}

// Fade out animation
function fadeOut(element) {
    element.style.opacity = '0';
    element.style.transition = 'opacity 0.5s ease';
    
    setTimeout(() => {
        element.remove();
    }, 500);
}

// Load user preferences
function loadUserPreferences() {
    // This would load user preferences from localStorage or server
    const preferences = {
        theme: 'light',
        notifications: true,
        language: 'en'
    };
    
    applyUserPreferences(preferences);
}

// Apply user preferences
function applyUserPreferences(preferences) {
    if (preferences.theme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    if (!preferences.notifications) {
        // Disable notifications
        console.log('Notifications disabled');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-toast`;
    notification.textContent = message;
    
    // Position notification
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    notification.style.transition = 'all 0.3s ease';
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Show loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    spinner.setAttribute('role', 'status');
    
    element.insertBefore(spinner, element.firstChild);
    element.disabled = true;
}

// Hide loading spinner
function hideLoading(element) {
    const spinner = element.querySelector('.spinner-border');
    if (spinner) {
        spinner.remove();
    }
    element.disabled = false;
}

// AJAX helper function
function ajaxRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        // Add CSRF token for POST requests
        if (method === 'POST' || method === 'PUT' || method === 'DELETE') {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken.value);
            }
        }
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error(xhr.statusText));
            }
        };
        
        xhr.onerror = function() {
            reject(new Error('Network error'));
        };
        
        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    });
}

// Utility functions
const utils = {
    // Format date
    formatDate: function(date) {
        return new Date(date).toLocaleDateString();
    },
    
    // Format time
    formatTime: function(date) {
        return new Date(date).toLocaleTimeString();
    },
    
    // Debounce function
    debounce: function(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },
    
    // Throttle function
    throttle: function(func, delay) {
        let timeoutId;
        let lastExecTime = 0;
        return function(...args) {
            const currentTime = Date.now();
            
            if (currentTime - lastExecTime > delay) {
                func.apply(this, args);
                lastExecTime = currentTime;
            } else {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                    lastExecTime = Date.now();
                }, delay - (currentTime - lastExecTime));
            }
        };
    },
    
    // Copy to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(() => {
            showNotification('Failed to copy to clipboard', 'error');
        });
    }
};

// Export functions for use in other scripts
window.MeetingApp = {
    showNotification,
    showLoading,
    hideLoading,
    ajaxRequest,
    utils
};

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .animate-click {
        transform: scale(0.95);
        transition: transform 0.1s ease;
    }
    
    .notification-toast {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-radius: 8px;
        border: none;
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .slide-up {
        animation: slideUp 0.5s ease-out;
    }
    
    @keyframes slideUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .dark-theme {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .dark-theme .card {
        background-color: #2d2d2d;
        border-color: #404040;
    }
    
    .dark-theme .navbar {
        background-color: #2d2d2d !important;
    }
`;
document.head.appendChild(style);