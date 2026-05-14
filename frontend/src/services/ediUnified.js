import api from './api';

const fmtDate = (d) => {
  if (!d) return null;
  const yyyy = String(d.getFullYear()).padStart(4, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}.${mm}.${dd}`;
};

export const enqueueEdiUnifiedJob = async ({ sources = ['silla', 'lotte'] } = {}) => {
  const response = await api.post('/api/tenant/data-mapping/edi-unified/run', { sources });
  return response.data;
};

export const getEdiUnifiedJobStatus = async (jobId) => {
  const response = await api.get(`/api/tenant/data-mapping/edi-unified/job/${jobId}`);
  return response.data;
};

export const listEdiUnifiedGroups = async ({
  fromDate,
  toDate,
  sources = 'all', // all|silla|lotte
  statusFilter = 'all', // all|full|partial|unmapped
  page = 1,
  pageSize = 50,
} = {}) => {
  const params = {
    from_date: typeof fromDate === 'string' ? fromDate : fmtDate(fromDate),
    to_date: typeof toDate === 'string' ? toDate : fmtDate(toDate),
    sources,
    status_filter: statusFilter,
    page,
    page_size: pageSize,
  };
  const response = await api.get('/api/tenant/data-mapping/edi-unified/groups', { params });
  return response.data;
};

export const getEdiUnifiedGroupDetail = async ({
  dutyfreeOperator,
  receiptNo,
  fromDate,
  toDate,
} = {}) => {
  const params = {
    dutyfree_operator: dutyfreeOperator,
    receipt_no: receiptNo,
    from_date: typeof fromDate === 'string' ? fromDate : fmtDate(fromDate),
    to_date: typeof toDate === 'string' ? toDate : fmtDate(toDate),
  };
  const response = await api.get('/api/tenant/data-mapping/edi-unified/groups/detail', { params });
  return response.data;
};

export const downloadEdiUnifiedExcel = async ({ fromDate, toDate, sources = 'all' } = {}) => {
  const params = {
    from_date: typeof fromDate === 'string' ? fromDate : fmtDate(fromDate),
    to_date: typeof toDate === 'string' ? toDate : fmtDate(toDate),
    sources,
  };
  const response = await api.get('/api/tenant/data-mapping/edi-unified/export', {
    params,
    responseType: 'blob',
  });

  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });

  const yyyyMmDd = (d) =>
    typeof d === 'string' ? d : fmtDate(d) || '';
  const filename = `EDI매핑결과_(${yyyyMmDd(fromDate)}~${yyyyMmDd(toDate)}).xlsx`;

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

