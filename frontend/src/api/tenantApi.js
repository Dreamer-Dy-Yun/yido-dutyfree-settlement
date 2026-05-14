import { tenantApiClient } from './client';

function buildUsageDateParams(startDate, endDate) {
  const params = {};
  if (startDate) params.start_date = startDate.toISOString();
  if (endDate) params.end_date = endDate.toISOString();
  return params;
}

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

export const getUsage = async (startDate = null, endDate = null) => {
  const response = await tenantApiClient.get('/api/tenant/usage', {
    params: buildUsageDateParams(startDate, endDate),
  });
  return response.data;
};

export const getUserTokenUsage = async (userId, startDate = null, endDate = null) => {
  const response = await tenantApiClient.get(`/api/tenant/usage/users/${userId}/tokens`, {
    params: buildUsageDateParams(startDate, endDate),
  });
  return response.data;
};

export const uploadEdiFile = async (file, ediSource = 'lotte') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('edi_source', ediSource);

  const response = await tenantApiClient.post('/api/tenant/data-mapping/edi-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const uploadImageZip = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await tenantApiClient.post('/api/tenant/data-mapping/image-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getImageOcrProgress = async () => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/image-ocr-progress');
  return response.data;
};

export const getReceiptList = async ({ isCompleted = false, skip = 0, limit = 50 } = {}) => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/receipts', {
    params: { is_completed: isCompleted, skip, limit },
  });
  return response.data;
};

export const getPassportList = async ({ isCompleted = false, skip = 0, limit = 50 } = {}) => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/passports', {
    params: { is_completed: isCompleted, skip, limit },
  });
  return response.data;
};

export const verifyReceipt = async (payload) => {
  const response = await tenantApiClient.post('/api/tenant/data-mapping/receipts/verify', payload);
  return response.data;
};

export const verifyPassport = async (payload) => {
  const response = await tenantApiClient.post('/api/tenant/data-mapping/passports/verify', payload);
  return response.data;
};

export const deleteReceipt = async (payload) => {
  const response = await tenantApiClient.delete('/api/tenant/data-mapping/receipts/verify', {
    data: payload,
  });
  return response.data;
};

export const deletePassport = async (payload) => {
  const response = await tenantApiClient.delete('/api/tenant/data-mapping/passports/verify', {
    data: payload,
  });
  return response.data;
};

export const bulkVerifyReceipts = async (ids) => {
  const response = await tenantApiClient.post('/api/tenant/data-mapping/receipts/bulk-verify', { ids });
  return response.data;
};

export const bulkVerifyPassports = async (ids) => {
  const response = await tenantApiClient.post('/api/tenant/data-mapping/passports/bulk-verify', { ids });
  return response.data;
};

export const getImageDetailsByHash = async (hashImg, options = {}) => {
  const params = { hash_img: hashImg };
  if (options.receiptSource != null && options.receiptId != null) {
    params.receipt_source = options.receiptSource;
    params.receipt_id = options.receiptId;
  }
  if (options.passportSource != null && options.passportId != null) {
    params.passport_source = options.passportSource;
    params.passport_id = options.passportId;
  }

  const response = await tenantApiClient.get('/api/tenant/data-mapping/image-details', { params });
  return response.data;
};

export const getImageBlobByHash = async (imageHash) => {
  const response = await tenantApiClient.get(`/api/tenant/data-mapping/image/${imageHash}`, {
    responseType: 'blob',
  });
  return response.data;
};

export const getMatchStatus = async () => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/match-status');
  return response.data;
};

export const postMatchAttempt = async ({ tryFallback = true } = {}) => {
  const response = await tenantApiClient.post('/api/tenant/data-mapping/match-attempt', {
    try_fallback: tryFallback,
  });
  return response.data;
};

export const getMatches = async ({ status = 'all', page = 1, pageSize = 20 } = {}) => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/matches', {
    params: { status, page, page_size: pageSize },
  });
  return response.data;
};

export const getMatchDetail = async (uuidReceipt) => {
  const response = await tenantApiClient.get(`/api/tenant/data-mapping/matches/${uuidReceipt}`);
  return response.data;
};
