import { tenantApiClient } from '../client/apiClient';

function buildUsageDateParams(startDate, endDate) {
  const params = {};
  if (startDate) params.start_date = startDate.toISOString();
  if (endDate) params.end_date = endDate.toISOString();
  return params;
}

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
