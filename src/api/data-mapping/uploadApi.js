import { tenantApiClient } from '../client/apiClient';

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
