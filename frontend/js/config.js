// Application Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/v1',
    VERSION: '1.0.0',
    
    // API Endpoints
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/auth/login',
            LOGOUT: '/auth/logout',
            REFRESH: '/auth/refresh',
            REGISTER: '/auth/register'
        },
        EVENTS: {
            LIST: '/events',
            CREATE: '/events',
            UPDATE: '/events/{id}',
            DELETE: '/events/{id}',
            GET: '/events/{id}'
        },
        TASKS: {
            LIST: '/tasks',
            CREATE: '/tasks',
            UPDATE: '/tasks/{id}',
            DELETE: '/tasks/{id}',
            GET: '/tasks/{id}'
        },
        USERS: {
            PROFILE: '/users/me',
            UPDATE: '/users/me'
        }
    },
    
    // Default Settings
    DEFAULTS: {
        PAGE_SIZE: 20,
        DATE_FORMAT: 'YYYY-MM-DD',
        TIME_FORMAT: 'HH:mm',
        TIMEZONE: 'UTC',
        CALENDAR_VIEW: 'week',
        REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
    },
    
    // Calendar Configuration
    CALENDAR: {
        VIEWS: ['month', 'week', 'day'],
        COLORS: {
            personal: '#3b82f6',
            work: '#10b981',
            projects: '#f59e0b',
            default: '#64748b'
        },
        HOURS_START: 6,
        HOURS_END: 22
    },
    
    // Task Configuration  
    TASKS: {
        PRIORITIES: [
            { value: 'low', label: 'Low', color: '#10b981' },
            { value: 'medium', label: 'Medium', color: '#f59e0b' },
            { value: 'high', label: 'High', color: '#ef4444' }
        ],
        STATUSES: [
            { value: 'pending', label: 'Pending' },
            { value: 'in_progress', label: 'In Progress' },
            { value: 'completed', label: 'Completed' },
            { value: 'cancelled', label: 'Cancelled' }
        ]
    },
    
    // UI Configuration
    UI: {
        MOBILE_BREAKPOINT: 768,
        TABLET_BREAKPOINT: 1024,
        SIDEBAR_WIDTH: 280,
        ANIMATION_DURATION: 150
    },
    
    // Storage Keys
    STORAGE_KEYS: {
        TOKEN: 'psychic_tribble_token',
        REFRESH_TOKEN: 'psychic_tribble_refresh_token',
        USER: 'psychic_tribble_user',
        SETTINGS: 'psychic_tribble_settings',
        CALENDAR_VIEW: 'psychic_tribble_calendar_view',
        SIDEBAR_STATE: 'psychic_tribble_sidebar_state'
    },
    
    // Error Messages
    MESSAGES: {
        NETWORK_ERROR: 'Network error. Please check your connection.',
        UNAUTHORIZED: 'Please log in to continue.',
        FORBIDDEN: 'You do not have permission to perform this action.',
        NOT_FOUND: 'The requested resource was not found.',
        SERVER_ERROR: 'Server error. Please try again later.',
        VALIDATION_ERROR: 'Please check your input and try again.',
        SUCCESS_CREATE: 'Created successfully!',
        SUCCESS_UPDATE: 'Updated successfully!',
        SUCCESS_DELETE: 'Deleted successfully!'
    }
};

// Environment-specific overrides
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    CONFIG.API_BASE_URL = 'http://localhost:8000/v1';
} else if (window.location.hostname.includes('staging')) {
    CONFIG.API_BASE_URL = 'https://staging-api.psychic-tribble.com/v1';
} else {
    CONFIG.API_BASE_URL = 'https://api.psychic-tribble.com/v1';
}

// Export configuration
window.CONFIG = CONFIG;
