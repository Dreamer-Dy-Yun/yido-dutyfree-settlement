import { adminApiClient } from './client';

export const getSystemStats = async () => {
  const response = await adminApiClient.get('/api/system-admin/dashboard/stats');
  return response.data;
};

export const getTenants = async (params = {}) => {
  const { skip = 0, limit = 100, is_active, search } = params;
  const response = await adminApiClient.get('/api/system-admin/tenants', {
    params: {
      skip,
      limit,
      ...(is_active !== undefined && { is_active }),
      ...(search && { search }),
    },
  });
  return response.data;
};

export const getTenantDetail = async (tenantId) => {
  const response = await adminApiClient.get(`/api/system-admin/tenants/${tenantId}`);
  return response.data;
};

export const getPendingTenants = async (params = {}) => {
  const { skip = 0, limit = 100 } = params;
  const data = await getTenants({ skip, limit, is_active: false });

  return {
    pending_tenants: data.tenants || [],
    total: data.total,
    skip: data.skip,
    limit: data.limit,
  };
};

export const approveTenant = async (tenantId, reason = null) => {
  const response = await adminApiClient.post(`/api/system-admin/tenants/${tenantId}/approve`, {
    reason,
  });
  return response.data;
};

export const rejectTenant = async (tenantId, reason) => {
  const response = await adminApiClient.post(`/api/system-admin/tenants/${tenantId}/reject`, {
    reason,
  });
  return response.data;
};

export const updateTenant = async (tenantId, updateData) => {
  const response = await adminApiClient.put(`/api/system-admin/tenants/${tenantId}`, updateData);
  return response.data;
};

export const deleteTenant = async (tenantId, reason) => {
  const response = await adminApiClient.delete(`/api/system-admin/tenants/${tenantId}`, {
    data: { reason },
  });
  return response.data;
};

export const getServiceAccounts = async (params = {}) => {
  const { skip = 0, limit = 100, role, is_active } = params;
  const response = await adminApiClient.get('/api/system-admin/service-accounts', {
    params: {
      skip,
      limit,
      ...(role && { role }),
      ...(is_active !== undefined && { is_active }),
    },
  });
  return response.data;
};

export const getServiceAccountDetail = async (accountId) => {
  const response = await adminApiClient.get(`/api/system-admin/service-accounts/${accountId}`);
  return response.data;
};

export const createServiceAccount = async (accountData) => {
  const response = await adminApiClient.post('/api/system-admin/service-accounts', accountData);
  return response.data;
};

export const updateServiceAccount = async (accountId, updateData) => {
  const response = await adminApiClient.put(`/api/system-admin/service-accounts/${accountId}`, updateData);
  return response.data;
};

export const deleteServiceAccount = async (accountId) => {
  const response = await adminApiClient.delete(`/api/system-admin/service-accounts/${accountId}`);
  return response.data;
};

export const getLlmApiKeys = async (params = {}) => {
  const { skip = 0, limit = 100, llm_provider, is_active } = params;
  const response = await adminApiClient.get('/api/system-admin/llm-api-keys', {
    params: {
      skip,
      limit,
      ...(llm_provider && { llm_provider }),
      ...(is_active !== undefined && { is_active }),
    },
  });
  return response.data;
};

export const getLlmApiKeyDetail = async (apiKeyId) => {
  const response = await adminApiClient.get(`/api/system-admin/llm-api-keys/${apiKeyId}`);
  return response.data;
};

export const createLlmApiKey = async (payload) => {
  const response = await adminApiClient.post('/api/system-admin/llm-api-keys', payload);
  return response.data;
};

export const updateLlmApiKey = async (apiKeyId, payload) => {
  const response = await adminApiClient.put(`/api/system-admin/llm-api-keys/${apiKeyId}`, payload);
  return response.data;
};

export const deleteLlmApiKey = async (apiKeyId) => {
  const response = await adminApiClient.delete(`/api/system-admin/llm-api-keys/${apiKeyId}`);
  return response.data;
};

export const getPrompts = async (params = {}) => {
  const { skip = 0, limit = 100, purpose, type, is_active } = params;
  const response = await adminApiClient.get('/api/system-admin/prompts', {
    params: {
      skip,
      limit,
      ...(purpose && { purpose }),
      ...(type && { type }),
      ...(is_active !== undefined && { is_active }),
    },
  });
  return response.data;
};

export const getPromptDetail = async (promptId) => {
  const response = await adminApiClient.get(`/api/system-admin/prompts/${promptId}`);
  return response.data;
};

export const createPrompt = async (payload) => {
  const response = await adminApiClient.post('/api/system-admin/prompts', payload);
  return response.data;
};

export const updatePrompt = async (promptId, payload) => {
  const response = await adminApiClient.put(`/api/system-admin/prompts/${promptId}`, payload);
  return response.data;
};

export const deletePrompt = async (promptId) => {
  const response = await adminApiClient.delete(`/api/system-admin/prompts/${promptId}`);
  return response.data;
};
