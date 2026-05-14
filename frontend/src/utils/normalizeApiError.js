/**
 * axios/FastAPI 응답의 detail(문자열·배열·객체)을 사용자에게 보여줄 문자열로 정규화한다.
 */
export function normalizeApiError(err, fallbackMessage) {
  const detail = err?.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const joined = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          if (typeof item.msg === 'string') return item.msg;
          if (typeof item.message === 'string') return item.message;
        }
        return '';
      })
      .filter(Boolean)
      .join(', ');
    return joined || fallbackMessage;
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string' && detail.message.trim()) {
      return detail.message;
    }
    if (typeof detail.code === 'string' && detail.code.trim()) {
      return `${fallbackMessage} (${detail.code})`;
    }
    return fallbackMessage;
  }

  const message = err?.message;
  if (typeof message === 'string' && message.trim()) {
    return message;
  }

  return fallbackMessage;
}
