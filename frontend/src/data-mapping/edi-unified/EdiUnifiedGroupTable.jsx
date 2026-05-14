import React from 'react';

const formatAccountingNumber = (v) => {
  if (v == null || v === '') return '-';
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return n.toLocaleString('ko-KR');
};

const getStatusBadge = (g) => {
  const hasReceipt = !!g.uuid_receipt;
  const hasPassport = !!g.uuid_passport;

  if (hasReceipt && hasPassport) {
    return { label: '완전연결', className: 'edi-badge full' };
  }
  if (hasReceipt && !hasPassport) {
    return { label: '부분연결', className: 'edi-badge partial' };
  }
  return { label: '미연결', className: 'edi-badge unmapped' };
};

const getLinkBadge = (hasUuid) =>
  hasUuid
    ? { label: '연결', className: 'edi-link-badge edi-link-on' }
    : { label: '미연결', className: 'edi-link-badge edi-link-off' };

const getSystemNoteBadge = (note) =>
  note && String(note).trim() !== ''
    ? { label: '[...]', className: 'edi-note-badge edi-note-on' }
    : { label: '없음', className: 'edi-note-badge edi-note-off' };

const normalizeSystemNote = (note) =>
  note && String(note).trim() !== '' ? String(note) : '시스템 비고가 없습니다.';

function EdiUnifiedGroupTable({
  loadingGroups,
  groups,
  selectedKey,
  detailError,
  detailLoading,
  detailLines,
  total,
  page,
  lastPage,
  onLoadDetail,
  onPrevPage,
  onNextPage,
  onShowNoteTooltip,
  onHideNoteTooltip,
}) {
  return (
    <>
      <table className="edi-table edi-main-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>매출일자</th>
            <th>면세점</th>
            <th>지점</th>
            <th>그룹번호</th>
            <th>영수증번호</th>
            <th>고객명</th>
            <th>라인수</th>
            <th>영수증연결</th>
            <th>여권연결</th>
          </tr>
        </thead>
        <tbody>
          {loadingGroups ? (
            <tr>
              <td colSpan={10}>로딩 중...</td>
            </tr>
          ) : groups.length === 0 ? (
            <tr>
              <td colSpan={10}>데이터가 없습니다.</td>
            </tr>
          ) : (
            groups.map((g) => {
              const key = `${g.dutyfree_operator}_${g.receipt_no}`;
              const isOpen = key === selectedKey;
              return (
                <React.Fragment key={key}>
                  <tr className="edi-row" onClick={() => onLoadDetail(g)}>
                    <td>
                      {(() => {
                        const st = getStatusBadge(g);
                        return <span className={st.className}>{st.label}</span>;
                      })()}
                    </td>
                    <td title={g.datetime_purchase ? String(g.datetime_purchase).replace('T', ' ').slice(0, 19) : ''}>
                      {g.datetime_purchase ? String(g.datetime_purchase).replace('T', ' ').slice(0, 10) : ''}
                    </td>
                    <td>{g.dutyfree_operator}</td>
                    <td>{g.dutyfree_branch || '-'}</td>
                    <td>{g.group_no || '-'}</td>
                    <td>{g.receipt_no}</td>
                    <td>{g.customer_name != null && g.customer_name !== '' ? g.customer_name : '-'}</td>
                    <td>{g.line_count}</td>
                    <td>
                      {(() => {
                        const lb = getLinkBadge(!!g.uuid_receipt);
                        return <span className={lb.className}>{lb.label}</span>;
                      })()}
                    </td>
                    <td>
                      {(() => {
                        const lb = getLinkBadge(!!g.uuid_passport);
                        return <span className={lb.className}>{lb.label}</span>;
                      })()}
                    </td>
                  </tr>
                  {isOpen && (
                    <tr className="edi-detail-row">
                      <td colSpan={10} className="edi-detail-cell">
                        <div className="edi-detail-wrap">
                          {detailError && <div className="edi-error">{detailError}</div>}
                          {detailLoading ? (
                            <div className="edi-detail-loading">로딩 중...</div>
                          ) : (
                            <DetailLinesTable
                              detailLines={detailLines}
                              onShowNoteTooltip={onShowNoteTooltip}
                              onHideNoteTooltip={onHideNoteTooltip}
                            />
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })
          )}
        </tbody>
      </table>

      <div className="edi-muted" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>
          총 {total}건 / 페이지 {page} / {lastPage}
        </span>
        <span style={{ display: 'flex', gap: 8 }}>
          <button className="edi-btn" onClick={onPrevPage} disabled={loadingGroups || page <= 1}>
            이전
          </button>
          <button className="edi-btn" onClick={onNextPage} disabled={loadingGroups || page >= lastPage}>
            다음
          </button>
        </span>
      </div>
    </>
  );
}

function DetailLinesTable({ detailLines, onShowNoteTooltip, onHideNoteTooltip }) {
  return (
    <table className="edi-table edi-detail-nested-table">
      <thead>
        <tr>
          <th>카테고리</th>
          <th>브랜드</th>
          <th>상품명</th>
          <th>수량</th>
          <th>총매출($)</th>
          <th>순매출($)</th>
          <th>할인($)</th>
          <th>system_note</th>
        </tr>
      </thead>
      <tbody>
        {detailLines.length === 0 ? (
          <tr>
            <td colSpan={8} className="edi-detail-empty">
              라인이 없습니다.
            </td>
          </tr>
        ) : (
          detailLines.map((r, idx) => (
            <tr key={idx}>
              <td>{r.category || '-'}</td>
              <td>{r.brand || '-'}</td>
              <td>{r.product_name}</td>
              <td>{r.quantity}</td>
              <td>{formatAccountingNumber(r.gross_sales_amount_usd)}</td>
              <td>{formatAccountingNumber(r.net_sales_amount_usd)}</td>
              <td>{formatAccountingNumber(r.discount_amount_usd)}</td>
              <td>
                {(() => {
                  const sb = getSystemNoteBadge(r.system_note);
                  return (
                    <button
                      type="button"
                      className={sb.className}
                      onMouseEnter={(e) => {
                        e.stopPropagation();
                        onShowNoteTooltip(normalizeSystemNote(r.system_note), e.clientX + 14, e.clientY + 14);
                      }}
                      onMouseMove={(e) => {
                        e.stopPropagation();
                        onShowNoteTooltip(normalizeSystemNote(r.system_note), e.clientX + 14, e.clientY + 14);
                      }}
                      onMouseLeave={(e) => {
                        e.stopPropagation();
                        onHideNoteTooltip();
                      }}
                    >
                      {sb.label}
                    </button>
                  );
                })()}
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

export default EdiUnifiedGroupTable;
