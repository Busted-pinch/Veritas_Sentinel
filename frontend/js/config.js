// Configuration file for Veritas Sentinel Frontend
// Place this file in js/config.js and import it in all other JS files

const CONFIG = {
    // API Configuration
    API_BASE_URL: 'http://localhost:8000',
    
    // Endpoints
    ENDPOINTS: {
        // Auth
        LOGIN: '/auth/login',
        REGISTER: '/auth/register',
        ME: '/auth/me',
        
        // Admin
        USERS: '/api/admin/users',
        ALERTS: '/api/admin/alerts',
        RISK_TREND_GLOBAL: '/api/admin/risk-trend-global',
        GEO_HOTSPOTS: '/api/admin/geo-hotspots',
        
        // Agent/Intelligence
        INTEL: '/api/agent/intel',
        RISK_TREND: '/api/agent/risk-trend',
        SPECULATION: '/api/agent/speculate',
        BEHAVIOR: '/api/agent/behavior-summary',
        INVESTIGATION: '/api/agent/investigation',
        
        // User
        TRANSACTION_NEW: '/api/transaction/new',
        ML_PREDICT: '/ml/predict'
    },
    
    // Chart Configuration
    CHARTS: {
        DEFAULT_COLORS: {
            primary: 'rgb(99, 102, 241)',
            success: 'rgb(16, 185, 129)',
            danger: 'rgb(239, 68, 68)',
            warning: 'rgb(245, 158, 11)',
            info: 'rgb(59, 130, 246)'
        },
        ANIMATION_DURATION: 1000,
        TENSION: 0.4
    },
    
    // Map Configuration
    MAP: {
        DEFAULT_CENTER: [20, 0],
        DEFAULT_ZOOM: 2,
        TILE_LAYER: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        ATTRIBUTION: '© OpenStreetMap contributors'
    },
    
    // UI Configuration
    UI: {
        NOTIFICATION_DURATION: 3000,
        DEBOUNCE_DELAY: 500,
        DEFAULT_PAGE_LIMIT: 100
    },
    
    // Risk Level Colors
    RISK_COLORS: {
        low: '#3b82f6',
        medium: '#f59e0b',
        high: '#f97316',
        critical: '#ef4444'
    },
    
    // Status Colors
    STATUS_COLORS: {
        active: '#10b981',
        inactive: '#ef4444',
        pending: '#f59e0b',
        open: '#f59e0b',
        closed: '#10b981'
    }
};

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return CONFIG.API_BASE_URL + endpoint;
}

// Helper function to get endpoint path
function getEndpoint(name) {
    return CONFIG.ENDPOINTS[name] || '';
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}