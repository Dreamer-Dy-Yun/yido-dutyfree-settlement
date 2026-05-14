const SELECTED_TENANT_ID_KEY = 'selected_tenant_id';
const SELECTED_TENANT_NAME_KEY = 'selected_tenant_name';

export function getCompanyDisplayName(company) {
  return company?.alias || company?.name || '';
}

export function readSelectedTenant() {
  const rawTenantId = localStorage.getItem(SELECTED_TENANT_ID_KEY);
  const tenantName = localStorage.getItem(SELECTED_TENANT_NAME_KEY);
  const tenantId = Number.parseInt(rawTenantId || '', 10);

  if (!Number.isFinite(tenantId) || !tenantName) {
    return null;
  }

  return {
    id: tenantId,
    name: tenantName,
    alias: null,
  };
}

export function storeSelectedTenant(company) {
  const displayName = getCompanyDisplayName(company);

  if (company?.id == null || !displayName) {
    return null;
  }

  localStorage.setItem(SELECTED_TENANT_ID_KEY, String(company.id));
  localStorage.setItem(SELECTED_TENANT_NAME_KEY, displayName);

  return {
    ...company,
    name: company.name || displayName,
    alias: company.alias ?? null,
  };
}
