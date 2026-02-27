// 세션 TTL(초)을 전역적으로 관리하는 간단한 스토어

let currentTTL = null; // 남은 시간(초)
const listeners = new Set();

/**
 * Axios 응답에서 세션 TTL 헤더를 읽어와 저장하고 구독자에게 알림
 * @param {import('axios').AxiosResponse} response
 */
export const updateSessionTTLFromResponse = (response) => {
  if (!response || !response.headers) return;

  const headerValue =
    response.headers['x-session-expires-in'] ??
    response.headers['X-Session-Expires-In'];

  if (headerValue === undefined || headerValue === null) return;

  const ttl = Number(headerValue);
  if (Number.isNaN(ttl)) return;

  currentTTL = ttl;
  listeners.forEach((listener) => {
    try {
      listener(currentTTL);
    } catch {
      // 개별 리스너 오류는 무시
    }
  });
};

/**
 * 세션 TTL 변경 구독
 * @param {(ttl: number | null) => void} callback
 * @returns {() => void} 구독 해제 함수
 */
export const subscribeSessionTTL = (callback) => {
  if (typeof callback !== 'function') {
    return () => {};
  }

  listeners.add(callback);

  // 이미 TTL 값이 있으면 즉시 한 번 알려줌
  if (currentTTL !== null) {
    callback(currentTTL);
  }

  return () => {
    listeners.delete(callback);
  };
};

