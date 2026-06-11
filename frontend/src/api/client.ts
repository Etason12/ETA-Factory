import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:5000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === 'object' && 'total' in response.data && 'page' in response.data) {
      if (!response.data.items) {
        const arrayKey = Object.keys(response.data).find(key => Array.isArray(response.data[key]));
        if (arrayKey) {
          response.data.items = response.data[arrayKey];
        } else {
          response.data.items = [];
        }
      }
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Log 422 errors for debugging
    if (error.response?.status === 422) {
      console.error('422 Validation Error:', error.config?.url, error.response?.data);
    }

    const isLoginRequest = originalRequest.url?.includes('/auth/login');
    if (error.response?.status === 401 && !originalRequest._retry && !isLoginRequest) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const { data } = await axios.post('http://localhost:5000/api/v1/auth/refresh', { refresh_token: refreshToken });
          localStorage.setItem('access_token', data.access_token);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          }
          return apiClient(originalRequest);
        } else {
          throw new Error('No refresh token available');
        }
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
