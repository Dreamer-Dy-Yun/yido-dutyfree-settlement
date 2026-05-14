import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  enqueueEdiUnifiedJob,
  getEdiUnifiedJobStatus,
  listEdiUnifiedGroups,
  getEdiUnifiedGroupDetail,
  downloadEdiUnifiedExcel,
} from '../api/data-mapping/ediUnifiedApi';
import EdiNoteTooltip from './edi-unified/EdiNoteTooltip';
import EdiUnifiedControls from './edi-unified/EdiUnifiedControls';
import EdiUnifiedGroupTable from './edi-unified/EdiUnifiedGroupTable';
import './EdiUnifiedCheckPanel.css';

const STATUS_TABS = [
  { value: 'all', label: '전체' },
  { value: 'full', label: '완전연결' },
  { value: 'partial', label: '부분연결' },
  { value: 'unmapped', label: '미연결' },
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
  const pageSize = 50;

  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);
  const [detailLines, setDetailLines] = useState([]);
  const [noteTooltip, setNoteTooltip] = useState({ open: false, text: '', x: 0, y: 0 });

  const sourcesForJob = useMemo(() => {
    if (source === 'silla') return ['silla'];
    if (source === 'lotte') return ['lotte'];
    return ['silla', 'lotte'];
  }, [source]);

  const loadGroupsPage = useCallback(async (nextPage) => {
    setLoadingGroups(true);
    setGroupsError('');
    try {
      const res = await listEdiUnifiedGroups({
        fromDate,
        toDate,
        sources: source,
        statusFilter,
        page: nextPage,
        pageSize,
      });
      setGroups(res.items || []);
      setTotal(res.total || 0);
    } catch (e) {
      setGroupsError(e.response?.data?.detail || '목록 조회에 실패했습니다.');
    } finally {
      setLoadingGroups(false);
    }
  }, [fromDate, source, statusFilter, toDate]);

  const refreshGroups = useCallback(async ({ resetPage = false } = {}) => {
    const nextPage = resetPage ? 1 : page;
    await loadGroupsPage(nextPage);
    if (resetPage) setPage(1);
  }, [loadGroupsPage, page]);

  const lastPage = Math.max(1, Math.ceil((total || 0) / pageSize));

  const clearDetail = () => {
    setSelectedKey(null);
    setDetailLines([]);
    setDetailError('');
    setDetailLoading(false);
  };

  const goToPage = async (next) => {
    if (next < 1 || next > lastPage) return;
    clearDetail();
    setPage(next);
    await loadGroupsPage(next);
  };

  const loadDetail = async (g) => {
    const key = `${g.dutyfree_operator}_${g.receipt_no}`;
    if (selectedKey === key) {
      clearDetail();
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
    loadGroupsPage(1);
    setPage(1);
    setSelectedKey(null);
    setDetailLines([]);
  }, [loadGroupsPage]);

  useEffect(() => {
    if (!jobId) return undefined;
    let mounted = true;
    let timerId = null;
    const poll = async () => {
      try {
        const res = await getEdiUnifiedJobStatus(jobId);
        if (!mounted) return;
        const st = res.job || null;
        setJobStatus(st);
        const running = st?.status === 'queued' || st?.status === 'running';
        setJobRunning(running);
        if (!running) {
          loadGroupsPage(1);
          setPage(1);
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
  }, [jobId, loadGroupsPage]);

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
      setDownloadLoading(true);
      await downloadEdiUnifiedExcel({ fromDate, toDate, sources: source });
    } catch (e) {
      setGroupsError(e.response?.data?.detail || '엑셀 다운로드에 실패했습니다.');
    } finally {
      setDownloadLoading(false);
    }
  };

  const showNoteTooltip = (text, x, y) => {
    setNoteTooltip({ open: true, text, x, y });
  };

  return (
    <div className="edi-check-panel">
      <EdiUnifiedControls
        fromDate={fromDate}
        toDate={toDate}
        source={source}
        jobRunning={jobRunning}
        downloadLoading={downloadLoading}
        loadingGroups={loadingGroups}
        onChangeFromDate={setFromDate}
        onChangeToDate={setToDate}
        onChangeSource={setSource}
        onRun={handleRun}
        onDownload={handleDownload}
        onRefresh={() => refreshGroups({ resetPage: true })}
      />

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

      <EdiUnifiedGroupTable
        loadingGroups={loadingGroups}
        groups={groups}
        selectedKey={selectedKey}
        detailError={detailError}
        detailLoading={detailLoading}
        detailLines={detailLines}
        total={total}
        page={page}
        lastPage={lastPage}
        onLoadDetail={loadDetail}
        onPrevPage={() => goToPage(page - 1)}
        onNextPage={() => goToPage(page + 1)}
        onShowNoteTooltip={showNoteTooltip}
        onHideNoteTooltip={() => setNoteTooltip((prev) => ({ ...prev, open: false }))}
      />

      <EdiNoteTooltip noteTooltip={noteTooltip} />
    </div>
  );
}
