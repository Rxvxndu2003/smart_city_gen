import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const authApi = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  register: (userData: any) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
};

export const projectsApi = {
  list: (params?: any) => api.get('/projects', { params }),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: any) => api.post('/projects', data),
  update: (id: number, data: any) => api.put(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
  statistics: () => api.get('/projects/statistics'),
};

export const validationApi = {
  validate: (projectId: number) => api.post('/validation/check', { project_id: projectId }),
  checkProject: (projectId: number, additionalData?: any) =>
    api.post('/validation/check', { project_id: projectId, additional_data: additionalData }),
  getReports: (projectId: number) => api.get(`/validation/reports/${projectId}`),
  quickCheck: (params: {
    site_area: number;
    project_type: string;
    district?: string;
  }) => api.get('/validation/quick-check', { params }),
};

export const approvalsApi = {
  submit: (projectId: number) => api.post('/approvals/submit', { project_id: projectId }),
  approve: (projectId: number, data: { action: string; comment?: string }) =>
    api.post('/approvals/approve', { project_id: projectId, ...data }),
  getPending: () => api.get('/approvals/pending'),
  submitReview: (approvalId: number, data: { approved: boolean; comments?: string }) =>
    api.post(`/approvals/${approvalId}/review`, data),
  getHistory: (projectId: number) => api.get(`/approvals/project/${projectId}/history`),
  getStats: () => api.get('/approvals/stats'),
};

export const generationApi = {
  generate: (layoutId: number, params?: any) =>
    api.post('/generation/generate', { layout_id: layoutId, ...params }),
  getJob: (jobId: number) => api.get(`/generation/jobs/${jobId}`),
  getProjectJobs: (projectId: number) => api.get(`/generation/projects/${projectId}/jobs`),
  textToCity: (projectId: number, data: { prompt: string; enable_ai_enhancement: boolean; grid_size_preset?: string }) =>
    api.post(`/generation/${projectId}/text-to-city`, data),
};

export const mlModelsApi = {
  predict: (data: any) => api.post('/ml-models/predict', data),
  getRecommendations: (projectData: any) =>
    api.post('/ml-models/recommendations', projectData),
};

export const usersApi = {
  me: () => api.get('/users/me'),
  update: (data: any) => api.put('/users/me', data),
  list: (params?: any) => api.get('/users', { params }),
  get: (id: number) => api.get(`/users/${id}`),
};

export const blockchainApi = {
  getStatus: () => api.get('/blockchain/status'),
  storeProject: (projectId: number, recordType: string, metadata?: any) =>
    api.post('/blockchain/store', {
      project_id: projectId,
      record_type: recordType,
      metadata: metadata || {},
    }),
  verifyRecord: (projectId: number, dataHash: string) =>
    api.post('/blockchain/verify', {
      project_id: projectId,
      data_hash: dataHash,
    }),
  getProjectRecords: (projectId: number) =>
    api.get(`/blockchain/project/${projectId}/records`),
  getIpfsData: (ipfsHash: string) =>
    api.get(`/blockchain/ipfs/${ipfsHash}`),
};

export default api;
