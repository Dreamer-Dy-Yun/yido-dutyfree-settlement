import api, { adminApi } from './api';

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
 * 시스템 어드민 로그아웃
 */
export const systemAdminLogout = async () => {
  try {
    await adminApi.post('/api/auth/system-admin/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    localStorage.removeItem('admin_access_token');
    window.location.href = '/';
  }
};

/**
 * 시스템 어드민 현재 사용자 정보 조회
 */
export const getCurrentSystemAdmin = async () => {
  const response = await adminApi.get('/api/auth/system-admin/me');
  return response.data;
};

/**
 * 시스템 어드민 정보 수정 (비밀번호 확인 필요)
 */
export const updateSystemAdminProfile = async (currentPassword, profile) => {
  const response = await adminApi.put('/api/auth/system-admin/me', {
    current_password: currentPassword,
    name: profile.name,
    alias: profile.alias,
    department: profile.department,
    contact: profile.contact,
  });
  return response.data;
};

/**
 * 현재 사용자 정보 조회
 */
export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

/**
 * 테넌트 사용자 비밀번호 확인 (정보 수정 전용)
 */
export const verifyPassword = async (password) => {
  const response = await api.post('/api/auth/verify-password', { password });
  return response.data;
};

/**
 * 테넌트 사용자 본인 정보 수정 (비밀번호 확인 필요)
 */
export const updateMyProfile = async (currentPassword, profile) => {
  const response = await api.put('/api/auth/me', {
    current_password: currentPassword,
    name: profile.name,
    department: profile.department,
    contact: profile.contact,
  });
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
 * 시스템 어드민 로그인
 */
export const systemAdminLogin = async (email, password) => {
  const response = await api.post('/api/auth/system-admin/login', {
    email,
    password,
  });
  
  if (response.data.access_token) {
    localStorage.setItem('admin_access_token', response.data.access_token);
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('tenant_schema');
  }
  
  return response.data;
};

/**
 * 토큰 확인
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

/**
 * JWT 토큰에서 사용자 정보 추출
 */
export const getTokenPayload = () => {
  const token = localStorage.getItem('access_token');
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload;
  } catch {
    return null;
  }
};

/**
 * 시스템 어드민 토큰 payload (필요 시 사용)
 */
export const getAdminTokenPayload = () => {
  const token = localStorage.getItem('admin_access_token');
  if (!token) return null;
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
};

/**
 * 시스템 어드민 로그인 여부
 */
export const isAdminAuthenticated = () => {
  return !!localStorage.getItem('admin_access_token');
};

/**
 * 시스템 어드민 권한 확인
 */
export const isSuperuser = () => {
  return isAdminAuthenticated();
};