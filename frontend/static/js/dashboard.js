// Authentication token
let authToken = localStorage.getItem('authToken');
const API_BASE = '/api';

// Check if user is authenticated
if (!authToken) {
    window.location.href = '/login.html';
}

// API request helper
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    try {
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            // Unauthorized - redirect to login
            localStorage.removeItem('authToken');
            window.location.href = '/login.html';
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        return null;
    }
}

// Load user information
async function loadUserInfo() {
    const user = await apiRequest('/auth/me');
    if (user) {
        document.getElementById('username').textContent = user.username;
    }
}

// Check service health
async function checkServiceHealth(showLoading = false) {
    if (showLoading) {
        // Show loading state
        const statusElements = document.querySelectorAll('.service-status span:last-child');
        statusElements.forEach(el => {
            if (el.textContent !== 'Not Registered') {
                el.innerHTML = '<span class="loading-spinner"></span> Checking...';
            }
        });
    }
    
    try {
        const health = await apiRequest('/health/services');
        if (health) {
            // Handle empty services case
            if (health.services && Object.keys(health.services).length > 0) {
                updateServiceStatuses(health.services);
                updateSystemMetrics(health.services);
            } else {
                // No services registered - show all as unknown
                updateServiceStatuses({});
                updateSystemMetrics({});
            }
        } else {
            // API request failed - show error state
            throw new Error('Failed to fetch service health');
        }
    } catch (error) {
        handleApiError(error, 'checkServiceHealth');
        updateServiceStatuses({});
    }
}

// Update service status indicators
function updateServiceStatuses(services) {
    const serviceMap = {
        'seafile': 'file-storage',
        'jellyfin': 'media-server',
        'wiki': 'productivity',
        'gitea': 'dev-tools',
        'prometheus': 'monitoring',
        'grafana': 'monitoring',
        'vaultwarden': 'security'
    };
    
    // Default service types to show
    const defaultServiceTypes = ['file-storage', 'media-server', 'productivity', 'dev-tools', 'monitoring', 'security'];
    
    // If no services, set all to unknown
    if (Object.keys(services).length === 0) {
        defaultServiceTypes.forEach(serviceType => {
            const statusElement = document.getElementById(`status-${serviceType}`);
            if (statusElement) {
                const indicator = statusElement.querySelector('.status-indicator');
                const text = statusElement.querySelector('span:last-child');
                
                indicator.className = 'status-indicator unknown';
                text.textContent = 'Not Registered';
            }
        });
        return;
    }
    
    // Update services that are registered
    Object.keys(services).forEach(serviceName => {
        const serviceType = serviceMap[serviceName.toLowerCase()] || serviceName.toLowerCase();
        const statusElement = document.getElementById(`status-${serviceType}`);
        if (statusElement) {
            const status = services[serviceName].status || 'unknown';
            const indicator = statusElement.querySelector('.status-indicator');
            const text = statusElement.querySelector('span:last-child');
            
            indicator.className = `status-indicator ${status}`;
            text.textContent = status === 'healthy' ? 'Online' : 
                              status === 'unhealthy' ? 'Offline' : 'Unknown';
        }
    });
    
    // Set unregistered services to "Not Registered"
    defaultServiceTypes.forEach(serviceType => {
        const statusElement = document.getElementById(`status-${serviceType}`);
        if (statusElement) {
            const indicator = statusElement.querySelector('.status-indicator');
            const text = statusElement.querySelector('span:last-child');
            
            // Check if this service type was updated above
            const wasUpdated = Object.keys(services).some(name => {
                const mappedType = serviceMap[name.toLowerCase()] || name.toLowerCase();
                return mappedType === serviceType;
            });
            
            if (!wasUpdated && indicator.className.includes('unknown') && text.textContent === 'Checking...') {
                text.textContent = 'Not Registered';
            }
        }
    });
}

// Update system metrics
function updateSystemMetrics(services) {
    const serviceList = Object.values(services);
    const total = serviceList.length;
    const healthy = serviceList.filter(s => s.status === 'healthy').length;
    const unhealthy = serviceList.filter(s => s.status === 'unhealthy').length;
    
    document.getElementById('total-services').textContent = total;
    document.getElementById('healthy-services').textContent = healthy;
    document.getElementById('unhealthy-services').textContent = unhealthy;
}

// Service URL cache (will be populated from backend)
let serviceUrlCache = {
    'file-storage': 'http://localhost:8001',
    'media-server': 'http://localhost:8096',
    'productivity': 'http://localhost:8002',
    'dev-tools': 'http://localhost:3000',
    'monitoring': 'http://localhost:3001',
    'security': 'http://localhost:8080'
};

// Map internal Docker URLs to external localhost URLs
function mapInternalToExternalUrl(internalUrl) {
    if (!internalUrl) return null;
    
    // Mapping of internal Docker service names to external ports
    const servicePortMap = {
        'seafile': '8001',
        'jellyfin': '8096',
        'bookstack': '8002',
        'gitea': '3000',
        'grafana': '3001',
        'vaultwarden': '8080',
        'prometheus': '9090'
    };
    
    // Extract service name from URL (e.g., "http://bookstack:80" -> "bookstack")
    const urlMatch = internalUrl.match(/https?:\/\/([^:]+)/);
    if (urlMatch) {
        const serviceName = urlMatch[1];
        const externalPort = servicePortMap[serviceName];
        if (externalPort) {
            return `http://localhost:${externalPort}`;
        }
    }
    
    // If no mapping found, return original URL (might already be external)
    return internalUrl;
}

// Load service URLs from backend
async function loadServiceUrls() {
    try {
        const services = await apiRequest('/services');
        if (services && Array.isArray(services)) {
            const serviceTypeMap = {
                'file_storage': 'file-storage',
                'media_server': 'media-server',
                'productivity': 'productivity',
                'dev_tools': 'dev-tools',
                'monitoring': 'monitoring',
                'security': 'security'
            };
            
            services.forEach(service => {
                const serviceType = serviceTypeMap[service.service_type];
                if (serviceType && service.base_url) {
                    // Map internal Docker URL to external localhost URL
                    const externalUrl = mapInternalToExternalUrl(service.base_url);
                    if (externalUrl) {
                        serviceUrlCache[serviceType] = externalUrl;
                    }
                }
            });
        }
    } catch (error) {
        console.warn('Could not load service URLs from backend, using defaults', error);
    }
}

// Open service
async function openService(serviceType) {
    // Try to get URL from cache or backend
    let url = serviceUrlCache[serviceType];
    
    if (!url) {
        // Try to fetch from backend
        await loadServiceUrls();
        url = serviceUrlCache[serviceType];
    }
    
    if (url) {
        try {
            window.open(url, '_blank');
            showNotification('Opening service...', 'info');
        } catch (error) {
            showNotification('Failed to open service. Please check if pop-ups are blocked.', 'error');
        }
    } else {
        showNotification('Service URL not configured. Please contact an administrator.', 'error');
    }
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const notificationArea = document.getElementById('notification-area');
    if (!notificationArea) return;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    }[type] || 'ℹ';
    
    notification.innerHTML = `
        <span>${icon}</span>
        <span>${message}</span>
        <span class="notification-close">&times;</span>
    `;
    
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.remove();
    });
    
    notificationArea.appendChild(notification);
    
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }
}

// Help modal
function setupHelpModal() {
    const helpBtn = document.getElementById('help-btn');
    const helpModal = document.getElementById('help-modal');
    const closeBtn = helpModal.querySelector('.modal-close');
    
    if (!helpBtn || !helpModal) return;
    
    helpBtn.addEventListener('click', () => {
        helpModal.classList.add('show');
    });
    
    closeBtn.addEventListener('click', () => {
        helpModal.classList.remove('show');
    });
    
    helpModal.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.classList.remove('show');
        }
    });
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger if typing in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Help modal (?) or (H)
        if (e.key === '?' || (e.key === 'h' && !e.ctrlKey && !e.metaKey)) {
            e.preventDefault();
            const helpModal = document.getElementById('help-modal');
            if (helpModal) {
                if (helpModal.classList.contains('show')) {
                    helpModal.classList.remove('show');
                } else {
                    helpModal.classList.add('show');
                }
            }
        }
        
        // Refresh (R)
        if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            const refreshBtn = document.getElementById('refresh-btn');
            if (refreshBtn) {
                refreshBtn.click();
            }
        }
        
        // Close modals (Esc)
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => modal.classList.remove('show'));
        }
    });
}

// Enhanced error handling
function handleApiError(error, context = '') {
    console.error(`API error${context ? ` in ${context}` : ''}:`, error);
    
    let message = 'An error occurred. Please try again.';
    
    if (error.message) {
        if (error.message.includes('401')) {
            message = 'Your session has expired. Please log in again.';
            setTimeout(() => {
                localStorage.removeItem('authToken');
                window.location.href = '/login.html';
            }, 2000);
        } else if (error.message.includes('403')) {
            message = 'You do not have permission to perform this action.';
        } else if (error.message.includes('404')) {
            message = 'The requested resource was not found.';
        } else if (error.message.includes('500')) {
            message = 'Server error. Please contact an administrator.';
        } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
            message = 'Network error. Please check your connection.';
        }
    }
    
    showNotification(message, 'error');
}

// Logout
document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('authToken');
    showNotification('Logging out...', 'info');
    setTimeout(() => {
        window.location.href = '/login.html';
    }, 500);
});

// Refresh button handler
function setupRefreshButton() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.disabled = true;
            refreshBtn.textContent = 'Refreshing...';
            await checkServiceHealth(true);
            showNotification('Service status refreshed', 'success', 2000);
            refreshBtn.disabled = false;
            refreshBtn.textContent = 'Refresh';
        });
    }
}

// Initialize dashboard
async function init() {
    try {
        await loadUserInfo();
        await loadServiceUrls();
        await checkServiceHealth();
        
        setupHelpModal();
        setupKeyboardShortcuts();
        setupRefreshButton();
        
        // Refresh health status every 30 seconds
        setInterval(() => checkServiceHealth(false), 30000);
        
        showNotification('Dashboard loaded successfully', 'success', 3000);
    } catch (error) {
        handleApiError(error, 'init');
    }
}

// Start when page loads
document.addEventListener('DOMContentLoaded', init);


