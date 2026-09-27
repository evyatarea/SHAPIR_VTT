/**
 * API Client Service
 * Axios configuration for backend API communication
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Create axios instance with default configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - Add auth token
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor - Handle errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * API Service Methods
 */
export const apiService = {
  /**
   * Authentication endpoints
   */
  auth: {
    login: (username: string, password: string) =>
      apiClient.post('/api/auth/login', { username, password }),
    logout: () => apiClient.post('/api/auth/logout'),
    getUser: () => apiClient.get('/api/auth/user'),
    verifyToken: () => apiClient.get('/api/auth/verify-token'),
  },

  /**
   * Recordings endpoints
   */
  recordings: {
    upload: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post('/api/recordings/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    list: (limit: number = 50, offset: number = 0) =>
      apiClient.get(`/api/recordings/?limit=${limit}&offset=${offset}`),
    get: (id: string) => apiClient.get(`/api/recordings/${id}`),
    getTranscript: (id: string) => apiClient.get(`/api/recordings/${id}/transcript`),
    transcribe: (id: string) => apiClient.post(`/api/recordings/${id}/transcribe`),
    delete: (id: string) => apiClient.delete(`/api/recordings/${id}`),
  },

  /**
   * Templates endpoints
   */
  templates: {
    list: (activeOnly: boolean = true, format?: string) => {
      let url = `/api/templates/?active_only=${activeOnly}`;
      if (format) url += `&output_format=${format}`;
      return apiClient.get(url);
    },
    get: (id: string) => apiClient.get(`/api/templates/${id}`),
    create: (template: any) => apiClient.post('/api/templates/', template),
    update: (id: string, template: any) =>
      apiClient.put(`/api/templates/${id}`, template),
    delete: (id: string) => apiClient.delete(`/api/templates/${id}`),
    seedDefaults: () => apiClient.post('/api/templates/seed/default'),
  },

  /**
   * Summaries endpoints
   */
  summaries: {
    create: (recordingId: string, templateId: string, context?: any) =>
      apiClient.post('/api/summaries/', {
        recording_id: recordingId,
        template_id: templateId,
        context,
      }),
    list: (recordingId?: string, templateId?: string, limit: number = 50, offset: number = 0) => {
      let url = `/api/summaries/?limit=${limit}&offset=${offset}`;
      if (recordingId) url += `&recording_id=${recordingId}`;
      if (templateId) url += `&template_id=${templateId}`;
      return apiClient.get(url);
    },
    get: (id: string) => apiClient.get(`/api/summaries/${id}`),
    download: (id: string, format: 'pdf' | 'docx' | 'xlsx' | 'txt' = 'txt') =>
      apiClient.get(`/api/summaries/${id}/download?format=${format}`, {
        responseType: 'blob',
      }),
    delete: (id: string) => apiClient.post(`/api/summaries/${id}/delete`),
    batchCreate: (recordingIds: string[], templateId: string) =>
      apiClient.post('/api/summaries/batch/create', {
        recording_ids: recordingIds,
        template_id: templateId,
      }),
  },
};
