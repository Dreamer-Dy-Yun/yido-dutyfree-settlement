import { adminApi } from '../../services/api';

/**
 * 시스템 어드민 API 서비스
 * 서비스 제공사 관리자 전용 API 호출
 */

/**
 * 시스템 통계 조회
 */
export const getSystemStats = async () => {
  const response = await adminApi.get('/api/system-admin/dashboard/stats');
  return response.data;
};

/**
 * 테넌트 목록 조회
 */
export const getTenants = async (params = {}) => {
  const { skip = 0, limit = 100, is_active, search } = params;
  const response = await adminApi.get('/api/system-admin/tenants', {
    params: {
      skip,
      limit,
      ...(is_active !== undefined && { is_active }),
      ...(search && { search }),
    },
  });
  return response.data;
};

/**
 * 테넌트 상세 조회
 */
export const getTenantDetail = async (tenantId) => {
  const response = await adminApi.get(`/api/system-admin/tenants/${tenantId}`);
  return response.data;
};

/**
 * 승인 대기 테넌트 목록 조회
 */
export const getPendingTenants = async (params = {}) => {
  const { skip = 0, limit = 100 } = params;
  // 전용 엔드포인트 대신 공통 테넌트 목록 API를 활용하여 is_active = false 필터링
  const data = await getTenants({
    skip,
    limit,
    is_active: false,
  });

  // 기존 응답 형태(pending_tenants)를 유지하여 프론트 코드 수정 최소화
  return {
    pending_tenants: data.tenants || [],
    total: data.total,
    skip: data.skip,
    limit: data.limit,
  };
};

/**
 * 테넌트 승인
 */
export const approveTenant = async (tenantId, reason = null) => {
  const response = await adminApi.post(`/api/system-admin/tenants/${tenantId}/approve`, {
    reason,
  });
  return response.data;
};

/**
 * 테넌트 거부
 */
export const rejectTenant = async (tenantId, reason) => {
  const response = await adminApi.post(`/api/system-admin/tenants/${tenantId}/reject`, {
    reason,
  });
  return response.data;
};

/**
 * 테넌트 정보 수정
 */
export const updateTenant = async (tenantId, updateData) => {
  const response = await adminApi.put(`/api/system-admin/tenants/${tenantId}`, updateData);
  return response.data;
};

/**
 * 테넌트 활성화
 */
export const activateTenant = async (tenantId) => {
  const response = await adminApi.post(`/api/system-admin/tenants/${tenantId}/activate`);
  return response.data;
};

/**
 * 테넌트 비활성화
 */
export const deactivateTenant = async (tenantId) => {
  const response = await adminApi.post(`/api/system-admin/tenants/${tenantId}/deactivate`);
  return response.data;
};

/**
 * 테넌트 삭제 (완전 삭제)
 */
export const deleteTenant = async (tenantId, reason) => {
  const response = await adminApi.delete(`/api/system-admin/tenants/${tenantId}`, {
    data: { reason },
  });
  return response.data;
};

/**
 * 서비스 어카운트 목록 조회
 */
export const getServiceAccounts = async (params = {}) => {
  const { skip = 0, limit = 100, role, is_active } = params;
  const response = await adminApi.get('/api/system-admin/service-accounts', {
    params: {
      skip,
      limit,
      ...(role && { role }),
      ...(is_active !== undefined && { is_active }),
    },
  });
  return response.data;
};

/**
 * 서비스 어카운트 상세 조회
 */
export const getServiceAccountDetail = async (accountId) => {
  const response = await adminApi.get(`/api/system-admin/service-accounts/${accountId}`);
  return response.data;
};

/**
 * 서비스 어카운트 생성
 */
export const createServiceAccount = async (accountData) => {
  const response = await adminApi.post('/api/system-admin/service-accounts', accountData);
  return response.data;
};

/**
 * 서비스 어카운트 수정
 */
export const updateServiceAccount = async (accountId, updateData) => {
  const response = await adminApi.put(`/api/system-admin/service-accounts/${accountId}`, updateData);
  return response.data;
};

/**
 * 서비스 어카운트 삭제
 */
export const deleteServiceAccount = async (accountId) => {
  const response = await adminApi.delete(`/api/system-admin/service-accounts/${accountId}`);
  return response.data;
};

/**
 * LLM API KEY 목록 조회
 */
export const getLlmApiKeys = async (params = {}) => {
  const { skip = 0, limit = 100, llm_provider, is_active } = params;
  const response = await adminApi.get('/api/system-admin/llm-api-keys', {
    params: {
      skip,
      limit,
      ...(llm_provider && { llm_provider }),
      ...(is_active !== undefined && { is_active }),
    },
  });
  return response.data;
};

/**
 * LLM API KEY 생성
 */
export const createLlmApiKey = async (payload) => {
  const response = await adminApi.post('/api/system-admin/llm-api-keys', payload);
  return response.data;
};

/**
 * LLM API KEY 수정
 */
export const updateLlmApiKey = async (apiKeyId, payload) => {
  const response = await adminApi.put(`/api/system-admin/llm-api-keys/${apiKeyId}`, payload);
  return response.data;
};

/**
 * LLM API KEY 삭제
 */
export const deleteLlmApiKey = async (apiKeyId) => {
  const response = await adminApi.delete(`/api/system-admin/llm-api-keys/${apiKeyId}`);
  return response.data;
};

/**
 * Prompt Path 목록 조회
 */
export const getPromptPaths = async (params = {}) => {
  const { skip = 0, limit = 100, purpose, is_active } = params;
  const response = await adminApi.get('/api/system-admin/prompt-paths', {
    params: {
      skip,
      limit,
      ...(purpose && { purpose }),
      ...(is_active !== undefined && { is_active }),
    },
  });
  return response.data;
};

/**
 * Prompt Path 생성
 */
export const createPromptPath = async (payload) => {
  const response = await adminApi.post('/api/system-admin/prompt-paths', payload);
  return response.data;
};

/**
 * Prompt Path 수정
 */
export const updatePromptPath = async (promptPathId, payload) => {
  const response = await adminApi.put(`/api/system-admin/prompt-paths/${promptPathId}`, payload);
  return response.data;
};

/**
 * Prompt Path 삭제
 */
export const deletePromptPath = async (promptPathId) => {
  const response = await adminApi.delete(`/api/system-admin/prompt-paths/${promptPathId}`);
  return response.data;
};
