import { useEffect, useState } from 'react';
import { subscribeSessionTTL } from '../services/sessionTTL';

/**
 * 백엔드에서 내려주는 X-Session-Expires-In 헤더 기반
 * 세션 남은 시간을 초/분 단위로 제공하는 훅
 */
export default function useSessionTTL() {
  const [ttl, setTtl] = useState(null);
  const hasTtl = ttl !== null;

  // 서버에서 TTL 헤더가 갱신될 때마다 최신 값 반영
  useEffect(() => {
    const unsubscribe = subscribeSessionTTL((value) => {
      setTtl(typeof value === 'number' ? value : null);
    });
    return unsubscribe;
  }, []);

  // 클라이언트 측에서 1초 단위로 카운트다운
  useEffect(() => {
    if (!hasTtl) return;

    const intervalId = setInterval(() => {
      setTtl((prev) => {
        if (prev === null) return prev;
        return prev > 0 ? prev - 1 : 0;
      });
    }, 1000);

    return () => clearInterval(intervalId);
  }, [hasTtl]);

  const minutes =
    ttl !== null && Number.isFinite(ttl) ? Math.floor(ttl / 60) : null;
  const seconds =
    ttl !== null && Number.isFinite(ttl) ? ttl % 60 : null;

  return { ttl, minutes, seconds };
}

