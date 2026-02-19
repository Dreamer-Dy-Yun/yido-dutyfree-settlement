/*###########################################
# Module name : cust_http.ts
# Module functions : CustHttp
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.11.04
# Updated at : 2025.11.04
# Supported by : Chat GPT-4o / Cursor AI
# Note : 
############################################*/


export class HttpError extends Error {
    constructor(public moduleName: string, public status: number, public body: string) {
        super(`ERR-HTTP: ${moduleName} | ${status} | ${body}`);
    }
}

/**
 * 에러 객체에서 사용자 친화적인 에러 메시지를 추출합니다.
 */
export function getDetailedErrorMessage(error: unknown): string {
    // HttpError인 경우
    if (error instanceof HttpError) {
        if (error.status === 0 || !error.status) {
            return `백엔드 서버에 연결할 수 없습니다.\n\n서버가 실행 중인지 확인해주세요.\n에러 상세: ${error.body || error.message}`;
        }
        return `서버 오류 (상태 코드: ${error.status})\n\n${error.body || error.message}`;
    }
    
    // 일반 Error인 경우
    if (error instanceof Error) {
        const message = error.message;
        
        // 네트워크 에러 구분
        if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
            return '백엔드 서버에 연결할 수 없습니다.\n\n네트워크 연결을 확인하거나 서버가 실행 중인지 확인해주세요.';
        }
        
        if (message.includes('timeout') || message.includes('Timeout')) {
            return '요청 시간이 초과되었습니다.\n\n서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.';
        }
        
        if (message.includes('aborted') || message.includes('Abort')) {
            return '요청이 취소되었습니다.';
        }
        
        // 기타 에러는 원본 메시지 반환
        return message;
    }
    
    // 알 수 없는 에러
    return '알 수 없는 오류가 발생했습니다.';
}


export interface HttpResult<T> {
    success: boolean;
    data: T;
    message: string;
}

export class CustHttp {
    private defaultBaseUrl: string;
    private defaultHeaders: Record<string, string>;
    public response!: Response;
    private methodName!: string;
    public blob : Blob | null = null;
    public blobUrl : string | null = null;

    constructor(
        baseUrl: string = '',
        defaultHeaders: Record<string, string> = {}
    ) {
        this.defaultBaseUrl = baseUrl;
        this.defaultHeaders = { 'Accept': 'application/json', ...defaultHeaders };
    }


    /**
     * 마지막 응답 결과를 가져옵니다.
     */
    public async getResult<TResp>(raiseIfError: boolean = true): Promise<TResp> {
        if (!this.response) return null as TResp;
        if (this.response.ok){
            return await this.response.json() as TResp;
        }else{
            if (raiseIfError){
                const errorText = await this.response.text();
                throw new HttpError(this.methodName, this.response.status, errorText);
            }else{
                return null as TResp;
            }
        }
    }

    /**
     * 마지막 응답 결과를 HttpResult 형태로 변환합니다.
     */
    public async getResultAsModified<TResp>(raiseIfError: boolean = true): Promise<HttpResult<TResp>> {

        let status : number = 0;
        let data : TResp = null as TResp;
        let success : boolean = false;
        let msg : string = '';

        try {
            if (!this.response) {
                status = 500;
                msg = 'No response';
                throw new HttpError(this.methodName, status, msg);
            }
            if (!this.response.ok) {
                status = this.response.status;
                msg = this.response.statusText;
                throw new HttpError(this.methodName, status, msg);
            }

            success = true;
            data = await this.response.json() as TResp;
            msg = 'Success';
        } catch (error) {
            if (raiseIfError) throw error;
            data = null as TResp;
        }

        return {
            success: success,
            data: data,
            message: msg
        };
    }


    /**
     * GET 요청
     * @param path - API 경로
     * @param params - 쿼리 파라미터
     * @param headers - 요청 헤더
     * @param signal - 요청 신호
     * @template TResp - 응답 타입 (getResult<TResp>()에서 타입 추론을 위해 사용)
     */
    async get<TResp>(
        path: string,
        params?: Record<string, string | number | boolean | undefined>,
        headers: Record<string, string> = {},
        signal?: AbortSignal,
    ): Promise<this> {
        this.methodName = this.constructor.name + '.get';
        const requestHeaders = { ...this.defaultHeaders, ...headers };
        const qs = new URLSearchParams();

        Object.entries(params ?? {}).forEach(([k, v]) => {
            if (v !== undefined && v !== null) qs.set(k, String(v));
        });

        const url = `${this.defaultBaseUrl}${path}?${qs.toString()}`;
        this.response = await fetch(url, {
            method: 'GET',
            headers: requestHeaders,
            signal: signal,
        });

        return this;
    }


    public async getBlob(filename: string = 'download.xlsx', raiseIfError: boolean = true): 
    Promise<{success : boolean; data: {blob: Blob; filename: string}; message: string }> {

        let success: boolean = false;
        let status: number = 0;
        let _blob: Blob = null as unknown as Blob;
        let msg: string = '';

        try {
            if (!filename?.trim()) {
                status = 400;
                msg = 'Filename required';
                throw new HttpError(this.methodName, status, msg);
            }
            if (!this.response) {
                status = 500;
                msg = 'No response';
                throw new HttpError(this.methodName, status, msg);
            }
            if (!this.response.ok) {
                status = this.response.status;
                msg = this.response.statusText;
                throw new HttpError(this.methodName, status, msg);
            }

            success = true;
            _blob = await this.response.blob();
            msg = 'Success';
        } catch (error) {
            if (raiseIfError) throw error;
            _blob = null as unknown as Blob;
        }

        return {
            success: success,
            data: {blob: _blob, filename: filename.trim()},
            message: msg
        };
        
    }


    /**
     * POST 요청
     * > ※ Post 요청시에는 Param 쓰지 말 것.
     * > ※ 반드시 필요한 경우라면, path에 붙여 넣을 것(지양 바람)
     * @param path - API 경로
     * @param body - 요청 바디
     * @param headers - 요청 헤더
     * @param signal - 요청 신호
     * @template TResp - 응답 타입 (getResult<TResp>()에서 타입 추론을 위해 사용)
     */
    async post<TResp>(
        path: string,   
        body?: any,
        headers?: Record<string, string>,
        signal?: AbortSignal,
        contentType: string = 'application/json'
    ): Promise<this> {
        this.methodName = this.constructor.name + '.post';
        
        // FormData인 경우 Content-Type을 설정하지 않음 (브라우저가 자동 설정)
        const isFormData = body instanceof FormData;
        const requestHeaders: Record<string, string> = { 
            ...this.defaultHeaders, 
            ...(headers ?? {}) 
        };
        
        if (!isFormData) {
            requestHeaders['Content-Type'] = contentType;
        }
        
        const requestSignal = signal ?? undefined;
        const url = `${this.defaultBaseUrl}${path}`;
        
        // FormData인 경우 그대로 전달, 아니면 JSON.stringify
        const requestBody = isFormData ? body : JSON.stringify(body);
        
        this.response = await fetch(url, {
            method: 'POST',
            headers: requestHeaders,
            body: requestBody,
            signal: requestSignal,
        });
        if (!this.response.ok) {
            const errorText = await this.response.text();
            throw new HttpError(url, this.response.status, errorText);
        }
        return this;
    }







  // TODO: 나중에 추가할 메서드들
  // async Put<TResp>(path: string, body?: any, config?: HttpRequestConfig): Promise<TResp> { ... }
  // async Delete<TResp>(path: string, config?: HttpRequestConfig): Promise<TResp> { ... }
}

