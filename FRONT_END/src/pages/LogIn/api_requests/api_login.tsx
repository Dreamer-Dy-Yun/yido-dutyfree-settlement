import { CustHttp, HttpResult } from '../../../../common/apis/cust_https';

/**
 * 로그인 요청 인터페이스
 */
export interface LoginRequest {
    email: string;
    password: string;
}

/**
 * 로그인 응답 인터페이스
 */
export interface LoginResponse {
    access_token: string;
    token_type: string;
}

/**
 * 로그인 API 요청
 * @param request - 로그인 요청 데이터 (이메일, 비밀번호)
 * @param baseUrl - API 기본 URL (선택사항)
 * @param endPoint - API 엔드포인트 (기본값: '/api/auth/login')
 * @param headers - 추가 헤더 (선택사항)
 * @param signal - 요청 취소 신호 (선택사항)
 * @returns 로그인 응답 결과
 */
export const login = async (
    request: LoginRequest,
    baseUrl?: string,
    endPoint: string = '/api/auth/login',
    headers?: Record<string, string>,
    signal?: AbortSignal
): Promise<HttpResult<LoginResponse>> => {
    console.log('로그인 요청:', { email: request.email });

    // OAuth2PasswordRequestForm 형식으로 FormData 생성
    const formData = new FormData();
    formData.append('username', request.email); // OAuth2PasswordRequestForm은 username 필드에 이메일 사용
    formData.append('password', request.password);

    const http = new CustHttp(baseUrl);
    // FormData 사용 시 Content-Type은 CustHttp에서 자동 처리됨
    await http.post<LoginResponse>(endPoint, formData, headers, signal, 'multipart/form-data');
    const result = await http.getResultAsModified<LoginResponse>();
    
    // 토큰 저장
    if (result.data?.access_token) {
        localStorage.setItem('access_token', result.data.access_token);
    }
    
    return result;
};