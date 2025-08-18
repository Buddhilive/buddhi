import axios from 'axios';

const DJANGO_BACKEND = process.env.DJANGO_BACKEND || 'http://localhost:8000';
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? DJANGO_BACKEND
  : 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to include CSRF token if needed
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      try {
        await api.post('/api/auth/refresh-token/');
        return api(original);
      } catch (refreshError) {
        // Redirect to login page
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data: any) => api.post('/api/auth/register/', data),
  login: (data: any) => api.post('/api/auth/login/', data),
  logout: () => api.post('/api/auth/logout/'),
  verifyEmail: (token: string) => api.get(`/api/auth/verify-email/${token}/`),
  requestPasswordReset: (email: string) => api.post('/api/auth/password-reset/request/', { email }),
  confirmPasswordReset: (data: any) => api.post('/api/auth/password-reset/confirm/', data),
  getProfile: () => api.get('/api/auth/profile/'),
  refreshToken: () => api.post('/api/auth/refresh-token/'),
};
