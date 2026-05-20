import { tenantApiClient } from '../client/apiClient';

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
