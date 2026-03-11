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
 * 테넌트 유저 활성 상태 변경
 */
export const userActivate = async (userId, isActive) => {
  const response = await api.patch(`/api/tenant/users/${userId}/activation`, {
    is_active: isActive,
  });
  return response.data;
};

/**
 * 테넌트 유저 물리 삭제
 */
export const deleteTenantUser = async (userId) => {
  const response = await api.delete(`/api/tenant/users/${userId}`);
  return response.data;
};

/**
 * 테넌트 유저 비밀번호 재설정
 * - 서버에서 임시 비밀번호를 생성하여 이메일로 발송
 */
export const resetUserPassword = async (userId) => {
  const response = await api.post(`/api/tenant/users/${userId}/reset-password`);
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

/**
 * EDI 엑셀 업로드 (면세점 구분 필수)
 * @param {File} file - 업로드할 엑셀 파일
 * @param {string} ediSource - 면세점 구분: 'lotte' | 'silla'
 */
export const uploadEdiFile = async (file, ediSource = 'lotte') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('edi_source', ediSource);

  const response = await api.post('/api/tenant/data-mapping/edi-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * 이미지 ZIP 업로드 (데이터 매핑용)
 * @param {File} file - 업로드할 ZIP 파일
 */
export const uploadImageZip = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/tenant/data-mapping/image-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * 이미지 OCR 진행도 조회 (폴링용)
 */
export const getImageOcrProgress = async () => {
  const response = await api.get('/api/tenant/data-mapping/image-ocr-progress');
  return response.data;
};

/**
 * 이미지 확인 - 영수증 리스트 조회
 * @param {Object} options
 * @param {boolean} [options.isCompleted=false] - true 이면 검수 완료(Verified), false 이면 미완료(OCR 원본)
 * @param {number} [options.skip=0]
 * @param {number} [options.limit=50]
 */
export const getReceiptList = async ({ isCompleted = false, skip = 0, limit = 50 } = {}) => {
  const params = {
    is_completed: isCompleted,
    skip,
    limit,
  };
  const response = await api.get('/api/tenant/data-mapping/receipts', { params });
  return response.data;
};

/**
 * 이미지 확인 - 여권 리스트 조회
 * @param {Object} options
 * @param {boolean} [options.isCompleted=false]
 * @param {number} [options.skip=0]
 * @param {number} [options.limit=50]
 */
export const getPassportList = async ({ isCompleted = false, skip = 0, limit = 50 } = {}) => {
  const params = {
    is_completed: isCompleted,
    skip,
    limit,
  };
  const response = await api.get('/api/tenant/data-mapping/passports', { params });
  return response.data;
};

/**
 * 이미지 확인 - 영수증 검수/수정
 * @param {Object} payload - 서버 설계에 맞는 검수/수정 데이터
 */
export const verifyReceipt = async (payload) => {
  const response = await api.post('/api/tenant/data-mapping/receipts/verify', payload);
  return response.data;
};

/**
 * 이미지 확인 - 여권 검수/수정
 * @param {Object} payload - 서버 설계에 맞는 검수/수정 데이터
 */
export const verifyPassport = async (payload) => {
  const response = await api.post('/api/tenant/data-mapping/passports/verify', payload);
  return response.data;
};

/**
 * 이미지 확인 - hash_img 기준 영수증/여권 상세 조회
 * @param {string} hashImg
 */
export const getImageDetailsByHash = async (hashImg) => {
  const response = await api.get('/api/tenant/data-mapping/image-details', {
    params: { hash_img: hashImg },
  });
  return response.data;
};