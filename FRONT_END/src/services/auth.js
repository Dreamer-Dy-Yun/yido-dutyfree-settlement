import api from './api';

/**
 * 회원가입
 */
export const register = async (userData) => {
  const response = await api.post('/api/registration/register', {
    username: userData.username,
    email: userData.email,
    password: userData.password,
    full_name: userData.full_name || null,
    company_name: userData.company_name,
  });
  return response.data;
};

/**
 * 로그인
 */
export const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email); // OAuth2PasswordRequestForm은 username 필드 사용
  formData.append('password', password);

  const response = await api.post('/api/auth/login', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  // 토큰 저장
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
  }
  
  return response.data;
};

/**
 * 로그아웃
 */
export const logout = () => {
  localStorage.removeItem('access_token');
  window.location.href = '/login';
};

/**
 * 현재 사용자 정보 조회
 */
export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

/**
 * 토큰 확인
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};
