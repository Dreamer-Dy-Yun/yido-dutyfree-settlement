const SOURCE_OPTIONS = [
  { value: 'all', label: '전체' },
  { value: 'silla', label: '신라' },
  { value: 'lotte', label: '롯데' },
];

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

function EdiUnifiedControls({
  fromDate,
  toDate,
  source,
  jobRunning,
  downloadLoading,
  loadingGroups,
  onChangeFromDate,
  onChangeToDate,
  onChangeSource,
  onRun,
  onDownload,
  onRefresh,
}) {
  return (
    <div className="edi-check-controls">
      <div className="field">
        <label>FROM_DATE</label>
        <input
          type="date"
          value={toDateInputValue(fromDate)}
          onChange={(e) => onChangeFromDate(fromDateInputValue(e.target.value))}
        />
      </div>
      <div className="field">
        <label>TO_DATE</label>
        <input
          type="date"
          value={toDateInputValue(toDate)}
          onChange={(e) => onChangeToDate(fromDateInputValue(e.target.value))}
        />
      </div>
      <div className="field">
        <label>면세점</label>
        <select value={source} onChange={(e) => onChangeSource(e.target.value)}>
          {SOURCE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div className="edi-check-actions">
        <button className="edi-btn primary" onClick={onRun} disabled={jobRunning}>
          {jobRunning ? 'EDI 매핑 실행 중...' : 'EDI 매핑 실행'}
        </button>
        <button className="edi-btn" onClick={onDownload} disabled={loadingGroups}>
          {downloadLoading ? (
            <>
              <span className="edi-spinner" aria-hidden="true" />
              엑셀 다운로드 중...
            </>
          ) : (
            '엑셀 다운로드'
          )}
        </button>
        <button className="edi-btn" onClick={onRefresh} disabled={loadingGroups}>
          새로고침
        </button>
      </div>
    </div>
  );
}

export default EdiUnifiedControls;
