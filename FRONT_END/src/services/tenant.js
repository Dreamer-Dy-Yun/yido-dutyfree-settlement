import api from './api';

/**
 * 테넌트 유저 목록 조회
 */
export const getTenantUsers = async (skip = 0, limit = 100, isActive = null) => {
  const params = { skip, limit };
  if (isActive !== null) params.is_active = isActive;
  
  const response = await api.get('/api/tenant/users', { params });
  return response.data;
};

/**
 * 테넌트 유저 추가
 */
export const createTenantUser = async (userData) => {
  const response = await api.post('/api/tenant/users', userData);
  return response.data;
};

/**
 * 테넌트 유저 조회
 */
export const getTenantUser = async (userId) => {
  const response = await api.get(`/api/tenant/users/${userId}`);
  return response.data;
};

/**
 * 테넌트 유저 수정
 */
export const updateTenantUser = async (userId, userData) => {
  const response = await api.put(`/api/tenant/users/${userId}`, userData);
  return response.data;
};

/**
 * 테넌트 유저 삭제/비활성화
 */
export const deleteTenantUser = async (userId) => {
  const response = await api.delete(`/api/tenant/users/${userId}`);
  return response.data;
};

/**
 * 테넌트 유저 비밀번호 재설정
 */
export const resetUserPassword = async (userId, newPassword) => {
  const response = await api.post(`/api/tenant/users/${userId}/reset-password`, {
    new_password: newPassword,
  });
  return response.data;
};

/**
 * 전체 사용량 조회
 */
export const getUsage = async (startDate = null, endDate = null) => {
  const params = {};
  if (startDate) params.start_date = startDate.toISOString();
  if (endDate) params.end_date = endDate.toISOString();
  
  const response = await api.get('/api/tenant/usage', { params });
  return response.data;
};

/**
 * 사용자별 토큰 사용량 조회
 */
export const getUserTokenUsage = async (userId, startDate = null, endDate = null) => {
  const params = {};
  if (startDate) params.start_date = startDate.toISOString();
  if (endDate) params.end_date = endDate.toISOString();
  
  const response = await api.get(`/api/tenant/usage/users/${userId}/tokens`, { params });
  return response.data;
};
