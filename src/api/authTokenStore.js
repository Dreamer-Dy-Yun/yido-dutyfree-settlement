const TENANT_TOKEN_KEY = 'access_token';
const ADMIN_TOKEN_KEY = 'admin_access_token';
const TENANT_ID_KEY = 'tenant_id';
const TENANT_SCHEMA_KEY = 'tenant_schema';

function decodeJwtPayload(token) {
  if (!token) return null;

  try {
    const [, payload] = token.split('.');
    if (!payload) return null;
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

export function getTenantToken() {
  return localStorage.getItem(TENANT_TOKEN_KEY);
}

export function getAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY);
}

export function storeTenantToken(token) {
  localStorage.setItem(TENANT_TOKEN_KEY, token);

  const payload = decodeJwtPayload(token);
  if (payload?.tenant_id) {
    localStorage.setItem(TENANT_ID_KEY, payload.tenant_id);
    localStorage.setItem(TENANT_SCHEMA_KEY, payload.tenant_schema);
  }
}

export function storeAdminToken(token) {
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
  localStorage.removeItem(TENANT_ID_KEY);
  localStorage.removeItem(TENANT_SCHEMA_KEY);
}

export function clearTenantSession() {
  localStorage.removeItem(TENANT_TOKEN_KEY);
  localStorage.removeItem(TENANT_ID_KEY);
  localStorage.removeItem(TENANT_SCHEMA_KEY);
}

export function clearAdminSession() {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
}

export function hasTenantSession() {
  return Boolean(getTenantToken());
}

export function hasAdminSession() {
  return Boolean(getAdminToken());
}

export function getTenantTokenPayload() {
  return decodeJwtPayload(getTenantToken());
}

export function getAdminTokenPayload() {
  return decodeJwtPayload(getAdminToken());
}
