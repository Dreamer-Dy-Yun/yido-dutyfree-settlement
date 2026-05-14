let currentTTL = null;
const listeners = new Set();

export function updateSessionTTLFromResponse(response) {
  if (!response?.headers) return;

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
      // Ignore listener errors so one subscriber cannot break session updates.
    }
  });
}

export function subscribeSessionTTL(callback) {
  if (typeof callback !== 'function') {
    return () => {};
  }

  listeners.add(callback);

  if (currentTTL !== null) {
    callback(currentTTL);
  }

  return () => {
    listeners.delete(callback);
  };
}
