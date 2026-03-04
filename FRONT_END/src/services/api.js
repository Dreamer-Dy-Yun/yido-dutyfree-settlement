import axios from 'axios';
import { updateSessionTTLFromResponse } from './sessionTTL';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const commonConfig = {
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
};

// 테넌트(일반)용 - access_token 사용
const api = axios.create(commonConfig);
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      config._hadAuthToken = true;
    }
    return config;
  },
  (e) => Promise.reject(e)
);
api.interceptors.response.use(
  (res) => {
    updateSessionTTLFromResponse(res);
    return res;
  },
  (error) => {
    if (error.response?.status === 401 && error.config?._hadAuthToken === true) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('tenant_id');
      localStorage.removeItem('tenant_schema');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// 시스템 관리자 전용 - admin_access_token만 사용
export const adminApi = axios.create(commonConfig);
adminApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      config._hadAuthToken = true;
    }
    return config;
  },
  (e) => Promise.reject(e)
);
adminApi.interceptors.response.use(
  (res) => {
    updateSessionTTLFromResponse(res);
    return res;
  },
  (error) => {
    if (error.response?.status === 401 && error.config?._hadAuthToken === true) {
      localStorage.removeItem('admin_access_token');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export default api;
