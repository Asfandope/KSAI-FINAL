// Export shared configurations
export * from "./eslint.js";

// Common constants
export const SUPPORTED_LANGUAGES = ['en', 'ta'] as const;
export const TOPICS = ['Politics', 'Environmentalism', 'SKCRF', 'Educational Trust'] as const;
export const CONTENT_TYPES = ['pdf', 'youtube'] as const;
export const USER_ROLES = ['user', 'admin'] as const;

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    ME: '/auth/me',
  },
  CHAT: {
    SEND: '/chat',
  },
  TOPICS: {
    LIST: '/topics',
    CATEGORIES: '/topics/categories',
  },
  ADMIN: {
    CONTENT: '/admin/content',
    DASHBOARD: '/admin/dashboard',
  },
} as const;

// UI constants
export const BREAKPOINTS = {
  MOBILE: '320px',
  TABLET: '768px',
  DESKTOP: '1024px',
  WIDE: '1280px',
} as const;

export const COLORS = {
  PRIMARY: '#2563EB',
  SECONDARY: '#EFF6FF', 
  ACCENT: '#F59E0B',
  SUCCESS: '#10B981',
  WARNING: '#FBBF24',
  ERROR: '#EF4444',
} as const;