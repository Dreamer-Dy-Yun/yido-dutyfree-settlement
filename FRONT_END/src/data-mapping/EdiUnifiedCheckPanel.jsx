import React, { useEffect, useMemo, useState } from 'react';
import {
  enqueueEdiUnifiedJob,
  getEdiUnifiedJobStatus,
  listEdiUnifiedGroups,
  getEdiUnifiedGroupDetail,
  downloadEdiUnifiedExcel,
} from '../services/ediUnified';
import './EdiUnifiedCheckPanel.css';

const toDateInputValue = (d) => {
  const yyyy = String(d.getFullYear()).padStart(4, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};

const fromDateInputValue = (v) => {
  if (!v) return null;
  const [yyyy, mm, dd] = v.split('-').map((x) => parseInt(x, 10));
  if (!yyyy || !mm || !dd) return null;
  return new Date(yyyy, mm - 1, dd);
};

const SOURCE_OPTIONS = [
  { value: 'all', label: '전체' },
  { value: 'silla', label: '신라' },
  { value: 'lotte', label: '롯데' },
];

const STATUS_TABS = [
  { value: 'all', label: '전체' },
  { value: 'full', label: '완전매핑' },
  { value: 'partial', label: '부분매핑' },
  { value: 'unmapped', label: '미매핑' },
];

export default function EdiUnifiedCheckPanel() {
  const today = useMemo(() => new Date(), []);
  const [fromDate, setFromDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [toDate, setToDate] = useState(today);
  const [source, setSource] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [jobError, setJobError] = useState('');
  const [jobRunning, setJobRunning] = useState(false);

  const [loadingGroups, setLoadingGroups] = useState(false);
  const [groupsError, setGroupsError] = useState('');
  const [groups, setGroups] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [selectedKey, setSelectedKey] = useState(null);
  const [detailLines, setDetailLines] = useState([]);

  const sourcesForJob = useMemo(() => {
    if (source === 'silla') return ['silla'];
    if (source === 'lotte') return ['lotte'];
    return ['silla', 'lotte'];
  }, [source]);

  const refreshGroups = async ({ resetPage = false } = {}) => {
    const nextPage = resetPage ? 1 : page;
    setLoadingGroups(true);
    setGroupsError('');
    try {
      const res = await listEdiUnifiedGroups({
        fromDate,
        toDate,
        sources: source,
        statusFilter,
        page: nextPage,
        pageSize: 50,
      });
      setGroups(res.items || []);
      setTotal(res.total || 0);
      if (resetPage) setPage(1);
    } catch (e) {
      setGroupsError(e.response?.data?.detail || '목록 조회에 실패했습니다.');
    } finally {
      setLoadingGroups(false);
    }
  };

  const loadDetail = async (g) => {
    const key = `${g.dutyfree_operator}_${g.receipt_no}`;

    // 같은 행 다시 클릭 시 토글(접기)
    if (selectedKey === key) {
      setSelectedKey(null);
      setDetailLines([]);
      setDetailError('');
      return;
    }

    setSelectedKey(key);
    setDetailLoading(true);
    setDetailError('');
    setDetailLines([]);
    try {
      const res = await getEdiUnifiedGroupDetail({
        dutyfreeOperator: g.dutyfree_operator,
        receiptNo: g.receipt_no,
        fromDate,
        toDate,
      });
      setDetailLines(res.items || []);
    } catch (e) {
      setDetailError(e.response?.data?.detail || '상세 조회에 실패했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    refreshGroups({ resetPage: true });
    // 상세 선택은 필터 변경 시 초기화
    setSelectedKey(null);
    setDetailLines([]);
  }, [fromDate, toDate, source, statusFilter]);

  useEffect(() => {
    if (!jobId) return;
    let mounted = true;
    let timerId = null;
    const poll = async () => {
      try {
        const res = await getEdiUnifiedJobStatus(jobId);
        if (!mounted) return;
        const st = res.job || null;
        setJobStatus(st);
        const s = st?.status;
        const running = s === 'queued' || s === 'running';
        setJobRunning(running);
        if (!running) {
          // 완료/실패 시 목록 갱신
          refreshGroups({ resetPage: true });
          // 완료/실패면 더 이상 폴링하지 않음
          if (timerId) clearInterval(timerId);
        }
      } catch (e) {
        if (!mounted) return;
        setJobError(e.response?.data?.detail || '작업 상태 조회에 실패했습니다.');
      }
    };
    timerId = setInterval(poll, 1500);
    poll();
    return () => {
      mounted = false;
      if (timerId) clearInterval(timerId);
    };
  }, [jobId]);

  const handleRun = async () => {
    setJobError('');
    try {
      setJobRunning(true);
      const res = await enqueueEdiUnifiedJob({ sources: sourcesForJob });
      setJobId(res.job?.job_id || null);
      setJobStatus(res.job || null);
    } catch (e) {
      setJobRunning(false);
      setJobError(e.response?.data?.detail || '작업 요청에 실패했습니다.');
    }
  };

  const handleDownload = async () => {
    try {
      await downloadEdiUnifiedExcel({ fromDate, toDate, sources: source });
    } catch (e) {
      setGroupsError(e.response?.data?.detail || '엑셀 다운로드에 실패했습니다.');
    }
  };

  return (
    <div className="edi-check-panel">
      <div className="edi-check-controls">
        <div className="field">
          <label>FROM_DATE</label>
          <input
            type="date"
            value={toDateInputValue(fromDate)}
            onChange={(e) => setFromDate(fromDateInputValue(e.target.value))}
          />
        </div>
        <div className="field">
          <label>TO_DATE</label>
          <input
            type="date"
            value={toDateInputValue(toDate)}
            onChange={(e) => setToDate(fromDateInputValue(e.target.value))}
          />
        </div>
        <div className="field">
          <label>면세점</label>
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            {SOURCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="edi-check-actions">
          <button className="edi-btn primary" onClick={handleRun} disabled={jobRunning}>
            {jobRunning ? 'EDI 매핑 실행 중...' : 'EDI 매핑 실행'}
          </button>
          <button className="edi-btn" onClick={handleDownload} disabled={loadingGroups}>
            엑셀 다운로드
          </button>
          <button className="edi-btn" onClick={() => refreshGroups({ resetPage: true })} disabled={loadingGroups}>
            새로고침
          </button>
        </div>
      </div>

      {jobId && (
        <div className="edi-muted">
          job_id: <strong>{jobId}</strong> / status: <strong>{jobStatus?.status || 'unknown'}</strong>
          {jobStatus?.error ? ` / error: ${jobStatus.error}` : ''}
        </div>
      )}
      {jobError && <div className="edi-error">{jobError}</div>}

      <div className="edi-tabs">
        {STATUS_TABS.map((t) => (
          <button
            key={t.value}
            className={`edi-tab ${statusFilter === t.value ? 'active' : ''}`}
            onClick={() => setStatusFilter(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {groupsError && <div className="edi-error">{groupsError}</div>}

      <table className="edi-table">
        <thead>
          <tr>
            <th>면세점</th>
            <th>영수증번호</th>
            <th>라인수</th>
            <th>최근매출일자</th>
            <th>영수증UUID</th>
            <th>여권UUID</th>
          </tr>
        </thead>
        <tbody>
          {loadingGroups ? (
            <tr>
              <td colSpan={6}>로딩 중...</td>
            </tr>
          ) : groups.length === 0 ? (
            <tr>
              <td colSpan={6}>데이터가 없습니다.</td>
            </tr>
          ) : (
            groups.map((g) => {
              const key = `${g.dutyfree_operator}_${g.receipt_no}`;
              const isOpen = key === selectedKey;
              return (
                <React.Fragment key={key}>
                  <tr
                    className="edi-row"
                    onClick={() => loadDetail(g)}
                  >
                    <td>{g.dutyfree_operator}</td>
                    <td>{g.receipt_no}</td>
                    <td>{g.line_count}</td>
                    <td>{g.datetime_purchase ? String(g.datetime_purchase).replace('T', ' ').slice(0, 19) : ''}</td>
                    <td>{g.uuid_receipt || ''}</td>
                    <td>{g.uuid_passport || ''}</td>
                  </tr>
                  {isOpen && (
                    <tr className="edi-detail-row">
                      <td colSpan={6}>
                        {detailError && <div className="edi-error">{detailError}</div>}
                        {detailLoading ? (
                          <div>로딩 중...</div>
                        ) : (
                          <table className="edi-table" style={{ marginTop: 8 }}>
                            <thead>
                              <tr>
                                <th>상품코드</th>
                                <th>상품명</th>
                                <th>수량</th>
                                <th>총매출($)</th>
                                <th>순매출($)</th>
                                <th>할인($)</th>
                                <th>고객명(EDI)</th>
                                <th>system_note</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailLines.length === 0 ? (
                                <tr>
                                  <td colSpan={8}>라인이 없습니다.</td>
                                </tr>
                              ) : (
                                detailLines.map((r, idx) => (
                                  <tr key={idx}>
                                    <td>{r.product_code}</td>
                                    <td>{r.product_name}</td>
                                    <td>{r.quantity}</td>
                                    <td>{r.gross_sales_amount_usd}</td>
                                    <td>{r.net_sales_amount_usd}</td>
                                    <td>{r.discount_amount_usd}</td>
                                    <td>{r.customer_name}</td>
                                    <td>{r.system_note}</td>
                                  </tr>
                                ))
                              )}
                            </tbody>
                          </table>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })
          )}
        </tbody>
      </table>

      <div className="edi-muted">
        총 {total}건 / 페이지 {page}
      </div>

    </div>
  );
}

