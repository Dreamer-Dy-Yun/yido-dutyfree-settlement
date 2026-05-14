import { adminApiClient, tenantApiClient } from '../client/apiClient';
import {
  clearAdminSession,
  clearTenantSession,
  getAdminTokenPayload as readAdminTokenPayload,
  getTenantTokenPayload,
  hasAdminSession,
  hasTenantSession,
  storeAdminToken,
  storeTenantToken,
} from './authTokenStore';

export const searchCompany = async (name, businessNo) => {
  const params = {};
  if (name) params.name = name;
  if (businessNo) params.business_no = businessNo;

  const response = await tenantApiClient.get('/api/company/search', { params });
  return response.data;
};

export const registerCompany = async (companyData) => {
  const response = await tenantApiClient.post('/api/company/register', companyData);
  return response.data;
};

export const login = async (email, password, tenantId) => {
  const response = await tenantApiClient.post('/api/auth/login', {
    email,
    password,
    tenant_id: tenantId,
  });

  if (response.data.access_token) {
    storeTenantToken(response.data.access_token);
  }

  return response.data;
};

export const logout = async () => {
  try {
    await tenantApiClient.post('/api/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearTenantSession();
    window.location.href = '/';
  }
};

export const systemAdminLogin = async (email, password) => {
  const response = await tenantApiClient.post('/api/auth/system-admin/login', {
    email,
    password,
  });

  if (response.data.access_token) {
    storeAdminToken(response.data.access_token);
  }

  return response.data;
};

export const systemAdminLogout = async () => {
  try {
    await adminApiClient.post('/api/auth/system-admin/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearAdminSession();
    window.location.href = '/';
  }
};

export const getCurrentSystemAdmin = async () => {
  const response = await adminApiClient.get('/api/auth/system-admin/me');
  return response.data;
};

export const updateSystemAdminProfile = async (currentPassword, profile) => {
  const response = await adminApiClient.put('/api/auth/system-admin/me', {
    current_password: currentPassword,
    name: profile.name,
    alias: profile.alias,
    department: profile.department,
    contact: profile.contact,
  });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await tenantApiClient.get('/api/auth/me');
  return response.data;
};

export const verifyPassword = async (password) => {
  const response = await tenantApiClient.post('/api/auth/verify-password', { password });
  return response.data;
};

export const updateMyProfile = async (currentPassword, profile) => {
  const response = await tenantApiClient.put('/api/auth/me', {
    current_password: currentPassword,
    name: profile.name,
    department: profile.department,
    contact: profile.contact,
  });
  return response.data;
};

export const changePassword = async (oldPassword, newPassword, isTempPassword = false) => {
  const response = await tenantApiClient.post('/api/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
    is_temp_password: isTempPassword,
  });
  return response.data;
};

export const isAuthenticated = () => hasTenantSession();

export const getTokenPayload = () => getTenantTokenPayload();

export const getAdminTokenPayload = () => readAdminTokenPayload();

export const isAdminAuthenticated = () => hasAdminSession();

export const isSuperuser = () => isAdminAuthenticated();
