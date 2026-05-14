import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearAdminSession,
  clearTenantSession,
  getAdminTokenPayload,
  getPostLoginRedirectPath,
  getTenantTokenPayload,
  storeAdminToken,
  storeTenantToken,
} from './authTokenStore';

function createToken(payload) {
  const encodedPayload = btoa(JSON.stringify(payload))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

  return `header.${encodedPayload}.signature`;
}

describe('authTokenStore', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores tenant token claims from base64url JWT payload', () => {
    storeTenantToken(createToken({ tenant_id: 12, tenant_schema: 'tenant_12', role: 'admin' }));

    expect(localStorage.getItem('access_token')).toBeTruthy();
    expect(localStorage.getItem('tenant_id')).toBe('12');
    expect(localStorage.getItem('tenant_schema')).toBe('tenant_12');
    expect(getTenantTokenPayload()).toMatchObject({ tenant_id: 12, role: 'admin' });
  });

  it('clears stale tenant id/schema when token has no tenant claims', () => {
    localStorage.setItem('tenant_id', 'old');
    localStorage.setItem('tenant_schema', 'old_schema');

    storeTenantToken(createToken({ role: 'user' }));

    expect(localStorage.getItem('tenant_id')).toBeNull();
    expect(localStorage.getItem('tenant_schema')).toBeNull();
  });

  it('stores admin token separately from tenant session details', () => {
    localStorage.setItem('tenant_id', '12');
    localStorage.setItem('tenant_schema', 'tenant_12');

    storeAdminToken(createToken({ role: 'system_admin', is_superuser: true }));

    expect(getAdminTokenPayload()).toMatchObject({ role: 'system_admin' });
    expect(localStorage.getItem('tenant_id')).toBeNull();
    expect(localStorage.getItem('tenant_schema')).toBeNull();
  });

  it('resolves post-login path from tenant token role', () => {
    storeTenantToken(createToken({ role: 'admin' }));
    expect(getPostLoginRedirectPath()).toBe('/dashboard');

    storeTenantToken(createToken({ role: 'user' }));
    expect(getPostLoginRedirectPath()).toBe('/dashboard/data-mapping');

    storeTenantToken(createToken({ role: 'system_admin' }));
    expect(getPostLoginRedirectPath()).toBe('/admin');
  });

  it('clears stored sessions', () => {
    storeTenantToken(createToken({ tenant_id: 12, tenant_schema: 'tenant_12' }));
    storeAdminToken(createToken({ role: 'system_admin' }));

    clearTenantSession();
    clearAdminSession();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('admin_access_token')).toBeNull();
    expect(localStorage.getItem('tenant_id')).toBeNull();
    expect(localStorage.getItem('tenant_schema')).toBeNull();
  });
});
