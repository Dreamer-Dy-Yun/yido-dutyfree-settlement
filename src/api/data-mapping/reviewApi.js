import { tenantApiClient } from '../client/apiClient';

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
