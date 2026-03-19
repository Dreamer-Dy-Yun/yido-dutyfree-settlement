import { useEffect, useRef, useState } from 'react';
import { getMatchStatus, postMatchAttempt, getMatches, getMatchDetail } from '../services/tenant';
import MappingDetailModal from './MappingDetailModal';
import ImageVerifyModal from './ImageVerifyModal';

/**
 * 이미지 매핑 탭 콘텐츠
 * - 상단: 매핑 상태 요약 + "매핑 시도" 버튼
 * - 하단: 매핑/미매핑/전체 리스트 (면세점 / 영수증 번호 / 이름만 표시)
 */
function ImageMappingPanel() {
  const [status, setStatus] = useState(null);
  const [statusError, setStatusError] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const pollingRef = useRef(null);

  const [filter, setFilter] = useState('all'); // 'all' | 'matched' | 'unmatched'
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [rows, setRows] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState('');

  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailIndex, setDetailIndex] = useState(0);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [verifyMode, setVerifyMode] = useState('receipt'); // 'receipt' | 'passport'
  const [verifyItem, setVerifyItem] = useState(null); // { hash_img, coordinate }

  const loadStatus = async () => {
    try {
      setStatusError('');
      const data = await getMatchStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load match status:', err);
      setStatusError('매칭 상태를 불러오지 못했습니다.');
    }
  };

  const loadList = async (opts = {}) => {
    const nextFilter = opts.filter ?? filter;
    const nextPage = opts.page ?? page;

    try {
      setListLoading(true);
      setListError('');
      const data = await getMatches({
        status: nextFilter,
        page: nextPage,
        pageSize,
      });

      // 백엔드 응답 형태에 따라 조정 필요
      const items = data.items || data.results || [];
      const total = data.total ?? data.total_count ?? items.length;

      setRows(items);
      setTotalCount(total);
      setPage(nextPage);
      setFilter(nextFilter);
    } catch (err) {
      console.error('Failed to load matches:', err);
      setListError('매칭 결과를 불러오지 못했습니다.');
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    loadList({ page: 1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const startMatchPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    let attempts = 0;
    const maxAttempts = 15; // 최대 약 30초 (2초 * 15)

    pollingRef.current = setInterval(async () => {
      attempts += 1;
      try {
        const data = await getMatchStatus();
        setStatus(data);
        await loadList({ page: 1 });

        const nextUnmatched = data?.unmatched_count ?? 0;
        if (nextUnmatched === 0 || attempts >= maxAttempts) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setIsRunning(false);
        }
      } catch (err) {
        console.error('Failed to poll match status:', err);
        if (attempts >= 3) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setIsRunning(false);
        }
      }
    }, 2000);
  };

  const handleMatchAttempt = async () => {
    if (isRunning) return;
    if (!status || status.unmatched_count === 0) {
      alert('미매핑 데이터가 없습니다.');
      return;
    }
    try {
      setIsRunning(true);
      await postMatchAttempt({ tryFallback: true });
      // 매칭 시도 후 상태/리스트를 폴링하면서 자동 갱신
      startMatchPolling();
    } catch (err) {
      console.error('Failed to trigger match attempt:', err);
      alert('매칭 시도 요청에 실패했습니다.');
    } finally {
      // 실제 매칭 작업은 비동기로 진행되므로,
      // 폴링 루프가 종료될 때까지 isRunning은 유지한다.
    }
  };

  const handleFilterChange = async (nextFilter) => {
    await loadList({ filter: nextFilter, page: 1 });
  };

  const handlePageChange = async (direction) => {
    const nextPage = page + direction;
    if (nextPage < 1) return;
    const maxPage = Math.max(1, Math.ceil(totalCount / pageSize));
    if (nextPage > maxPage) return;
    await loadList({ page: nextPage });
  };

  const unmatchedCount = status?.unmatched_count ?? 0;

  const handleOpenDetail = async (row, index) => {
    if (!row?.uuid_receipt) return;
    try {
      setDetailModalOpen(true);
      setDetailIndex(index);
      setDetailLoading(true);
      setDetailError('');
      const data = await getMatchDetail(row.uuid_receipt);
      setDetail(data);
    } catch (err) {
      console.error('Failed to load match detail:', err);
      setDetailError('매핑 상세 정보를 불러오지 못했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setDetailModalOpen(false);
    setDetail(null);
    setDetailError('');
  };

  const handleDetailChangeIndex = async (direction) => {
    if (rows.length === 0) return;

    const nextIndex =
      direction === 'prev'
        ? (detailIndex === 0 ? rows.length - 1 : detailIndex - 1)
        : (detailIndex === rows.length - 1 ? 0 : detailIndex + 1);

    const nextRow = rows[nextIndex];
    if (!nextRow?.uuid_receipt) return;

    try {
      setDetailIndex(nextIndex);
      setDetailLoading(true);
      setDetailError('');
      const data = await getMatchDetail(nextRow.uuid_receipt);
      setDetail(data);
    } catch (err) {
      console.error('Failed to load match detail:', err);
      setDetailError('매핑 상세 정보를 불러오지 못했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  const reloadCurrentDetail = async () => {
    const row = rows[detailIndex];
    if (!row?.uuid_receipt) return;
    try {
      setDetailLoading(true);
      setDetailError('');
      const data = await getMatchDetail(row.uuid_receipt);
      setDetail(data);
      await loadStatus();
    } catch (err) {
      console.error('Failed to reload match detail:', err);
      setDetailError('매핑 상세 정보를 다시 불러오지 못했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleEditReceipt = (receipt) => {
    if (!receipt?.hash_img) return;
    setVerifyMode('receipt');
    setVerifyItem({
      hash_img: receipt.hash_img,
      coordinate: receipt.coordinate_verified || null,
    });
    setVerifyModalOpen(true);
  };

  const handleEditPassport = (passport) => {
    if (!passport?.hash_img) return;
    setVerifyMode('passport');
    setVerifyItem({
      hash_img: passport.hash_img,
      coordinate: passport.coordinate || null,
    });
    setVerifyModalOpen(true);
  };

  return (
    <div className="tab-content">
      <h2>이미지 매핑</h2>

      <div className="mapping-status-card">
        {statusError && <div className="upload-error">{statusError}</div>}
        {status && !statusError && (
          <div className="upload-success">
            확인되었으나 미매핑된 데이터 {unmatchedCount}건이 있습니다.
          </div>
        )}

        <div className="mapping-actions">
          <button
            className="primary-button"
            onClick={handleMatchAttempt}
            disabled={isRunning || unmatchedCount === 0}
          >
            {isRunning ? '매핑 시도 중...' : '매핑 시도'}
          </button>
        </div>
        {isRunning && (
          <div style={{ marginTop: 8, fontSize: '0.85rem', color: '#4b5563' }}>
            매칭 작업이 진행 중입니다. 완료되면 목록이 자동으로 새로고침됩니다.
          </div>
        )}
      </div>

      <div className="mapping-list-card">
        <div className="mapping-list-header">
          <div className="mapping-filters">
            <button
              className={filter === 'all' ? 'filter-button active' : 'filter-button'}
              onClick={() => handleFilterChange('all')}
            >
              전체
            </button>
            <button
              className={filter === 'matched' ? 'filter-button active' : 'filter-button'}
              onClick={() => handleFilterChange('matched')}
            >
              매핑됨
            </button>
            <button
              className={filter === 'unmatched' ? 'filter-button active' : 'filter-button'}
              onClick={() => handleFilterChange('unmatched')}
            >
              미매핑
            </button>
          </div>
        </div>

        {listError && <div className="upload-error">{listError}</div>}

        <table className="common-table">
          <thead>
            <tr>
              <th>면세점</th>
              <th>영수증 번호</th>
              <th>이름</th>
              <th>동작</th>
            </tr>
          </thead>
          <tbody>
            {listLoading && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center' }}>
                  로딩 중...
                </td>
              </tr>
            )}
            {!listLoading && rows.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center' }}>
                  표시할 데이터가 없습니다.
                </td>
              </tr>
            )}
            {!listLoading &&
              rows.map((row, idx) => {
                // 백엔드 응답 필드 이름에 맞게 조정 필요 (예: dutyfree_company, receipt_no, name 등)
                const dutyfreeCompany = row.dutyfree_company ?? '-';
                const receiptNo = row.receipt_no ?? '-';
                const purchaserName = row.name ?? '-';

                return (
                  <tr key={row.uuid_receipt || `${dutyfreeCompany}-${receiptNo}-${purchaserName}`}>
                    <td>{dutyfreeCompany}</td>
                    <td>{receiptNo}</td>
                    <td>{purchaserName}</td>
                    <td>
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => handleOpenDetail(row, idx)}
                      >
                        상세 보기
                      </button>
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>

        <div className="pagination-controls">
          <button
            className="secondary-button"
            type="button"
            onClick={() => handlePageChange(-1)}
            disabled={page <= 1}
          >
            이전
          </button>
          <span className="page-info">
            페이지 {page} / {Math.max(1, Math.ceil(totalCount / pageSize))}
          </span>
          <button
            className="secondary-button"
            type="button"
            onClick={() => handlePageChange(1)}
            disabled={page >= Math.max(1, Math.ceil(totalCount / pageSize))}
          >
            다음
          </button>
        </div>
      </div>

      {detailModalOpen && (
        <MappingDetailModal
          loading={detailLoading}
          error={detailError}
          detail={detail}
          onClose={handleCloseDetail}
          onPrev={() => handleDetailChangeIndex('prev')}
          onNext={() => handleDetailChangeIndex('next')}
          onEditReceipt={handleEditReceipt}
          onEditPassport={handleEditPassport}
        />
      )}

      {verifyModalOpen && verifyItem && (
        <ImageVerifyModal
          mode={verifyMode}
          items={[
            {
              image: {
                hash_img: verifyItem.hash_img,
                coordinate: verifyItem.coordinate || null,
              },
              source: 'verified',
            },
          ]}
          currentIndex={0}
          onChangeIndex={() => {}}
          onClose={() => setVerifyModalOpen(false)}
          onSaved={() => {
            setVerifyModalOpen(false);
            reloadCurrentDetail();
          }}
          disableNavigation
        />
      )}
    </div>
  );
}

export default ImageMappingPanel;

