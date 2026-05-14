import { tenantApiClient } from './client';

const formatDate = (date) => {
  if (!date) return null;
  const yyyy = String(date.getFullYear()).padStart(4, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}.${mm}.${dd}`;
};

const toDateParam = (date) => (typeof date === 'string' ? date : formatDate(date));

export const enqueueEdiUnifiedJob = async ({ sources = ['silla', 'lotte'] } = {}) => {
  const response = await tenantApiClient.post('/api/tenant/data-mapping/edi-unified/run', { sources });
  return response.data;
};

export const getEdiUnifiedJobStatus = async (jobId) => {
  const response = await tenantApiClient.get(`/api/tenant/data-mapping/edi-unified/job/${jobId}`);
  return response.data;
};

export const listEdiUnifiedGroups = async ({
  fromDate,
  toDate,
  sources = 'all',
  statusFilter = 'all',
  page = 1,
  pageSize = 50,
} = {}) => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/edi-unified/groups', {
    params: {
      from_date: toDateParam(fromDate),
      to_date: toDateParam(toDate),
      sources,
      status_filter: statusFilter,
      page,
      page_size: pageSize,
    },
  });
  return response.data;
};

export const getEdiUnifiedGroupDetail = async ({
  dutyfreeOperator,
  receiptNo,
  fromDate,
  toDate,
} = {}) => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/edi-unified/groups/detail', {
    params: {
      dutyfree_operator: dutyfreeOperator,
      receipt_no: receiptNo,
      from_date: toDateParam(fromDate),
      to_date: toDateParam(toDate),
    },
  });
  return response.data;
};

export const downloadEdiUnifiedExcel = async ({ fromDate, toDate, sources = 'all' } = {}) => {
  const response = await tenantApiClient.get('/api/tenant/data-mapping/edi-unified/export', {
    params: {
      from_date: toDateParam(fromDate),
      to_date: toDateParam(toDate),
      sources,
    },
    responseType: 'blob',
  });

  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const filename = `EDI매핑결과_(${toDateParam(fromDate) || ''}~${toDateParam(toDate) || ''}).xlsx`;
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
