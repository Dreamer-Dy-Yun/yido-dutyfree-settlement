import api from './api';

/**
 * 회사 검색
 */
export const searchCompany = async (name, businessNo) => {
  const params = {};
  if (name) params.name = name;
  if (businessNo) params.business_no = businessNo;
  
  const response = await api.get('/api/company/search', { params });
  return response.data;
};

/**
 * 신규 회사 등록
 */
export const registerCompany = async (companyData) => {
  const response = await api.post('/api/company/register', companyData);
  return response.data;
};

/**
 * 로그인 (회사 선택 후)
 */
export const login = async (email, password, tenantId) => {
  const response = await api.post('/api/auth/login', {
    email,
    password,
    tenant_id: tenantId,
  });
  
  // 토큰 및 테넌트 정보 저장
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
    // JWT에서 테넌트 정보 추출 (또는 응답에 포함)
    const token = response.data.access_token;
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.tenant_id) {
      localStorage.setItem('tenant_id', payload.tenant_id);
      localStorage.setItem('tenant_schema', payload.tenant_schema);
    }
  }
  
  return response.data;
};

/**
 * 로그아웃
 */
export const logout = async () => {
  try {
    await api.post('/api/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    localStorage.removeItem('access_token');
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('tenant_schema');
    window.location.href = '/';
  }
};

/**
 * 현재 사용자 정보 조회
 */
export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

/**
 * 비밀번호 변경
 */
export const changePassword = async (oldPassword, newPassword, isTempPassword = false) => {
  const response = await api.post('/api/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
    is_temp_password: isTempPassword,
  });
  return response.data;
};

/**
 * 토큰 확인
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};
