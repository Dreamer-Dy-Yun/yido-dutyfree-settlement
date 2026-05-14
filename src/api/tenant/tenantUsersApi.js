import { tenantApiClient } from '../client/apiClient';

export const getTenantUsers = async (skip = 0, limit = 100, isActive = null) => {
  const params = { skip, limit };
  if (isActive !== null) params.is_active = isActive;

  const response = await tenantApiClient.get('/api/tenant/users', { params });
  return response.data;
};

export const createTenantUser = async (userData) => {
  const response = await tenantApiClient.post('/api/tenant/users', userData);
  return response.data;
};

export const getTenantUser = async (userId) => {
  const response = await tenantApiClient.get(`/api/tenant/users/${userId}`);
  return response.data;
};

export const updateTenantUser = async (userId, userData) => {
  const response = await tenantApiClient.put(`/api/tenant/users/${userId}`, userData);
  return response.data;
};

export const userActivate = async (userId, isActive) => {
  const response = await tenantApiClient.patch(`/api/tenant/users/${userId}/activation`, {
    is_active: isActive,
  });
  return response.data;
};

export const deleteTenantUser = async (userId) => {
  const response = await tenantApiClient.delete(`/api/tenant/users/${userId}`);
  return response.data;
};

export const resetUserPassword = async (userId) => {
  const response = await tenantApiClient.post(`/api/tenant/users/${userId}/reset-password`);
  return response.data;
};
