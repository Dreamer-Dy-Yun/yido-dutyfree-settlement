import axios from 'axios';
import {
  clearAdminSession,
  clearTenantSession,
  getAdminToken,
  getTenantToken,
} from './authTokenStore';
import { updateSessionTTLFromResponse } from './sessionTtlStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:10000';

const commonConfig = {
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
};

function attachAuthInterceptor(client, getToken) {
  client.interceptors.request.use(
    (config) => {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        config._hadAuthToken = true;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );
}

function attachSessionInterceptor(client, onUnauthorized) {
  client.interceptors.response.use(
    (response) => {
      updateSessionTTLFromResponse(response);
      return response;
    },
    (error) => {
      if (error.response?.status === 401 && error.config?._hadAuthToken === true) {
        onUnauthorized();
      }
      return Promise.reject(error);
    }
  );
}

export const tenantApiClient = axios.create(commonConfig);
attachAuthInterceptor(tenantApiClient, getTenantToken);
attachSessionInterceptor(tenantApiClient, () => {
  clearTenantSession();
  window.location.href = '/';
});

export const adminApiClient = axios.create(commonConfig);
attachAuthInterceptor(adminApiClient, getAdminToken);
attachSessionInterceptor(adminApiClient, () => {
  clearAdminSession();
  window.location.href = '/admin/login';
});
