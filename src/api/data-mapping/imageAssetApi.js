import { tenantApiClient } from '../client/apiClient';

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
