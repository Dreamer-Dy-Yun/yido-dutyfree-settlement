import { beforeEach, describe, expect, it } from 'vitest';
import {
  getCompanyDisplayName,
  readSelectedTenant,
  storeSelectedTenant,
} from './tenantSelectionStore';

describe('tenantSelectionStore', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('uses alias as the company display name when present', () => {
    expect(getCompanyDisplayName({ name: 'Long Company', alias: 'Short' })).toBe('Short');
  });

  it('stores and reads the last selected tenant company', () => {
    const stored = storeSelectedTenant({ id: 7, name: 'Yido', alias: 'YIDO' });

    expect(stored).toMatchObject({ id: 7, name: 'Yido', alias: 'YIDO' });
    expect(localStorage.getItem('selected_tenant_id')).toBe('7');
    expect(localStorage.getItem('selected_tenant_name')).toBe('YIDO');
    expect(readSelectedTenant()).toEqual({ id: 7, name: 'YIDO', alias: null });
  });

  it('returns null for invalid stored tenant selection', () => {
    localStorage.setItem('selected_tenant_id', 'not-a-number');
    localStorage.setItem('selected_tenant_name', 'YIDO');

    expect(readSelectedTenant()).toBeNull();
  });

  it('does not store incomplete company data', () => {
    expect(storeSelectedTenant({ name: 'No Id' })).toBeNull();
    expect(localStorage.getItem('selected_tenant_id')).toBeNull();
  });
});
